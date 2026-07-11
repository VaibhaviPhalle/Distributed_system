from sqlalchemy import Column, String, Integer
from app.db.session import Base

class TenantPolicy(Base):
    __tablename__ = "tenant_policies"

    tenant_id = Column(String, primary_key=True, index=True)
    limit = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    burst_allowance = Column(Integer, default=0)