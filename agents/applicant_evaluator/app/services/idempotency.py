# Idempotency-Key storage (DB/Redis)

import hashlib
import json
import time

from agents.applicant_evaluator.app.core.config import settings


class IdempotencyStore:
    _mem: dict[str, tuple[str, dict, float]] = {}

    @staticmethod
    def _hash_body(body: object) -> str:
        return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()

    @classmethod
    def get(cls, key: str, body) -> dict | None:
        ttl = settings().IDEMPOTENCY_TTL_SECONDS
        record = cls._mem.get(key)
        if not record:
            return None
        body_hash, response, ts = record
        if time.time() - ts > ttl:
            cls._mem.pop(key, None)
            return None
        if body_hash != cls._hash_body(body.model_dump() if hasattr(body, "model_dump") else body):
            return None
        return response

    @classmethod
    def set(cls, key: str, body, response: dict) -> None:
        cls._mem[key] = (
            cls._hash_body(body.model_dump() if hasattr(body, "model_dump") else body),
            response,
            time.time(),
        )
