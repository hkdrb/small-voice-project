from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import os

from backend.database import SessionLocal, User, UserSession, get_db
from backend.security_utils import verify_password_safe, validate_password_strength, hash_pass
import bcrypt


router = APIRouter()

# Security Config
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "False").lower() == "true"


# hash_pass moved to security_utils, but kept here as alias if needed or imported for compat
# Ideally, we should import it from security_utils everywhere.
# For now, let's just make sure we use the one from utils if possible or redundant.
# The previous line replaces the import, so we don't need to redefine it unless it's used locally before import fix.
# Actually, let's just remove the local definition since we imported it.

class LoginRequest(BaseModel):
    username: str # Email in this app
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    must_change_password: bool
    current_org_id: int | None = None
    org_role: str | None = None

@router.post("/login")
def login(login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    # Fetch user for verification
    user = db.query(User).filter(User.email == login_data.username).first()

    # Verify Password Safe (Timing Attack Resistant)
    # If user is None, verify_password_safe handles it safely (using dummy hash if available or random delay).
    if not verify_password_safe(login_data.password, user.password_hash if user else None):
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")
        
    if not user: # Should be caught by verify_password_safe logic returning False, but explicit check for flow
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")

    # Create Session
    session_token = secrets.token_urlsafe(32)
    
    # Session valid for 7 days
    expires_at = datetime.now() + timedelta(days=7)
    
    db_session = UserSession(id=session_token, user_id=user.id, expires_at=expires_at)
    db.add(db_session)
    db.commit()

    # Set Cookie
    response.set_cookie(
        key="small_voice_session",
        value=session_token,
        httponly=True,
        max_age=86400 * 7, # 7 days
        samesite="lax",
        secure=SECURE_COOKIES
    )

    return {
        "message": "ログインに成功しました",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "must_change_password": user.must_change_password
        }
    }

