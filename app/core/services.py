import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile, HTTPException, status

from app.core.config import BASE_DIR, ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, MEDIA_ROOT


class StorageService:
    CHUNK_SIZE = 1024 * 1024

    @staticmethod
    async def save_file(file: UploadFile, folder: Path, max_size: int) -> tuple[str, int]:        
        folder.mkdir(parents=True, exist_ok=True)
        extension = StorageService.get_file_extension(filename=file.filename)
        filename = f"{uuid.uuid4()}{extension}"
        file_path = folder / filename

        total_size = 0
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await file.read(StorageService.CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > max_size:
                    await out_file.close()
                    if file_path.exists():
                        file_path.unlink()

                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File is too large"
                    )
                await out_file.write(chunk)

        await file.close()
        return filename, total_size
    
    @staticmethod
    def remove_file(path: Path | None) -> None:
        if not path:
            return
        file_path = BASE_DIR / path
        if file_path.exists():
            file_path.unlink()

    @staticmethod
    async def save_image(image: UploadFile | None, sub_folder: str) -> str | None:
        if not image:
            return None
        if image and image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG, PNG, WebP images are allowed"
            )
        images_path = MEDIA_ROOT / sub_folder / "images"
        image_name, _ = await StorageService.save_file(image, images_path, MAX_IMAGE_SIZE)
        image_url = f"{sub_folder}/images/{image_name}"
        return image_url

    @staticmethod
    def get_file_extension(filename: str | None) -> str:
        return Path(filename or "").suffix.lower()
