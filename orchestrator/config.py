from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://models.inference.ai.azure.com"
    openai_model: str = "gpt-4o"
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
