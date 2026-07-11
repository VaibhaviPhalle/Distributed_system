import asyncio
from app.db.session import SessionLocal
from app.db.models import TenantPolicy

# This dict acts as our fast, in-memory cache
POLICY_CACHE = {}

async def poll_policies():
    """Background task that syncs Postgres data into memory every 60s."""
    while True:
        db = SessionLocal()
        try:
            policies = db.query(TenantPolicy).all()
            new_cache = {
                p.tenant_id: {
                    "limit": p.limit, 
                    "window_seconds": p.window_seconds
                } for p in policies
            }
            POLICY_CACHE.clear()
            POLICY_CACHE.update(new_cache)
        except Exception as e:
            print(f"Error polling policies: {e}")
        finally:
            db.close()
        
        # Wait 60 seconds before polling again
        await asyncio.sleep(60)