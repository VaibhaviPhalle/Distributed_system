import time
import uuid
import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Connection pool setup
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Pre-load Lua scripts into Redis memory for fast execution
with open("app/redis/scripts/check_global_bucket.lua", "r") as f:
    global_script = redis_client.register_script(f.read())

with open("app/redis/scripts/check_tenant_window.lua", "r") as f:
    tenant_script = redis_client.register_script(f.read())

def check_global_limit(capacity: int, refill_rate: int) -> tuple[bool, int, int]:
    """Returns (allowed, remaining_tokens, reset_seconds)"""
    try:
        now = int(time.time())
        result = global_script(
            keys=["ratelimit:global:bucket"],
            args=[capacity, refill_rate, now]
        )
        return bool(result[0]), int(result[1]), int(result[2])
    except redis.RedisError as e:
        logger.error(f"Redis failure in global check: {e}")
        # Apply Failure Strategy
        if settings.RATE_LIMITER_FAILURE_STRATEGY == "fail-open":
            return True, 0, 0
        return False, 0, 0

def check_tenant_limit(tenant_id: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
    """Returns (allowed, remaining, reset_seconds)"""
    try:
        now = int(time.time())
        req_id = str(uuid.uuid4())
        result = tenant_script(
            keys=[f"ratelimit:tenant:{tenant_id}:window"],
            args=[limit, window_seconds, now, req_id]
        )
        return bool(result[0]), int(result[1]), int(result[2])
    except redis.RedisError as e:
        logger.error(f"Redis failure in tenant check: {e}")
        # Apply Failure Strategy
        if settings.RATE_LIMITER_FAILURE_STRATEGY == "fail-open":
            return True, 0, 0
        return False, 0, 0