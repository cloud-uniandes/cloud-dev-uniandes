from app.storage.base_storage import BaseStorage
from app.storage.local_storage import LocalStorage 
from app.storage.s3_storage import S3Storage
from app.core.config import settings

class FileService:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    async def save_file(self, file_content: bytes, filename: str, subfolder: str = "uploads"):
        path = await self.storage.save_file(file_content, filename, subfolder)
        return str(path)

    async def delete_file(self, path: str):
        await self.storage.delete_file(path)
    
    def get_file_url(self, path:str):
        return self.storage.get_file_url(path)

def create_storage() -> BaseStorage:
    storage_type = getattr(settings, "STORAGE_TYPE", "local").lower()
    if storage_type == "s3":
        return S3Storage()
    else:
        return LocalStorage()


storage = create_storage()
fileservice = FileService(storage)