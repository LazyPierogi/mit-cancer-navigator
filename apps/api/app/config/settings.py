from pathlib import Path

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    app_name: str = "Lung Cancer Treatment Navigator API"
    app_env: str = "development"
    database_url: str = Field(
        default=f"sqlite:///{ROOT_DIR / 'apps' / 'api' / 'navigator.db'}",
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL"),
    )
    redis_url: str = "redis://localhost:6379/0"
    pubmed_email: str = "team@example.edu"
    pubmed_tool: str = "lung-cancer-treatment-navigator"
    ruleset_version: str = "mvp-2026-02-28"
    corpus_version: str = "sample-corpus-v1"
    safety_template_version: str = "safety-v1"
    input_schema_version: str = "vignette-v1"
    api_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()
