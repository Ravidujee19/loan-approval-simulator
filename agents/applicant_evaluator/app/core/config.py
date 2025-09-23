from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator
from urllib.parse import urlsplit
import json

class Settings(BaseSettings):
    ENV: str = "dev"
    API_TITLE: str = "Applicant Evaluator API"
    API_VERSION: str = "v1"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]

    DATABASE_URL: str = "postgresql+psycopg2://app:app@localhost:5432/evaluator"
    RATE_LIMIT_DEFAULT_PER_MIN: int = 60
    RATE_LIMIT_ADMIN_PER_MIN: int = 30
    CACHE_BACKEND: str = "memory"
    REDIS_URL: str = "redis://localhost:6379/0"
    IDEMPOTENCY_TTL_SECONDS: int = 60 * 60 * 24

    ANNUAL_INTEREST_RATE: float = 0.12
    MIN_INCOME: float = 50000.0
    UNEMPLOYED_MIN_OTHER_INCOME: float = 25000.0
    MAX_DEBT_RATIO: float = 0.40

    ENABLE_OTEL: bool = False
    PROMETHEUS_ENABLED: bool = True

    SEED_ON_START: bool = True
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "Admin@12345"

    # save applicant+loan JSON bundles for manith
    SCORE_STORE_DIR: str = "data/score_store"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        # Accept JSON string, CSV, single string, or list
        if isinstance(v, list):
            raw = v
        elif isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                raw = json.loads(s)
            elif "," in s:
                raw = [p.strip() for p in s.split(",") if p.strip()]
            else:
                raw = [s]
        else:
            raw = v

        # Normalize: strip trailing '/', lower scheme/host, keep explicit port
        def norm(u: str) -> str:
            u = u.strip().rstrip("/")
            sp = urlsplit(u)
            # Rebuild with scheme://host[:port]
            host = sp.hostname or ""
            port = f":{sp.port}" if sp.port else ""
            scheme = (sp.scheme or "http").lower()
            return f"{scheme}://{host.lower()}{port}"

        return [norm(u) for u in raw]

@lru_cache
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]