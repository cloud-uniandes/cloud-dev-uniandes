import shutil
from pathlib import Path
from time import sleep
from uuid import UUID
import os
import logging
import subprocess
import json

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

# Storage backend para S3 (solo si STORAGE_TYPE=s3)
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
    1. Download from S3 if needed
    2. Update status to 'processing'
    3. Validate video with FFprobe
    4. Process video (cutting, resizing, adding banner)
    5. Upload to S3 or move to processed folder
    6. Update status to 'processed' or 'failed'
    """
    db = SyncSessionLocal()
    
    local_temp_input = None
    local_temp_output = None
    
    try:
        sleep(5)
        
        logger.info(f" Processing video {video_id}")

        # Get video record
        video = db.query(Video).filter(Video.id == UUID(video_id)).first()
        
        if not video:
            raise Exception(f"Video {video_id} not found in database")
        
        # Update status to processing
        video.status = "processing"
        db.commit()
        logger.info(" Status updated to 'processing'")
        
        # PASO 1: Download from S3 if needed
        if settings.STORAGE_TYPE == "s3":
            os.makedirs(settings.TEMP_PATH, exist_ok=True)
            local_temp_input = f"{settings.TEMP_PATH}/{video_id}_input.mp4"
            
            logger.info(f" Downloading from S3: {temp_file_path}")
            if not storage_s3.download_file_sync(temp_file_path, local_temp_input):
                raise Exception("Failed to download video from S3")
            
            video_file_path = local_temp_input
            logger.info(f" Video downloaded to: {local_temp_input}")
        else:
            # Para NFS: usar directamente el path
            video_file_path = temp_file_path
            logger.info(f" Using local file: {video_file_path}")
        
        # PASO 2: Validate video with FFprobe
        logger.info(f" Validating video: {video_file_path}")
        metadata = validate_video_sync(video_file_path)
        
        # Update duration
        video.duration_seconds = int(metadata['duration'])
        db.commit()
        logger.info(f" Duration: {video.duration_seconds}s")
        
        # PASO 3: Process video (cutting, adding banner, watermark and resizing.)
        logger.info(f" Loading video: {video_file_path}")
        videoclip = VideoFileClip(video_file_path)

        # Intro and Outro logo
        if settings.STORAGE_TYPE == "s3":
            logo_local = f"{settings.TEMP_PATH}/logo720.png"
            logo_s3_key = "resources/logo720.png"
            
            if not os.path.exists(logo_local):
                logger.info(f" Downloading logo from S3: {logo_s3_key}")
                if not storage_s3.download_file_sync(logo_s3_key, logo_local):
                    logger.warning("⚠️ Logo not found in S3, creating temporary")
                    from PIL import Image, ImageDraw, ImageFont
                    img = Image.new('RGBA', (160, 50), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(img)
                    try:
                        font = ImageFont.truetype("arial.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                    draw.text((10, 15), "ANB Video", fill=(255, 255, 255, 255), font=font)
                    img.save(logo_local)
                    logger.info(" Temporary logo created")
            
            logo_path = Path(logo_local)
        else:
            logo_path = Path(settings.RES_PATH) / "logo720.png"
        
        logger.info(f" Using logo: {logo_path}")

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
            logger.info(" Video trimmed to 30s")

        videoclip = videoclip.with_effects([vfx.CrossFadeIn(watermark_fadein)]).resized((1280,1080))
        logger.info(" Video resized to 1280x1080")

        # Watermark (positioned at 50% from top, centered horizontally)
        watermark = (ImageClip(str(logo_path))
             .with_duration(video_duration)
             .resized(height=100)
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
        logger.info("🎬 Compositing clips...")
        final_clip = CompositeVideoClip([
            intro_logo,
            videoclip.with_start(intro_duration),
            watermark,
            outro_logo
        ])

        # Remove audio
        final_clip = final_clip.with_audio(None)
        logger.info(" Audio removed")

        # PASO 4: Export
        if settings.STORAGE_TYPE == "s3":
            os.makedirs(settings.TEMP_PATH, exist_ok=True)
            local_temp_output = f"{settings.TEMP_PATH}/{video_id}_processed.mp4"
            
            logger.info(f" Rendering to: {local_temp_output}")
            
            #  FIX: Usar parámetros simples como en versión original
            final_clip.write_videofile(
                local_temp_output,
                codec='libx264',
                audio_codec='aac'
                #  NO usar logger=None, threads, preset
            )
            
            logger.info(f" Video rendered")
            
            #  FIX: Cerrar clips ANTES de validar
            videoclip.close()
            final_clip.close()
            logger.info(" Moviepy resources closed")
            
            # Verificar tamaño
            if not os.path.exists(local_temp_output):
                raise Exception(f"Rendered file not found: {local_temp_output}")
            
            output_size = os.path.getsize(local_temp_output)
            logger.info(f" File size: {output_size / (1024*1024):.2f} MB")
            
            if output_size < 100000:  # 100KB
                raise Exception(f"Rendered file too small: {output_size} bytes")
            
            #  Validar con FFprobe (DESPUÉS de cerrar clips)
            logger.info(f" Validating processed video: {local_temp_output}")
            try:
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', local_temp_output]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise Exception(f"FFprobe failed: {result.stderr}")
                
                data = json.loads(result.stdout)
                has_video = any(s.get('codec_type') == 'video' for s in data.get('streams', []))
                
                if not has_video:
                    raise Exception("No video stream found")
                
                duration = float(data.get('format', {}).get('duration', 0))
                if duration <= 0:
                    raise Exception("Invalid duration")
                
                logger.info(f" Processed video is VALID - Duration: {duration}s")
                
            except Exception as e:
                raise Exception(f"Validation FAILED: {str(e)}")
            
            # Upload to S3
            s3_processed_key = f"processed/{video_id}.mp4"
            logger.info(f" Uploading to S3: {s3_processed_key}")
            
            if not storage_s3.upload_file_sync(local_temp_output, s3_processed_key):
                raise Exception("Failed to upload to S3")
            
            processed_file_path = s3_processed_key
            logger.info(f" Uploaded to S3: {s3_processed_key}")
            
        else:
            # Para NFS (versión original)
            temp_path = Path(temp_file_path)
            processed_folder = Path(settings.STORAGE_PATH) / "processed"
            processed_folder.mkdir(parents=True, exist_ok=True)
            
            processed_file_path = processed_folder / temp_path.name
            
            logger.info(f" Rendering to: {processed_file_path}")
            final_clip.write_videofile(str(processed_file_path))
            logger.info(" Video rendered")
            
            # Clean up
            videoclip.close()
            final_clip.close()
            logger.info(" Moviepy resources closed")
        
        # Update database record
        video.file_path = str(processed_file_path)
        video.status = "processed"
        db.commit()
        logger.info(" Database updated")
        
        # Clean up temp files
        if settings.STORAGE_TYPE == "s3":
            if local_temp_input and os.path.exists(local_temp_input):
                os.remove(local_temp_input)
                logger.info(f" Cleaned: {local_temp_input}")
            if local_temp_output and os.path.exists(local_temp_output):
                os.remove(local_temp_output)
                logger.info(f" Cleaned: {local_temp_output}")
        else:
            temp_path = Path(temp_file_path)
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f" Cleaned: {temp_file_path}")
        
        logger.info(f" Video {video_id} processed successfully!")
        
        return {
            "status": "success",
            "video_id": video_id,
            "message": "Video processed successfully",
            "file_path": str(processed_file_path)
        }
        
    except Exception as e:
        logger.error(f" ERROR: {str(e)}")
        
        # Update status to failed
        if video:
            video.status = "failed"
            db.commit()
        
        # Clean up on error
        if settings.STORAGE_TYPE == "s3":
            for temp_file in [local_temp_input, local_temp_output]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                        logger.info(f" Cleaned: {temp_file}")
                    except:
                        pass
        
        return {
            "status": "failed",
            "video_id": video_id,
            "error": str(e)
        }
        
    finally:
        db.close()