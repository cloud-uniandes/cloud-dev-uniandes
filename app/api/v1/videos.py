from fastapi import APIRouter, Depends, File, UploadFile, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import uuid
from pathlib import Path
import aiofiles

from app.core.message_producer import SQSMessageProducer
from app.db.session import get_db
from app.schemas.video import (
    VideoUploadResponse,
    VideoListItem,
    VideoDetail,
    VideoDeleteResponse,
    VideoPublishResponse
)
from app.repositories.video_repository import video_repository
from app.storage.file_service import fileservice
from app.utils.video_validator import validate_video
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.exceptions import (
    ValidationException,
    NotFoundException,
    ForbiddenException
)

import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError

router = APIRouter()
producer = SQSMessageProducer(queue_name='message-queue')

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=VideoUploadResponse,
    summary="📤 Upload a video",
    description="Upload a video file. **Requires JWT authentication**.",
    responses={
        201: {"description": "Video uploaded successfully"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        400: {"description": "Bad request - Invalid file or data"}
    }
)
async def upload_video(
    video_file: UploadFile = File(..., description="Video file to upload (MP4 format)"),
    title: str = Form(..., min_length=1, max_length=200, description="Video title"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a video file (JWT Protected)"""
    if not video_file.content_type or not video_file.content_type.startswith("video/"):
        raise ValidationException("File must be a video")
    
    file_content = await video_file.read()
    file_size = len(file_content)
    
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise ValidationException(f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE_MB}MB)")
    
    # Generate unique filename
    video_id = uuid.uuid4()
    temp_filename = f"{video_id}.mp4"
    
    # Save file to uploads folder (temp location for processing)
    temp_file_path = await fileservice.save_file(file_content=file_content, filename=f"{video_id}.mp4", subfolder="uploads")
    
    # Create video record in database with status="uploaded"
    video = await video_repository.create(
        db=db,
        user_id=current_user.id,
        title=title,
        original_filename=video_file.filename or "video.mp4",
        file_path=str(temp_file_path),
        duration_seconds=0,
        file_size_bytes=file_size,
        status="uploaded"
    )
    
    # Queue the video processing task
    producer.send_message(str(video_id), str(temp_file_path))
    #task = process_video_task.delay(str(video.id), str(temp_file_path))
    
    return VideoUploadResponse(
        message="Video uploaded successfully and queued for processing",
        task_id=str(video.id)
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=List[VideoListItem],
    summary="List user's videos",
    description="Get all videos uploaded by the authenticated user. **Requires JWT authentication**.",
    responses={
        200: {"description": "List of user's videos"},
        401: {"description": "Unauthorized - Invalid or missing token"}
    }
)
async def list_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all videos for authenticated user (JWT Protected)"""
    videos = await video_repository.get_by_user(db, current_user.id)
    
    return [
        VideoListItem(
            video_id=str(v.id),
            title=v.title,
            status=v.status,
            uploaded_at=v.uploaded_at,
            file_path=v.file_path if v.status == "processed" else None
        )
        for v in videos
    ]


@router.get(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoDetail,
    summary="🔍 Get video details",
    description="Get detailed information about a specific video. **Requires JWT authentication**.",
    responses={
        200: {"description": "Video details"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Not the video owner"},
        404: {"description": "Video not found"}
    }
)
async def get_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get video details (JWT Protected)"""
    try:
        video_uuid = UUID(video_id)
    except ValueError:
        raise ValidationException("Invalid UUID format")
    
    video = await video_repository.get_by_id(db, video_uuid)
    
    if not video:
        raise NotFoundException("Video not found")
    
    if video.user_id != current_user.id:
        raise ForbiddenException("You don't have permission to view this video")
    
    return VideoDetail(
        video_id=str(video.id),
        title=video.title,
        status=video.status,
        uploaded_at=video.uploaded_at,
        file_path=video.file_path,
        votes=video.votes_count,
        duration_seconds=video.duration_seconds,
        file_size_bytes=video.file_size_bytes,
        is_public=video.is_public
    )


@router.put(
    "/{video_id}/publish",
    status_code=status.HTTP_200_OK,
    response_model=VideoPublishResponse,
    summary="🌐 Publish a video",
    description="Make a video public. **Requires JWT authentication**.",
    responses={
        200: {"description": "Video published successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Video not found"}
    }
)
async def publish_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Make a video public (JWT Protected)"""
    try:
        video_uuid = UUID(video_id)
    except ValueError:
        raise ValidationException("Invalid UUID format")
    
    video = await video_repository.get_by_id(db, video_uuid)
    
    if not video:
        raise NotFoundException("Video not found")
    
    if video.user_id != current_user.id:
        raise ForbiddenException("You don't have permission to publish this video")
    
    if video.status != "processed":
        raise ValidationException("Video must be processed before publishing")
    
    # Actualizar el video
    video.is_public = True
    db.add(video)
    await db.commit()
    await db.refresh(video) 
    
    return VideoPublishResponse(
        message="Video published successfully",
        video_id=str(video.id)  
    )


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoDeleteResponse,
    summary="🗑️ Delete a video",
    description="Delete a video. **Requires JWT authentication**.",
    responses={
        200: {"description": "Video deleted successfully"},
        400: {"description": "Cannot delete public video"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Video not found"}
    }
)
async def delete_video(
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a video (JWT Protected)"""
    try:
        video_uuid = UUID(video_id)
    except ValueError:
        raise ValidationException("Invalid UUID format")
    
    video = await video_repository.get_by_id(db, video_uuid)
    
    if not video:
        raise NotFoundException("Video not found")
    
    if video.user_id != current_user.id:
        raise ForbiddenException("You don't have permission to delete this video")
    
   
    if video.is_public:
        raise ValidationException("Cannot delete a public video")
    
    # Eliminar archivo físico
    try:
        await fileservice.delete_file(video.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Eliminar registro de BD
    await video_repository.delete(db, video_uuid)
    
    return VideoDeleteResponse(
        message="Video deleted successfully",
        video_id=str(video.id) 
    )