from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
import dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"  # backend/.env


class Settings(BaseSettings):
    BACKEND_PORT: int = 8000
    SECRET_KEY: str

    MODEL_ARTIFACT_PATH: str = "ml_training/artifacts/wip_final_jan_oct_extra_trees/pipeline.pkl"

    SWEEPER_ENABLED: bool = True
    SWEEPER_INTERVAL_SECONDS: int = 60
    PROCESSING_TIMEOUT_MINUTES: int = 10

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="forbid",
    )


settings = Settings()

def update_active_model_path(new_path: str):
    """Update the MODEL_ARTIFACT_PATH in .env file and settings"""
    dotenv.set_key(str(ENV_FILE), "MODEL_ARTIFACT_PATH", new_path)
    settings.MODEL_ARTIFACT_PATH = new_path
