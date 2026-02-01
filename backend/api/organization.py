from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import get_db, Organization, OrganizationMember
from backend.api.auth import get_current_user, UserResponse

router = APIRouter()

# Models
class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    id: int
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class MemberResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str # org-specific role

# Endpoints

@router.get("", response_model=List[OrganizationResponse])
def get_organizations(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only System Admin can see all orgs (or maybe authenticated users need list for joining?)
    # Streamlit logic: System Admin sees all in management tab.
    # For now, restriction to System Admin for management list.
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    orgs = db.query(Organization).order_by(Organization.id.desc()).all()
    return orgs

@router.post("", response_model=OrganizationResponse)
def create_organization(
    org: OrganizationCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check unique name
    existing = db.query(Organization).filter(Organization.name == org.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization name already exists")
        
    new_org = Organization(name=org.name, description=org.description)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    org_update: OrganizationUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    org_obj = db.query(Organization).filter(Organization.id == org_id).first()
    if not org_obj:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Check unique name if changing
    if org_update.name != org_obj.name:
        existing = db.query(Organization).filter(Organization.name == org_update.name).first()
        if existing:
             raise HTTPException(status_code=400, detail="Organization name already exists")
             
    org_obj.name = org_update.name
    org_obj.description = org_update.description
    db.commit()
    db.refresh(org_obj)
    return org_obj

@router.delete("/{org_id}")
def delete_organization(
    org_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    org_obj = db.query(Organization).filter(Organization.id == org_id).first()
    if not org_obj:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check for members
    member_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).count()
    if member_count > 0:
        raise HTTPException(
            status_code=400, 
            detail="所属メンバーが存在するため、この組織を削除することはできません。すべてのメンバーを解除してから再度実行してください。"
        )
        
    db.delete(org_obj)
    db.commit()
    return {"message": "Organization deleted"}

@router.get("/{org_id}/members", response_model=List[MemberResponse])
def get_organization_members(
    org_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user belongs to this org or is system admin
    is_system_admin = current_user.role == 'system_admin'
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id
    ).first()
    
    if not is_system_admin and not membership:
        raise HTTPException(status_code=403, detail="Access denied to this organization")
        
    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).order_by(OrganizationMember.id.desc()).all()
    
    results = []
    for m in members:
        results.append(MemberResponse(
            id=m.user.id,
            username=m.user.username,
            email=m.user.email,
            role=m.role
        ))
    return results
