"""アプリケーション設定。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定。環境変数から自動読み込みする。"""

    anthropic_api_key: str = ""
    redmine_url: str = "http://localhost:8080"
    redmine_api_key: str = ""
    redmine_default_project_id: int = 1
    claude_model: str = "claude-opus-4-6"
    agent_max_tokens: int = 4096
    redmine_timeout: int = 30
    redmine_max_retries: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """設定シングルトンを返す。"""
    return Settings()
