"""Environment settings. Refuses to start against live PayPal (sandbox-only hackathon build)."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_webhook_id: str = ""
    paypal_api_base_url: str = "https://api-m.sandbox.paypal.com"

    env: str = "local_test"
    demo_mode: bool = True
    database_url: str = "sqlite:///./gameya.db"
    frontend_origin: str = "http://localhost:5173"

    gemini_api_key: str = ""

    @field_validator("paypal_api_base_url")
    @classmethod
    def sandbox_only(cls, v: str) -> str:
        if "sandbox.paypal.com" not in v:
            raise ValueError("PAYPAL_API_BASE_URL must point at the PayPal sandbox")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
