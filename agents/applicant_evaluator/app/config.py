from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

def _find_env() -> str:
    here = Path(__file__).resolve()
    for i in range(6):
        cand = here.parents[i] / ".env"
        if cand.exists():
            return str(cand)
    return ".env"

class Settings(BaseSettings):
    STORAGE_DIR: str = "./_ae_store"
    SCORE_AGENT_URL: str = "http://localhost:8100/api/v1/score" # url ek ube
    CORS_ALLOW_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = _find_env()  
        extra = "ignore"

def settings() -> Settings:
    return Settings()
