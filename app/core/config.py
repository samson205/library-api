import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")


BASE_DIR = Path(__file__).parent.parent.parent
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
STORAGE_ROOT = BASE_DIR / "storage"
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_BOOK_EXTENSIONS = {".epub", ".fb2", ".pdf"}
MAX_IMAGE_SIZE = 3 * 1024 * 1024
MAX_BOOK_SIZE = 100 * 1024 * 1024
