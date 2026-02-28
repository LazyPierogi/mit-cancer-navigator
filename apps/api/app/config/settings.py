from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Lung Cancer Treatment Navigator API"
    app_env: str = "development"
    postgres_url: str = "postgresql://navigator:navigator@localhost:5432/navigator"
    redis_url: str = "redis://localhost:6379/0"
    pubmed_email: str = "team@example.edu"
    pubmed_tool: str = "lung-cancer-treatment-navigator"
    ruleset_version: str = "mvp-2026-02-28"
    corpus_version: str = "sample-corpus-v1"
    safety_template_version: str = "safety-v1"
    input_schema_version: str = "vignette-v1"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()

