import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.api.policies import router as policies_router
from app.db.session import engine, Base
from app.core.policy_cache import poll_policies
from app.core.middleware import RateLimitMiddleware

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    poller_task = asyncio.create_task(poll_policies())
    # Give the poller 1 second to load the initial Postgres data into the cache
    await asyncio.sleep(1)
    yield
    poller_task.cancel()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Add our custom Rate Limiter Middleware
app.add_middleware(RateLimitMiddleware)

# Register our endpoints
app.include_router(policies_router)

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

# This is the fake backend endpoint our Rate Limiter is protecting
@app.get("/api/data")
async def get_secure_data():
    return {"message": "You successfully bypassed the rate limiter!", "data": [1, 2, 3]}