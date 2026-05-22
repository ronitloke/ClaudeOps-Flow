from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "ClaudeOps Flow API"
    app_env: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    llm_provider: str = "claude"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-4-5"
    claude_max_tokens: int = 300
    claude_temperature: float = 0.0

    llm_input_cost_per_1m_tokens: float = 0.0
    llm_output_cost_per_1m_tokens: float = 0.0

    llm_max_retries: int = 1
    llm_retry_delay_seconds: float = 1.0

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/claudeops_flow"
    fastapi_base_url: str = "http://127.0.0.1:8000"

    enable_automation_hooks: bool = True
    slack_webhook_url: str = ""
    generic_webhook_url: str = ""

    enable_zapier_hook: bool = True
    zapier_webhook_url: str = ""

    enable_make_hook: bool = True
    make_webhook_url: str = ""

    raw_data_dir: str = str(BASE_DIR / "data" / "raw")
    processed_data_dir: str = str(BASE_DIR / "data" / "processed")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()