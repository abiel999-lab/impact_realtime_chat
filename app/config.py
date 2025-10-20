from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List

class Settings(BaseSettings):
    app_name: str = Field(default="Impact Realtime Chat (FastAPI)", alias="APP_NAME")
    env: str = Field(default="dev", alias="ENV")
    database_url: str = Field(default="sqlite:///./chat.db", alias="DATABASE_URL")

    # CORS/Socket.IO origins
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"], alias="ALLOWED_ORIGINS")
    sio_cors_origins: List[str] = Field(default_factory=lambda: ["*"], alias="SIO_CORS_ORIGINS")

    default_room: str = Field(default="lobby", alias="DEFAULT_ROOM")

    # Uploads
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_mb: int = Field(default=50, alias="MAX_UPLOAD_MB")  # batas server-side soft limit

    @field_validator("allowed_origins", "sio_cors_origins", mode="before")
    @classmethod
    def parse_list(cls, v):
        if v is None or v == "":
            return ["*"]
        if isinstance(v, list):
            return v
        s = str(v).strip()
        if s.startswith("["):
            import json
            try:
                return json.loads(s)
            except Exception:
                pass
        return [x.strip() for x in s.split(",") if x.strip()]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "populate_by_name": True,
    }

settings = Settings()
