import subprocess
import json
from typing import Dict
from app.core.exceptions import ValidationException


def validate_video_sync(file_path: str) -> Dict:
    """
    Synchronous version of validate_video for Celery workers.
    Validate video file using ffprobe.
    Returns metadata dict with duration, width, height.
    Raises ValidationException if video is invalid.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise ValidationException("Unable to process video file")
        
        metadata = json.loads(result.stdout)
        
        # Find video stream
        video_stream = next(
            (s for s in metadata.get('streams', []) if s.get('codec_type') == 'video'),
            None
        )
        
        if not video_stream:
            raise ValidationException("No video stream found in file")
        
        # Extract information
        duration = float(metadata.get('format', {}).get('duration', 0))
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        
        # Validate duration (20-60 seconds as per requirements)
        if duration < 20 or duration > 60:
            raise ValidationException(
                f"Video duration must be between 20 and 60 seconds (current: {duration:.1f}s)"
            )
        
        # Validate resolution (minimum 1080p as per requirements)
        if height < 1080:
            raise ValidationException(
                f"Video resolution must be at least 1080 (current: {height}p)"
            )
        
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'codec': video_stream.get('codec_name', 'unknown')
        }
        
    except subprocess.TimeoutExpired:
        raise ValidationException("Video validation timeout")
    except json.JSONDecodeError:
        raise ValidationException("Unable to parse video metadata")
    except Exception as e:
        if isinstance(e, ValidationException):
            raise
        raise ValidationException(f"Video validation error: {str(e)}")


async def validate_video(file_path: str) -> Dict:
    """
    Async version - just wraps the sync version for compatibility.
    This is used by the FastAPI endpoints.
    """
    return validate_video_sync(file_path)