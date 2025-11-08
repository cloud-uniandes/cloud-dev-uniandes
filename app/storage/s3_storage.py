"""
S3 Storage Implementation - Compatible with BaseStorage interface
Uses IAM roles when running on AWS (no credentials needed)
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import logging
import asyncio
from functools import partial
from io import BytesIO

from .base_storage import BaseStorage
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Storage(BaseStorage):
    """
    Implementación de BaseStorage usando Amazon S3
    Mantiene la misma interfaz que LocalStorage
    
    Credenciales:
    - En AWS (EC2/ECS): Usa automáticamente el IAM Role asignado
    - En local: Usa credenciales de settings (si existen) o ~/.aws/credentials
    """
    
    def __init__(self):
        """
        Inicializar cliente S3
        
        boto3 busca credenciales en este orden:
        1. Parámetros explícitos (aws_access_key_id, aws_secret_access_key)
        2. Variables de entorno (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        3. Archivo ~/.aws/credentials
        4. IAM Role (si está en EC2/ECS/Lambda)
        """
        
        # Si las credenciales están en settings (no None), usarlas
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            logger.info("🔑 Using AWS credentials from settings (environment variables)")
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        else:
            # boto3 buscará automáticamente las credenciales:
            # - En ~/.aws/credentials (desarrollo local)
            # - En IAM Role (si está en EC2/ECS)
            logger.info("🔐 Using AWS credentials from IAM role or AWS CLI config")
            self.s3_client = boto3.client(
                's3',
                region_name=settings.AWS_REGION
            )
        
        self.bucket_name = settings.S3_BUCKET_NAME
        
        # Verificar conexión
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ S3Storage initialized - Bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"❌ Bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                logger.error(f"❌ Access denied to bucket '{self.bucket_name}'. Check IAM permissions.")
            else:
                logger.error(f"❌ Error connecting to S3: {e}")
            raise
    
    async def save_file(self, file_content: bytes, filename: str, subfolder: str = "uploads") -> str:
        """
        Save file to S3 and return the S3 key
        
        Args:
            file_content: File content in bytes
            filename: Name of the file
            subfolder: Subfolder (uploads, processed, temp)
        
        Returns:
            str: S3 key (ej: "uploads/video123.mp4")
        """
        # Construir S3 key igual que LocalStorage construye el path
        s3_key = f"{subfolder}/{filename}"
        
        try:
            loop = asyncio.get_event_loop()
            
            # ✅ FIX: Especificar Content-Type para video
            await loop.run_in_executor(
                None,
                partial(
                    self.s3_client.upload_fileobj,
                    BytesIO(file_content),
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': 'video/mp4',  # ✅ CRÍTICO
                        'ContentDisposition': 'inline'
                    }
                )
            )
            logger.info(f"✅ File uploaded to S3: {s3_key}")
            
            # Retornar S3 key (similar a como LocalStorage retorna path)
            return s3_key
            
        except ClientError as e:
            logger.error(f"❌ Error uploading to S3: {e}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    async def delete_file(self, path: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            path: S3 key del archivo (ej: "uploads/video123.mp4")
        
        Returns:
            bool: True if successful
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                partial(
                    self.s3_client.delete_object,
                    Bucket=self.bucket_name,
                    Key=path
                )
            )
            logger.info(f"🗑️ File deleted from S3: {path}")
            return True
        except ClientError as e:
            logger.error(f"❌ Error deleting from S3: {e}")
            return False
    
    def get_file_url(self, path: str) -> str:
        """
        Return a presigned URL for file access
        
        Args:
            path: S3 key del archivo
        
        Returns:
            str: Pre-signed URL (válida por 1 hora)
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': path},
                ExpiresIn=3600  # 1 hora
            )
            logger.info(f"🔗 Generated presigned URL for: {path}")
            return url
        except ClientError as e:
            logger.error(f"❌ Error generating presigned URL: {e}")
            return ""
    
    # Métodos adicionales útiles para Celery (síncrono)
    def upload_file_sync(self, local_path: str, s3_key: str) -> bool:
        """Upload file from local path to S3 (synchronous for Celery)"""
        try:
            # ✅ FIX CRÍTICO: Leer archivo como binario y especificar Content-Type
            import os
            
            # Verificar que el archivo existe
            if not os.path.exists(local_path):
                logger.error(f"❌ File not found: {local_path}")
                return False
            
            # Leer archivo en modo binario
            with open(local_path, 'rb') as f:
                file_data = f.read()
            
            # Verificar que no está vacío
            if len(file_data) == 0:
                logger.error(f"❌ File is empty: {local_path}")
                return False
            
            logger.info(f"📦 Uploading {len(file_data) / (1024*1024):.2f} MB to S3: {s3_key}")
            
            # Subir como binario con Content-Type correcto
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,  # ✅ Buffer binario (no path string)
                ContentType='video/mp4',  # ✅ CRÍTICO
                ContentDisposition='inline'
            )
            
            logger.info(f"✅ Uploaded to S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Error uploading file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error uploading file: {e}")
            return False
    
    def download_file_sync(self, s3_key: str, local_path: str) -> bool:
        """Download file from S3 to local path (synchronous for Celery)"""
        try:
            import os
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # ✅ FIX: Descargar y escribir en modo binario
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            
            with open(local_path, 'wb') as f:  # ✅ 'wb' = write binary
                f.write(response['Body'].read())
            
            # Verificar que se descargó correctamente
            if not os.path.exists(local_path):
                logger.error(f"❌ Downloaded file not found: {local_path}")
                return False
            
            file_size = os.path.getsize(local_path)
            logger.info(f"✅ Downloaded from S3: {s3_key} ({file_size / (1024*1024):.2f} MB)")
            
            return True
            
        except ClientError as e:
            logger.error(f"❌ Error downloading file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading file: {e}")
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False