@router.post("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    # Invalidate server-side session if cookie exists
    session_token = request.cookies.get("small_voice_session")
    if session_token:
        db.query(UserSession).filter(UserSession.id == session_token).delete()
        db.commit()

    response.delete_cookie("small_voice_session", httponly=True, samesite="lax", secure=SECURE_COOKIES)
    response.delete_cookie("small_voice_org_context", httponly=True, samesite="lax", secure=SECURE_COOKIES)
    return {"message": "ログアウトしました"}

@router.get("/me", response_model=UserResponse)
def get_current_user(
    small_voice_session: str | None = Cookie(default=None), 
    small_voice_org_context: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not small_voice_session:
        raise HTTPException(status_code=401, detail="認証されていません")
    
    session_record = db.query(UserSession).filter(UserSession.id == small_voice_session).first()
    if not session_record:
        raise HTTPException(status_code=401, detail="無効なセッションです")
    
    # Check Expiration
    if session_record.expires_at and session_record.expires_at < datetime.now():
        # Clean up expired session
        db.delete(session_record)
        db.commit()
        raise HTTPException(status_code=401, detail="セッションの期限が切れました")
        
    user = session_record.user
    if not user:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません")

    # Determine current_org_id and org_role
    current_org_id = None
    org_role = None
    from backend.database import Organization, OrganizationMember
    
    # 1. Try Cookie Context
    if small_voice_org_context:
        try:
             req_org_id = int(small_voice_org_context)
             # Validate membership
             if user.role == 'system_admin':
                 current_org_id = req_org_id
                 org_role = 'admin' # System admin is admin everywhere
             else:
                 mem = db.query(OrganizationMember).filter(
                     OrganizationMember.user_id == user.id,
                     OrganizationMember.organization_id == req_org_id
                 ).first()
                 if mem:
                     current_org_id = req_org_id
                     org_role = mem.role
        except:
            pass
            
    # 2. Fallback if no cookie or invalid
    if not current_org_id:
        if user.role == "system_admin":
            default_org = db.query(Organization).first()
            if default_org:
                current_org_id = default_org.id
                org_role = 'admin'
        else:
            member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
            if member:
                current_org_id = member.organization_id
                org_role = member.role
        
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        must_change_password=user.must_change_password,
        current_org_id=current_org_id,
        org_role=org_role
    )

@router.post("/switch-org")
def switch_org(
    payload: dict,
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_org_id = payload.get("org_id")
    if not target_org_id:
         raise HTTPException(status_code=400, detail="org_idが指定されていません")
         
    # Validate Membership
    from backend.database import OrganizationMember
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.organization_id == target_org_id
    ).first()
    
    if not member and current_user.role != 'system_admin':
         raise HTTPException(status_code=403, detail="この組織のメンバーではありません")
         
    # Set Cookie
    response.set_cookie(
        key="small_voice_org_context",
        value=str(target_org_id),
        httponly=True,
        max_age=86400 * 7,
        samesite="lax",
        secure=SECURE_COOKIES
    )
    
    return {"message": f"組織 {target_org_id} に切り替えました"}


@router.get("/my-orgs")
def get_my_orgs(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from backend.database import Organization, OrganizationMember
    
    if current_user.role == 'system_admin':
        # System Admin sees ALL organizations
        return db.query(Organization).all()
    else:
        # General/Org Admin sees only joined organizations
        return db.query(Organization).join(OrganizationMember).filter(
            OrganizationMember.user_id == current_user.id
        ).all()



class UserUpdate(BaseModel):
    username: str
    password: str | None = None
    current_password: str | None = None

@router.put("/me", response_model=UserResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        
    user.username = update_data.username
    
    if update_data.password and update_data.password.strip():
        # Verify current password
        if not update_data.current_password:
             raise HTTPException(status_code=400, detail="現在のパスワードが必要です")
        if not verify_password_safe(update_data.current_password, user.password_hash):
             raise HTTPException(status_code=400, detail="現在のパスワードが正しくありません")

        # Validate Strength
        is_valid, msg = validate_password_strength(update_data.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"パスワード要件を満たしていません: {msg}")

        # Hash new password
        user.password_hash = hash_pass(update_data.password)
        
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        must_change_password=user.must_change_password,
        current_org_id=current_user.current_org_id,
        org_role=current_user.org_role
    )

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
def reset_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    # Note: datetime imported at top now
    from backend.database import User, UserSession
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Password reset attempt with token: {data.token}")
    
    # Check if token exists at all
    token_user = db.query(User).filter(User.reset_token == data.token).first()
    if not token_user:
        logger.warning(f"No user found with token: {data.token}")
        raise HTTPException(status_code=400, detail="有効期限切れか、無効なトークンです")

    logger.info(f"User found: {token_user.email}, Expiry: {token_user.reset_token_expiry}, Current UTC Time: {datetime.utcnow()}")

    if not token_user.reset_token_expiry or token_user.reset_token_expiry < datetime.utcnow():
        logger.warning(f"Token expired for user {token_user.email}")
        raise HTTPException(status_code=400, detail="有効期限切れか、無効なトークンです")
    
    user = token_user

    # Hash and save new password
    is_valid, msg = validate_password_strength(data.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"パスワード要件を満たしていません: {msg}")

    user.password_hash = hash_pass(data.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    user.must_change_password = False
    
    db.commit()
    return {"message": "パスワードを更新しました"}

@router.post("/request-reset")
def request_reset(payload: dict, db: Session = Depends(get_db)):
    from backend.services.email_service import send_reset_email, generate_reset_token
    # Note: datetime imported at top now
    
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="メールアドレスが必要です")
        
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Generate Token
        token = generate_reset_token()
        expiry = datetime.utcnow() + timedelta(hours=1)
        
        user.reset_token = token
        user.reset_token_expiry = expiry
        db.commit()
        
        # Send Email (Mock)
        send_reset_email(email, token)
        
    # Security: Always return success even if user not found to avoid account enumeration
    return {"message": "リセット手順を送信しました（有効なアドレスの場合）"}
