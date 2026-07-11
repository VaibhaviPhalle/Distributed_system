from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import TenantPolicy
from app.schemas.policy import PolicyCreate, PolicyResponse, PolicyBase
from app.api.dependencies import verify_admin_key

# Apply the admin key dependency to all routes in this router
router = APIRouter(
    prefix="/policies",
    tags=["Policies"],
    dependencies=[Depends(verify_admin_key)]
)

@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(policy: PolicyCreate, db: Session = Depends(get_db)):
    db_policy = db.query(TenantPolicy).filter(TenantPolicy.tenant_id == policy.tenant_id).first()
    if db_policy:
        raise HTTPException(status_code=400, detail="Policy already exists for this tenant")
    
    new_policy = TenantPolicy(**policy.model_dump())
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return new_policy

@router.get("/{tenant_id}", response_model=PolicyResponse)
def get_policy(tenant_id: str, db: Session = Depends(get_db)):
    db_policy = db.query(TenantPolicy).filter(TenantPolicy.tenant_id == tenant_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return db_policy

@router.put("/{tenant_id}", response_model=PolicyResponse)
def update_policy(tenant_id: str, policy: PolicyBase, db: Session = Depends(get_db)):
    db_policy = db.query(TenantPolicy).filter(TenantPolicy.tenant_id == tenant_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    for key, value in policy.model_dump().items():
        setattr(db_policy, key, value)
        
    db.commit()
    db.refresh(db_policy)
    return db_policy