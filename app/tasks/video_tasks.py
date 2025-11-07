import shutil
from pathlib import Path
from time import sleep
from uuid import UUID
import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from moviepy import ImageClip, VideoFileClip, CompositeVideoClip, vfx

from app.core.celery_app import celery_app
from app.core.config import settings
from app.utils.video_validator_sync import validate_video_sync
from app.models.video import Video

logger = logging.getLogger(__name__)

# Create synchronous database session for Celery worker
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "")
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)

# 🆕 AGREGAR: Storage backend para S3 (solo si STORAGE_TYPE=s3)
if settings.STORAGE_TYPE == "s3":
    from app.storage.s3_storage import S3Storage
    storage_s3 = S3Storage()
    logger.info("🪣 Celery using S3 storage backend")
else:
    storage_s3 = None
    logger.info("📁 Celery using local/NFS storage backend")


@celery_app.task(name="process_video")
def process_video_task(video_id: str, temp_file_path: str):
    """
    Process uploaded video asynchronously.
    
    Steps:
    1. Update status to 'processing'
    2. Validate video with FFprobe
    3. Process video (cutting, resizing, adding banner)
    4. Move to processed folder
    5. Update status to 'processed' or 'failed'
    """
    db = SyncSessionLocal()
    
    local_temp_input = None
    local_temp_output = None
    
    try:
        sleep(5)

        # Get video record
        video = db.query(Video).filter(Video.id == UUID(video_id)).first()
        
        if not video:
            raise Exception(f"Video {video_id} not found in database")
        
        # Update status to processing
        video.status = "processing"
        db.commit()
        
        if settings.STORAGE_TYPE == "s3":
            local_temp_input = f"{settings.TEMP_PATH}/{video_id}_input.mp4"
            logger.info(f"Downloading from S3: {temp_file_path}")
            if not storage_s3.download_file_sync(temp_file_path, local_temp_input):
                raise Exception("Failed to download video from S3")
        
            video_file_path = local_temp_input
            logger.info(f"Video downloaded to: {local_temp_input}")
        
        else:
            # Para NFS: usar directamente el path
            video_file_path = temp_file_path
            logger.info(f"✅ Using local file: {video_file_path}")
        
        # Validate video with FFprobe
        metadata = validate_video_sync(video_file_path)
        
        # Update duration
        video.duration_seconds = int(metadata['duration'])
        db.commit()
        
        # Process video (cutting, adding banner, watermark and resizing.)
        videoclip = VideoFileClip(video_file_path)


        # Intro and Outro logo
        if settings.STORAGE_TYPE == "s3":
            # Descargar logo de S3 si no existe localmente
            logo_local = f"{settings.TEMP_PATH}/logo720.png"
            logo_s3_key = "resources/logo720.png"
            
            if not os.path.exists(logo_local):
                logger.info(f"Downloading logo from S3: {logo_s3_key}")
                if not storage_s3.download_file_sync(logo_s3_key, logo_local):
                    logger.warning("Logo not found in S3, using default")
                    # Aquí podrías crear un logo temporal o usar uno por defecto
            
            logo_path = Path(logo_local)
        else:
            # Para NFS: usar logo desde RES_PATH
            logo_path = Path(settings.RES_PATH) / "logo720.png"

        # Determine durations
        video_duration = video.duration_seconds if video.duration_seconds <= 30 else 30
        intro_duration = 2.5
        outro_duration = 2.5
        watermark_fadein = 2.0

        # Create clips
        intro_logo = (ImageClip(str(logo_path))
              .with_duration(intro_duration)
              .with_position(("center", "center")))
        
        # Trim video if needed and add fade in
        if video.duration_seconds > 30:
            videoclip = videoclip.subclipped(0, 30)

        videoclip = videoclip.with_effects([vfx.CrossFadeIn(watermark_fadein)]).resized((1280,1080))

        # Watermark (positioned at 50% from top, centered horizontally)
        watermark = (ImageClip(str(logo_path))
             .with_duration(video_duration)
             .resized(height=150)  # Resize logo for watermark
             .with_position(("center", 0.5), relative=True)
             .with_effects([vfx.CrossFadeIn(watermark_fadein)])
             .with_opacity(0.5)
             .with_start(intro_duration))

        # Outro logo
        outro_logo = (ImageClip(str(logo_path))
              .with_duration(outro_duration)
              .with_position(("center", "center"))
              .with_effects([vfx.CrossFadeIn(2.0)])
              .with_start(intro_duration + video_duration))

        # Composite all clips
        final_clip = CompositeVideoClip([
            intro_logo,
            videoclip.with_start(intro_duration),
            watermark,
            outro_logo
        ])

        # Remove audio and resize
        final_clip = (final_clip.with_audio(None))
        

        # Export
        if settings.STORAGE_TYPE == "s3":
            # Para S3: renderizar a temporal y luego subir
            os.makedirs(settings.TEMP_PATH, exist_ok=True)
            local_temp_output = f"{settings.TEMP_PATH}/{video_id}_processed.mp4"
            final_clip.write_videofile(
                local_temp_output,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            
            if not os.path.exists(local_temp_output):
                raise Exception(f"Rendered file not found: {local_temp_output}")
            
            output_size = os.path.getsize(local_temp_output)
            logger.info(f"Rendered size: {output_size / (1024*1024):.2f} MB")
            
            if output_size < 1000:
                raise Exception(f"Rendered file too small (corrupted): {output_size} bytes")
            
            # ✅ Validar video procesado con FFprobe
            logger.info(f"Validating processed video: {local_temp_output}")
            try:
                processed_metadata = validate_video_sync(local_temp_output)
                logger.info(f"Processed video is VALID - Duration: {processed_metadata['duration']}s")
            except Exception as e:
                raise Exception(f"Processed video validation FAILED: {str(e)}")
           
            
            # Subir a S3
            s3_processed_key = f"processed/{video_id}.mp4"
            
            if not storage_s3.upload_file_sync(local_temp_output, s3_processed_key):
                raise Exception("Failed to upload processed video to S3")
            
            # Actualizar path en BD con S3 key
            processed_file_path = s3_processed_key
            logger.info(f"Video uploaded to S3: {s3_processed_key}")
            
        else:
            # Para NFS: renderizar directamente a carpeta processed
            temp_path = Path(temp_file_path)
            processed_folder = Path(settings.STORAGE_PATH) / "processed"
            processed_folder.mkdir(parents=True, exist_ok=True)
            
            processed_file_path = str(processed_folder / temp_path.name)
            
            logger.info(f"Rendering to: {processed_file_path}")
            final_clip.write_videofile(
                processed_file_path,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            logger.info(f"Video saved to: {processed_file_path}")

        # Clean up
        videoclip.close()
        final_clip.close()
        
        # Update database record
        video.file_path = str(processed_file_path)
        video.status = "processed"
        db.commit()
        
        if settings.STORAGE_TYPE == "s3":
            if local_temp_input and os.path.exists(local_temp_input):
                os.remove(local_temp_input)
                logger.info(f"Cleaned input: {local_temp_input}")
            if local_temp_output and os.path.exists(local_temp_output):
                os.remove(local_temp_output)
                logger.info(f"Cleaned output: {local_temp_output}")
        else:
            temp_path = Path(temp_file_path)
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"Cleaned: {temp_file_path}")
        
        
        logger.info(f"Video {video_id} processed succesfully")
        
        return {
            "status": "success",
            "video_id": video_id,
            "message": "Video processed successfully",
            "file_path": str(processed_file_path)
        }
        
    except Exception as e:
        # Update status to failed
        if video:
            video.status = "failed"
            db.commit()
        
        if settings.STORAGE_TYPE == "s3":
            for temp_file in [local_temp_input,local_temp_output]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        logger.info(f"Cleaned temp file: {temp_file}")
                    except:
                        pass
        
        return {
            "status": "failed",
            "video_id": video_id,
            "error": str(e)
        }
        
    finally:
        db.close()
        logger.info("Database session closed")