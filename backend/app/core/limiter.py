import redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _get_storage_uri() -> str:
    # Use Redis if URL is configured and Redis server is actively responding; fallback to in-memory storage
    if settings.REDIS_URL and "redis://" in settings.REDIS_URL:
        try:
            r = redis.from_url(settings.REDIS_URL, socket_timeout=0.2, socket_connect_timeout=0.2)
            if r.ping():
                return settings.REDIS_URL
        except Exception:
            pass
    return "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_get_storage_uri(),
    strategy="fixed-window"
)
