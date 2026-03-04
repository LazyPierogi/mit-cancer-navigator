import os
from pathlib import Path

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_SQLITE_PATH = ROOT_DIR / "apps" / "api" / "navigator.db"
VERCEL_SQLITE_PATH = Path("/tmp/navigator.db")


def _default_database_url() -> str:
    if os.getenv("VERCEL"):
        return f"sqlite:///{VERCEL_SQLITE_PATH}"
    return f"sqlite:///{DEFAULT_SQLITE_PATH}"


class Settings(BaseSettings):
    app_name: str = "Lung Cancer Treatment Navigator API"
    app_env: str = "development"
    database_url: str = Field(
        default_factory=_default_database_url,
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL"),
    )
    redis_url: str = "redis://localhost:6379/0"
    pubmed_email: str = "team@example.edu"
    pubmed_tool: str = "lung-cancer-treatment-navigator"
    ruleset_version: str = "mvp-2026-02-28"
    corpus_version: str = "curated-preview-v2"
    safety_template_version: str = "safety-v1"
    input_schema_version: str = "vignette-v2"
    api_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()
