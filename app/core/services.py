import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile, HTTPException, status

from app.core.config import BASE_DIR


class StorageService:
    CHUNK_SIZE = 1024 * 1024

    @staticmethod
    async def save_file(file: UploadFile, folder: Path, max_size: int) -> tuple[str, int]:        
        folder.mkdir(parents=True, exist_ok=True)
        extension = Path(file.filename or "").suffix.lower()
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
    def remove_file(url: str | None) -> None:
        if not url:
            return
        file_path = BASE_DIR / url.lstrip("/")
        if file_path.exists():
            file_path.unlink()
