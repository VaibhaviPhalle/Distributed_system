import json
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.redis.client import check_global_limit, check_tenant_limit
from app.core.policy_cache import POLICY_CACHE
from app.core.logger import logger

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/policies") or request.url.path == "/healthz":
            return await call_next(request)

        # Start OpenTelemetry-ready timing
        start_time = time.perf_counter()

        tenant_id = request.headers.get("X-API-Key")
        if not tenant_id or tenant_id not in POLICY_CACHE:
            return Response(
                content=json.dumps({"error": "unauthorized", "detail": "Missing or unknown X-API-Key"}),
                status_code=401,
                media_type="application/json"
            )

        policy = POLICY_CACHE[tenant_id]

        # Layer 1: Global Check
        global_capacity = 1000
        global_refill_rate = 100
        global_allowed, global_rem, global_reset = check_global_limit(global_capacity, global_refill_rate)

        if not global_allowed:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("Rate limit exceeded", extra={"telemetry": {
                "tenant_id": tenant_id, "decision": "denied", "scope": "global", "latency_ms": round(latency_ms, 2)
            }})
            return Response(
                content=json.dumps({"error": "rate_limit_exceeded", "scope": "global", "retry_after_seconds": global_reset}),
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(global_capacity), "X-RateLimit-Remaining": str(global_rem),
                    "X-RateLimit-Reset": str(global_reset), "X-RateLimit-Scope": "global", "Retry-After": str(global_reset)
                },
                media_type="application/json"
            )

        # Layer 2: Per-Tenant Check
        tenant_allowed, tenant_rem, tenant_reset = check_tenant_limit(
            tenant_id=tenant_id, limit=policy["limit"], window_seconds=policy["window_seconds"]
        )

        if not tenant_allowed:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("Rate limit exceeded", extra={"telemetry": {
                "tenant_id": tenant_id, "decision": "denied", "scope": "tenant", "latency_ms": round(latency_ms, 2)
            }})
            return Response(
                content=json.dumps({"error": "rate_limit_exceeded", "scope": "tenant", "retry_after_seconds": tenant_reset}),
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(policy["limit"]), "X-RateLimit-Remaining": str(tenant_rem),
                    "X-RateLimit-Reset": str(tenant_reset), "X-RateLimit-Scope": "tenant", "Retry-After": str(tenant_reset)
                },
                media_type="application/json"
            )

        # Success Flow
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(policy["limit"])
        response.headers["X-RateLimit-Remaining"] = str(tenant_rem)
        response.headers["X-RateLimit-Reset"] = str(tenant_reset)
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info("Request allowed", extra={"telemetry": {
            "tenant_id": tenant_id, "decision": "allowed", "scope": "none", "latency_ms": round(latency_ms, 2)
        }})
        
        return response