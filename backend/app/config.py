from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    notion_api_key: str = ""
    notion_database_id: str = "2b89a109ef108015ac7ae62c5e4ac0aa"
    gemini_api_key: str = ""
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
