from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import json

from backend.database import get_db, CasualPost, CasualPostLike, CasualAnalysis, OrganizationMember, Organization
from backend.api.auth import get_current_user, UserResponse
from backend.services.analysis import analyze_casual_posts_logic

router = APIRouter()

# Pydantic Models
class CasualPostCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None  # 返信先の投稿ID

class CasualPostResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_name: Optional[str]
    likes_count: int
    is_liked_by_me: bool
    parent_id: Optional[int] = None
    replies_count: int = 0

class AnalysisResponse(BaseModel):
    id: int
    created_at: datetime
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_published: bool
    result: dict

class AnalysisVisibilityUpdate(BaseModel):
    is_published: bool

# Endpoints
@router.post("/posts", response_model=CasualPostResponse)
def create_post(
    post_data: CasualPostCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        raise HTTPException(status_code=400, detail="組織に参加していません")

    # If parent_id is provided, verify it exists
    if post_data.parent_id:
        parent_post = db.query(CasualPost).filter(CasualPost.id == post_data.parent_id).first()
        if not parent_post:
            raise HTTPException(status_code=404, detail="返信先の投稿が見つかりません")

    post = CasualPost(
        organization_id=current_user.current_org_id,
        user_id=current_user.id,
        content=post_data.content,
        parent_id=post_data.parent_id
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return {
        "id": post.id,
        "content": post.content,
        "created_at": post.created_at,
        "user_name": current_user.username,
        "likes_count": 0,
        "is_liked_by_me": False,
        "parent_id": post.parent_id,
        "replies_count": 0
    }

@router.get("/posts", response_model=List[CasualPostResponse])
def get_posts(
    skip: int = 0,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        raise HTTPException(status_code=400, detail="組織に参加していません")

    # Get all posts (including replies) for the organization
    posts = db.query(CasualPost).filter(
        CasualPost.organization_id == current_user.current_org_id
    ).order_by(CasualPost.created_at.desc()).offset(skip).limit(limit).all()
    
    # Check likes
    post_ids = [p.id for p in posts]
    my_likes = db.query(CasualPostLike).filter(
        CasualPostLike.user_id == current_user.id,
        CasualPostLike.post_id.in_(post_ids)
    ).all()
    liked_post_ids = {like.post_id for like in my_likes}

    # Count replies for each post
    from sqlalchemy import func
    replies_count_query = db.query(
        CasualPost.parent_id,
        func.count(CasualPost.id).label('count')
    ).filter(
        CasualPost.parent_id.in_(post_ids)
    ).group_by(CasualPost.parent_id).all()
    
    replies_count_map = {parent_id: count for parent_id, count in replies_count_query}

    results = []
    for post in posts:
        results.append({
            "id": post.id,
            "content": post.content,
            "created_at": post.created_at,
            "user_name": post.user.username if post.user else "Unknown",
            "likes_count": post.likes_count,
            "is_liked_by_me": post.id in liked_post_ids,
            "parent_id": post.parent_id,
            "replies_count": replies_count_map.get(post.id, 0)
        })
    return results

@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(CasualPost).filter(CasualPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="投稿が見つかりません")
        
    # Check if liked
    existing_like = db.query(CasualPostLike).filter(
        CasualPostLike.post_id == post_id,
        CasualPostLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        is_liked = False
    else:
        new_like = CasualPostLike(post_id=post_id, user_id=current_user.id)
        db.add(new_like)
        post.likes_count += 1
        is_liked = True
        
    db.commit()
    return {"liked": is_liked, "likes_count": post.likes_count}

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_posts(
    start_date: str = None,
    end_date: str = None,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only Admin (Org admin or System admin)
    if not current_user.current_org_id:
        raise HTTPException(status_code=400, detail="組織が選択されていません")

    is_admin = current_user.org_role == 'admin' or current_user.role == 'system_admin'
    if not is_admin:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")

    org = db.query(Organization).filter(Organization.id == current_user.current_org_id).first()
    
    # Parse dates
    from datetime import datetime as dt
    if start_date:
        start_dt = dt.fromisoformat(start_date)
    else:
        # Default: 30 days ago
        start_dt = datetime.now() - timedelta(days=30)
    
    if end_date:
        end_dt = dt.fromisoformat(end_date)
        # Set to end of day
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
    else:
        # Default: now
        end_dt = datetime.now()
    
    # 1. Fetch posts
    posts = db.query(CasualPost).filter(
        CasualPost.organization_id == current_user.current_org_id,
        CasualPost.created_at >= start_dt,
        CasualPost.created_at <= end_dt
    ).all()
    
    if not posts:
        return {
            "id": 0, # Dummy ID
            "created_at": datetime.now(),
            "start_date": start_dt,
            "end_date": end_dt,
            "is_published": False,
            "result": {"recommendations": [], "message": "期間内の投稿がありません"}
        }

    # 2. Analyze
    result_data = analyze_casual_posts_logic(posts, org_name=org.name if org else "")
    
    # 3. Save
    analysis = CasualAnalysis(
        organization_id=current_user.current_org_id,
        start_date=start_dt,
        end_date=end_dt,
        result_json=json.dumps(result_data, ensure_ascii=False),
        is_published=False 
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return {
        "id": analysis.id,
        "created_at": analysis.created_at,
        "start_date": analysis.start_date,
        "end_date": analysis.end_date,
        "is_published": analysis.is_published,
        "result": result_data
    }

@router.get("/analyses", response_model=List[AnalysisResponse])
def get_analyses(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        raise HTTPException(status_code=400, detail="組織に参加していません")

    # If Admin, show all. If Member, show only published.
    is_admin = current_user.org_role == 'admin' or current_user.role == 'system_admin'
    
    query = db.query(CasualAnalysis).filter(
        CasualAnalysis.organization_id == current_user.current_org_id
    )
    
    if not is_admin:
        query = query.filter(CasualAnalysis.is_published == True)
        
    analyses = query.order_by(CasualAnalysis.created_at.desc()).all()
    
    results = []
    for a in analyses:
        try:
            res_content = json.loads(a.result_json)
        except:
            res_content = {}
            
        results.append({
            "id": a.id,
            "created_at": a.created_at,
            "start_date": a.start_date,
            "end_date": a.end_date,
            "is_published": a.is_published,
            "result": res_content
        })
    return results

@router.patch("/analyses/{analysis_id}/visibility")
def update_visibility(
    analysis_id: int,
    update: AnalysisVisibilityUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
         raise HTTPException(status_code=400, detail="組織コンテキストが必要です")
         
    is_admin = current_user.org_role == 'admin' or current_user.role == 'system_admin'
    if not is_admin:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
        
    analysis = db.query(CasualAnalysis).filter(
        CasualAnalysis.id == analysis_id,
        CasualAnalysis.organization_id == current_user.current_org_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="分析レポートが見つかりません")
        
    analysis.is_published = update.is_published
    db.commit()
    
    return {"id": analysis.id, "is_published": analysis.is_published}

@router.delete("/analyses/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
         raise HTTPException(status_code=400, detail="組織コンテキストが必要です")
         
    is_admin = current_user.org_role == 'admin' or current_user.role == 'system_admin'
    if not is_admin:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
        
    analysis = db.query(CasualAnalysis).filter(
        CasualAnalysis.id == analysis_id,
        CasualAnalysis.organization_id == current_user.current_org_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="分析レポートが見つかりません")
        
    db.delete(analysis)
    db.commit()
    
    return {"message": "分析レポートを削除しました"}
