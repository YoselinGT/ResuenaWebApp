"""Cliente Redis async compartido (cache, OTP, sesiones efímeras).

Un único pool por proceso. `decode_responses=True` para trabajar con str.
"""

from __future__ import annotations

import redis.asyncio as redis

from src.config.settings import get_settings

settings = get_settings()

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Devuelve el cliente Redis singleton."""
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client
