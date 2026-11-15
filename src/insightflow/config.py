import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INSIGHTFLOW_")

    app_name: str = "InsightFlow BI"
    db_path: str = Field(default=":memory:", description="SQLite database file path or :memory:")
    max_query_limit: int = Field(default=100, description="Enforced max row limit on analytical queries")
    query_timeout_seconds: float = Field(default=5.0, description="Max query execution time")
