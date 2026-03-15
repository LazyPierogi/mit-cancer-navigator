import os
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.versioning import load_version_manifest


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SQLITE_PATH = next(
    (
        candidate
        for candidate in (
            PACKAGE_ROOT / "navigator.db",
            REPO_ROOT / "apps" / "api" / "navigator.db",
        )
        if candidate.exists()
    ),
    PACKAGE_ROOT / "navigator.db",
)
VERCEL_SQLITE_PATH = Path("/tmp/navigator.db")


def _default_database_url() -> str:
    if os.getenv("VERCEL"):
        return f"sqlite:///{VERCEL_SQLITE_PATH}"
    return f"sqlite:///{DEFAULT_SQLITE_PATH}"


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgresql+"):
        return value
    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value.removeprefix("postgresql://")
    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value.removeprefix("postgres://")
    return value


class Settings(BaseSettings):
    _version_manifest: dict[str, object] = load_version_manifest()
    app_name: str = "Lung Cancer Treatment Navigator API"
    app_env: str = "development"
    database_url: str = Field(
        default_factory=_default_database_url,
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL_NON_POOLING", "POSTGRES_URL"),
    )
    redis_url: str = "redis://localhost:6379/0"
    pubmed_email: str = "team@example.edu"
    pubmed_tool: str = "lung-cancer-treatment-navigator"
    semantic_vector_backend: str = "local"
    semantic_retrieval_default_mode: str = "hybrid"
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection_pubmed: str = "navigator-pubmed"
    qdrant_collection_esmo: str = "navigator-esmo"
    embedding_provider: str = "local"
    embedding_model: str = "hash-embedding-v1"
    embedding_api_key: str | None = None
    llm_provider: str = "disabled"
    llm_api_key: str | None = None
    llm_model: str = ""
    semantic_top_k: int = 25
    semantic_rrf_k: int = 60
    ruleset_version: str = str(_version_manifest.get("rulesetVersion", "mvp-2026-02-28"))
    corpus_version: str = str(_version_manifest.get("corpusVersion", "curated-preview-v2"))
    safety_template_version: str = "safety-v1"
    input_schema_version: str = "vignette-v2"
    api_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), env_prefix="", extra="ignore")

    @model_validator(mode="after")
    def normalize_database_url(self) -> "Settings":
        self.database_url = _normalize_database_url(self.database_url)
        return self


settings = Settings()
