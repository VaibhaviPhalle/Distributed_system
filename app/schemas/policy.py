from pydantic import BaseModel

class PolicyBase(BaseModel):
    limit: int
    window_seconds: int
    burst_allowance: int = 0

class PolicyCreate(PolicyBase):
    tenant_id: str

class PolicyResponse(PolicyBase):
    tenant_id: str

    class Config:
        from_attributes = True