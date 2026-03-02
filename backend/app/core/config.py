from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    env: str = "dev"
    api_key: str = "change-me"

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "root"
    db_name: str = "mamutero"

    redis_url: str = "redis://redis:6379/0"
    rq_queue: str = "mamutero"

    videos_dir: str = "/data/videos"
    whisper_dir: str = "/data/whisper"
    logs_dir: str = "/data/logs/jobs"

    whisper_model: str = "large"
    whisper_device: str = "cpu"
    whisper_language_default: str = "es"

    yt_dlp_path: str = "yt-dlp"
    ffmpeg_path: str = "ffmpeg"

    youtube_api_key: str = ""

    page_size_default: int = 25
    page_size_max: int = 100

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()