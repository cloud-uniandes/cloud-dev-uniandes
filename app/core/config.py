from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # Storage Configuration
    STORAGE_TYPE: str = "local"  # "local" (NFS) o "s3" (Amazon S3)
    STORAGE_PATH: str = "./storage"  # Solo para STORAGE_TYPE=local
    
    # AWS S3 Configuration
    # Si están en None, boto3 usará IAM Role (en EC2) o ~/.aws/credentials (local)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None  # Requerido solo si STORAGE_TYPE=s3
    
    # Storage Local (temporal)
    TEMP_PATH: str = "/tmp/anb-temp"
    
    # Security
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # App
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv"]
    VIDEO_RESOLUTIONS: List[str] = ["360p", "480p", "720p"]
    CORS_ORIGINS: List[str] = ["*"]
    
    
    class Config:
        env_file = ".env"
        extra = "allow"
        case_sensitive = False 

settings = Settings()


# Validar configuración S3 si está habilitado
if settings.STORAGE_TYPE == "s3":
    if not settings.S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME is required when STORAGE_TYPE=s3")

# Crear directorio temporal si no existe
os.makedirs(settings.TEMP_PATH, exist_ok=True)
if settings.STORAGE_TYPE == "local":
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)