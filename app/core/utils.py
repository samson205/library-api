import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException, status

from app.core.config import ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE, MEDIA_ROOT, BASE_DIR


async def save_image(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, WebP images are allowed"
        )
    
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image is too large"
        )
    
    image_folder = MEDIA_ROOT / "images"
    image_folder.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "").suffix.lower() or ".jpg"
    file_name = f"{uuid.uuid4()}{extension}"
    file_path = image_folder / file_name
    file_path.write_bytes(content)

    return f"/media/images/{file_name}"


def remove_image(url: str | None) -> None:
    if not url:
        return
    relative_path = url.lstrip("/")
    file_path = BASE_DIR / relative_path
    if file_path.exists():
        file_path.unlink()
