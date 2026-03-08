from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEYS = {
    "CHANGE_ME_TO_A_SECURE_RANDOM_SECRET",
    "PLEASE_REPLACE_WITH_A_LONG_RANDOM_SECRET",
}
DEFAULT_ADMIN_PASSWORDS = {
    "dier2010",
    "admin123",
    "changeme",
    "password",
}


def _parse_csv_values(raw_values: str) -> list[str]:
    if not raw_values.strip():
        return []
    return [value.strip().rstrip("/") for value in raw_values.split(",") if value.strip()]


class Settings(BaseSettings):
    environment: Literal["development", "staging", "production"] = "development"
    app_name: str = "Online Market API"
    api_prefix: str = "/api"
    secret_key: str = "CHANGE_ME_TO_A_SECURE_RANDOM_SECRET"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./market.db"
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = ""
    trusted_hosts: str = "*"
    admin_phone: str = "+998931981793"
    admin_email: str = ""
    admin_password: str = "dier2010"
    seed_catalog_on_startup: bool = True
    docs_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if not self.is_production:
            return self

        if self.secret_key in DEFAULT_SECRET_KEYS or len(self.secret_key) < 32:
            raise ValueError(
                "Productionda SECRET_KEY kamida 32 belgili va default qiymatdan farqli bo'lishi kerak."
            )

        if self.admin_password in DEFAULT_ADMIN_PASSWORDS or len(self.admin_password) < 8:
            raise ValueError(
                "Productionda ADMIN_PASSWORD default bo'lmasligi va kamida 8 belgidan iborat bo'lishi kerak."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def parse_cors_origins(raw_origins: str) -> list[str]:
    return _parse_csv_values(raw_origins)


def parse_trusted_hosts(raw_hosts: str) -> list[str]:
    hosts = _parse_csv_values(raw_hosts)
    return hosts or ["*"]
