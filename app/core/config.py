from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    SECRET_KEY: str = ""
    ALGORITHM: str = ""
    DB_URL: str = ""
    TEST_DB_URL: str = ""

    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}
    ALLOWED_BOOK_EXTENSIONS: set[str] = {".epub", ".fb2", ".pdf"}
    MAX_IMAGE_SIZE: int = 3 * 1024 * 1024
    MAX_BOOK_SIZE: int = 100 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore"
    )

    @property
    def MEDIA_ROOT(self) -> Path:
        path = BASE_DIR / "media"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def STORAGE_ROOT(self) -> Path:
        path = BASE_DIR / "storage"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
