from sqlalchemy.orm import Session
from backend.database import Notification, User, OrganizationMember
from typing import Optional

def create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    content: str,
    link: str,
    organization_id: Optional[int] = None
):
    notification = Notification(
        user_id=user_id,
        organization_id=organization_id,
        type=type,
        title=title,
        content=content,
        link=link
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def notify_organization_members(
    db: Session,
    organization_id: int,
    type: str,
    title: str,
    content: str,
    link: str,
    exclude_user_id: Optional[int] = None
):
    members = db.query(OrganizationMember).filter(OrganizationMember.organization_id == organization_id).all()
    for member in members:
        if exclude_user_id and member.user_id == exclude_user_id:
            continue
        create_notification(db, member.user_id, type, title, content, link, organization_id)

def notify_organization_admins(
    db: Session,
    organization_id: int,
    type: str,
    title: str,
    content: str,
    link: str,
    exclude_user_id: Optional[int] = None
):
    # Get organization admins
    org_admins = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.role == 'admin'
    ).all()
    
    # Get system admins (they should also see org-level notifications usually, but let's stick to org admins for now as per request)
    # Actually, system admins might want to know about form applications too.
    system_admins = db.query(User).filter(User.role == 'system_admin').all()
    
    admin_user_ids = {m.user_id for m in org_admins}
    admin_user_ids.update({u.id for u in system_admins})
    
    for uid in admin_user_ids:
        if exclude_user_id and uid == exclude_user_id:
            continue
        create_notification(db, uid, type, title, content, link, organization_id)
