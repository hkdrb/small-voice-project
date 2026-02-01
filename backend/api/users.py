from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import string
import logging

from backend.database import get_db, User, Organization, OrganizationMember
from backend.api.auth import get_current_user, UserResponse
from backend.security_utils import hash_pass, validate_password_strength, generate_strong_password
from backend.services.email_service import send_invitation_email, generate_reset_token

router = APIRouter()
logger = logging.getLogger(__name__)

# Models

# ... imports ...

class OrgAssignment(BaseModel):
    org_id: int
    role: str # 'admin' or 'general'

class UserCreate(BaseModel):
    email: str
    username: str
    is_system_admin: bool = False
    org_assignments: List[OrgAssignment] = [] # List of {org_id, role}

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    org_assignments: Optional[List[OrgAssignment]] = None

class UserOrgInfo(BaseModel):
    org_id: int
    name: str
    role: str

class UserListResponse(BaseModel):
    id: int
    email: Optional[str] = ""
    username: Optional[str] = ""
    role: Optional[str] = "system_user"
    organizations: List[UserOrgInfo] = []
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[UserListResponse])
def get_users(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    users = db.query(User).order_by(User.id.desc()).all()
    
    results = []
    for u in users:
        orgs = []
        for mem in u.organization_mappings:
            orgs.append(UserOrgInfo(
                org_id=mem.organization_id,
                name=mem.organization.name,
                role=mem.role
            ))
        
        results.append(UserListResponse(
            id=u.id,
            email=u.email,
            username=u.username,
            role=u.role,
            organizations=orgs
        ))
        
    return results

# generate_random_password removed, use generate_strong_password from security_utils

# ...

@router.post("", response_model=UserListResponse)
def create_user_endpoint(
    user: UserCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    # Validation
    if not user.email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    # Logic: Non-System Admins must join at least one Org
    if not user.is_system_admin and not user.org_assignments:
        raise HTTPException(status_code=400, detail="User must belong to at least one organization")

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
        
    # Generate Password & Token
    pw = generate_strong_password()
    token = generate_reset_token()
    expiry = datetime.now() + timedelta(hours=24)
    fake_hash = hash_pass(pw)
    
    new_user = User(
        email=user.email,
        username=user.username,
        password_hash=fake_hash,
        role="system_admin" if user.is_system_admin else "system_user",
        must_change_password=True,
        reset_token=token,
        reset_token_expiry=expiry
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Assign Orgs - STRICTLY prevent headers for system_admin
    if not user.is_system_admin and user.org_assignments:
        for assignment in user.org_assignments:
            # Verify org exists
            org = db.query(Organization).filter(Organization.id == assignment.org_id).first()
            if org:
                db.add(OrganizationMember(
                    user_id=new_user.id, 
                    organization_id=org.id, 
                    role=assignment.role
                ))
        db.commit()
        
    # Send Invitation
    try:
        success = send_invitation_email(user.email, token)
        if success:
            logger.info(f"Invitation email sent successfully to {user.email}")
        else:
            logger.warning(f"Failed to send invitation email to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send invitation email to {user.email}: {e}")
        # Continue, don't rollback user creation
        
    return new_user

@router.put("/{user_id}", response_model=UserListResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'system_admin':
        raise HTTPException(status_code=403, detail="Permission denied")
        
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
        
    if data.email and data.email != u.email:
         existing = db.query(User).filter(User.email == data.email).first()
         if existing:
             raise HTTPException(status_code=400, detail="Email already exists")
         u.email = data.email
         
    if data.password and data.password.strip():
        # Validate Strength
        is_valid, msg = validate_password_strength(data.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"パスワード要件を満たしていません: {msg}")

        # Hash new password
        fake_hash = hash_pass(data.password)
        u.password_hash = fake_hash
        
    if data.username:
        u.username = data.username
    if data.role:
        u.role = data.role
        
    # Sync Organizations
    # Rule: System Admin (role="system_admin") CANNOT have organization mappings.
    # Logic: 
    # 1. If becoming/staying system_admin -> Clear all mappings.
    # 2. If system_user -> Apply org_assignments (must have at least one if we strictly enforced it, 
    #    but update might just be profile update. However, if unlinking orgs, we should check).
    
    # Check effective role
    effective_role = data.role if data.role else u.role
    
    if effective_role == 'system_admin':
        # Force removal of all memberships
        db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).delete()
    elif data.org_assignments is not None:
        # Delete existing memberships
        db.query(OrganizationMember).filter(OrganizationMember.user_id == user_id).delete()
        # Add new ones
        for assignment in data.org_assignments:
            # Verify org exists
            org = db.query(Organization).filter(Organization.id == assignment.org_id).first()
            if not org:
                raise HTTPException(status_code=400, detail=f"Organization with ID {assignment.org_id} not found.")
            db.add(OrganizationMember(
                user_id=user_id,
                organization_id=assignment.org_id,
                role=assignment.role
            ))
            
    db.commit()
    db.refresh(u)
    
    # Return with orgs
    orgs = []
    # Refresh the user object to load updated organization_mappings
    db.refresh(u) 
    for mem in u.organization_mappings:
        orgs.append(UserOrgInfo(
            org_id=mem.organization_id,
            name=mem.organization.name,
            role=mem.role
        ))
    
    return UserListResponse(
        id=u.id,
        email=u.email,
        username=u.username,
        role=u.role,
        organizations=orgs
    )

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != 'system_admin':
         raise HTTPException(status_code=403, detail="Permission denied")
         
    if current_user.id == user_id:
         raise HTTPException(status_code=400, detail="Cannot delete your own account")
         
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
         raise HTTPException(status_code=404, detail="User not found")
         
    db.delete(u)
    db.commit()
    return {"message": "User deleted"}
