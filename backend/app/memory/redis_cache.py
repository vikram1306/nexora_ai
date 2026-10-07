import json
import hashlib
import time
import os
from typing import Dict, Any, Optional, List
import redis
from app.core.config import settings

class EnterpriseCacheManager:
    """Enterprise Redis Caching Layer with TTL management, cache invalidation, and zero-downtime in-memory fallback."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnterpriseCacheManager, cls).__new__(cls)
            cls._instance._init_cache()
        return cls._instance

    def _init_cache(self):
        self._redis_client = None
        self._is_connected = False
        self._fallback_store: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        self._connect_redis()

    def _connect_redis(self):
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        if redis_url and "redis://" in redis_url:
            try:
                client = redis.from_url(
                    redis_url,
                    socket_timeout=0.3,
                    socket_connect_timeout=0.3,
                    decode_responses=True
                )
                if client.ping():
                    self._redis_client = client
                    self._is_connected = True
                    return
            except Exception:
                pass
        self._redis_client = None
        self._is_connected = False

    def is_connected(self) -> bool:
        if self._redis_client:
            try:
                return bool(self._redis_client.ping())
            except Exception:
                self._is_connected = False
                return False
        return False

    def _hash_key(self, key_str: str) -> str:
        return hashlib.sha256(key_str.strip().lower().encode("utf-8")).hexdigest()[:16]

    # --- Generic Get / Set with fallback ---
    def get(self, key: str) -> Optional[Any]:
        if self.is_connected():
            try:
                val = self._redis_client.get(key)
                if val is not None:
                    self._hits += 1
                    return json.loads(val)
            except Exception:
                pass

        # In-Memory Fallback
        entry = self._fallback_store.get(key)
        if entry:
            if entry["expires_at"] is None or entry["expires_at"] > time.time():
                self._hits += 1
                return entry["data"]
            else:
                del self._fallback_store[key]

        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = 3600):
        val_str = json.dumps(value)
        if self.is_connected():
            try:
                if ttl:
                    self._redis_client.setex(key, ttl, val_str)
                else:
                    self._redis_client.set(key, val_str)
            except Exception:
                pass

        # Always keep in fallback as well for resilient recovery
        self._fallback_store[key] = {
            "data": value,
            "expires_at": time.time() + ttl if ttl else None
        }

    def delete(self, key: str):
        if self.is_connected():
            try:
                self._redis_client.delete(key)
            except Exception:
                pass
        self._fallback_store.pop(key, None)

    def delete_prefix(self, prefix: str):
        if self.is_connected():
            try:
                keys = self._redis_client.keys(f"{prefix}*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception:
                pass

        # In-memory cleanup
        matching = [k for k in self._fallback_store if k.startswith(prefix)]
        for k in matching:
            self._fallback_store.pop(k, None)

    # --- Domain Specific Cache Operations ---

    def get_kpi_summary(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        return self.get(f"nexora:kpi:{tenant_id}")

    def set_kpi_summary(self, tenant_id: str, data: Dict[str, Any], ttl: int = 3600):
        self.set(f"nexora:kpi:{tenant_id}", data, ttl=ttl)

    def get_query_response(self, tenant_id: str, prompt: str) -> Optional[Dict[str, Any]]:
        prompt_hash = self._hash_key(prompt)
        return self.get(f"nexora:query:{tenant_id}:{prompt_hash}")

    def set_query_response(self, tenant_id: str, prompt: str, data: Dict[str, Any], ttl: int = 600):
        prompt_hash = self._hash_key(prompt)
        self.set(f"nexora:query:{tenant_id}:{prompt_hash}", data, ttl=ttl)

    def get_department_metrics(self, tenant_id: str, department: str) -> Optional[List[Dict[str, Any]]]:
        return self.get(f"nexora:dept:{tenant_id}:{department.lower()}")

    def set_department_metrics(self, tenant_id: str, department: str, data: List[Dict[str, Any]], ttl: int = 1800):
        self.set(f"nexora:dept:{tenant_id}:{department.lower()}", data, ttl=ttl)

    def get_job_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.get(f"nexora:job:{job_id}")

    def set_job_state(self, job_id: str, data: Dict[str, Any], ttl: int = 86400):
        self.set(f"nexora:job:{job_id}", data, ttl=ttl)

    def invalidate_tenant_cache(self, tenant_id: str, department: Optional[str] = None):
        """Invalidates KPI summaries, department metrics, and cached queries for the tenant."""
        self.delete(f"nexora:kpi:{tenant_id}")
        if department:
            self.delete(f"nexora:dept:{tenant_id}:{department.lower()}")
        else:
            self.delete_prefix(f"nexora:dept:{tenant_id}:")
        # Invalidate all query caches for this tenant since data has changed
        self.delete_prefix(f"nexora:query:{tenant_id}:")

    def get_cache_stats(self) -> Dict[str, Any]:
        connected = self.is_connected()
        total_ops = self._hits + self._misses
        hit_ratio = round((self._hits / total_ops) * 100, 2) if total_ops > 0 else 0.0

        total_keys = 0
        if connected:
            try:
                keys = self._redis_client.keys("nexora:*")
                total_keys = len(keys)
            except Exception:
                total_keys = len(self._fallback_store)
        else:
            total_keys = len(self._fallback_store)

        return {
            "status": "connected" if connected else "fallback_in_memory",
            "redis_connected": connected,
            "cache_backend": "Redis 7 Server" if connected else "In-Memory LRU/TTL Cache",
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio_percent": hit_ratio,
            "total_cached_keys": total_keys
        }

    def clear_all(self):
        if self.is_connected():
            try:
                keys = self._redis_client.keys("nexora:*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception:
                pass
        self._fallback_store.clear()
        self._hits = 0
        self._misses = 0


cache_manager = EnterpriseCacheManager()
