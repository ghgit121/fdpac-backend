from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_ssl_query_for_asyncpg(database_url: str) -> str:
    parsed = urlparse(database_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    if sslmode and "ssl" not in query:
        query["ssl"] = sslmode
    return urlunparse(parsed._replace(query=urlencode(query)))


def _normalize_database_url(raw_url: str, async_mode: bool) -> str:
    database_url = raw_url.strip()

    if async_mode:
        if database_url.startswith("postgresql+psycopg2://"):
            database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        elif database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

        if database_url.startswith("postgresql+asyncpg://"):
            return _normalize_ssl_query_for_asyncpg(database_url)
        return database_url

    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    if database_url.startswith("sqlite+aiosqlite:///"):
        return database_url.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return database_url


class Settings(BaseSettings):
    app_name: str = "Finance Data Processing and Access Control Dashboard"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fdpac"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 24 * 60
    cors_origins: str = "http://localhost:3000"
    rate_limit_per_minute: int = 60

    @property
    def async_database_url(self) -> str:
        return _normalize_database_url(self.database_url, async_mode=True)

    @property
    def sync_database_url(self) -> str:
        return _normalize_database_url(self.database_url, async_mode=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
