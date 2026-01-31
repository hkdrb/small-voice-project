from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.database import SessionLocal, AnalysisSession, AnalysisResult, IssueDefinition, Survey, Comment, CommentLike, Answer, get_db
from backend.api.auth import get_current_user, UserResponse

router = APIRouter()

# --- Pydantic Models for Response ---
class SessionSummary(BaseModel):
    id: int
    title: str
    theme: str
    is_published: bool
    created_at: datetime
    
class SurveySummary(BaseModel):
    id: int
    title: str
    uuid: str
    is_active: bool
    approval_status: str # pending, approved, rejected
    rejection_reason: Optional[str] = None
    created_by: Optional[int]
    description: Optional[str]

class PublishRequest(BaseModel):
    is_published: bool

class AnalysisResultItem(BaseModel):
    sub_topic: str
    sentiment: float
    summary: str
    original_text: str
    x: float
    y: float
    y: float

class CommentItem(BaseModel):
    id: int
    content: str
    user_id: Optional[int]
    user_name: str
    is_anonymous: bool
    created_at: datetime
    likes_count: int
    parent_id: Optional[int]

class SessionDetail(BaseModel):
    id: int
    title: str
    theme: str
    is_published: bool
    report_content: Optional[str] = None
    results: List[AnalysisResultItem] = []
    comments: List[CommentItem] = []
    comment_analysis: Optional[str] = None
    is_comment_analysis_published: bool = False

@router.get("/sessions", response_model=List[SessionSummary])
def get_sessions(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        return []
        
    query = db.query(AnalysisSession).filter(
        AnalysisSession.organization_id == current_user.current_org_id
    )
    
    # Filter for non-admins (System Admin or Organization Admin)
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
        query = query.filter(AnalysisSession.is_published == True)
        
    sessions = query.order_by(AnalysisSession.id.desc()).all()
    
    return [
        SessionSummary(
            id=s.id, 
            title=s.title, 
            theme=s.theme, 
            is_published=s.is_published, 
            created_at=s.created_at
        ) for s in sessions
    ]

@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session_detail(
    session_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        raise HTTPException(status_code=403, detail="No organization context")

    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.organization_id == current_user.current_org_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Check permissions
    is_admin = current_user.role in ["admin", "system_admin"] or current_user.org_role == "admin"
    if not is_admin and not session.is_published:
         raise HTTPException(status_code=403, detail="Permission denied")

    issue_def = db.query(IssueDefinition).filter(IssueDefinition.session_id == session_id).first()
    results = db.query(AnalysisResult).filter(AnalysisResult.session_id == session_id).order_by(AnalysisResult.id.desc()).all()
    
    # Comments logic
    comments_query = db.query(Comment).options(joinedload(Comment.user), joinedload(Comment.likes)).filter(Comment.session_id == session_id).order_by(Comment.id.desc()).all()
    
    comment_items = []
    for c in comments_query:
        name = "匿名" if c.is_anonymous else (c.user.username if c.user and c.user.username else c.user.email if c.user else "Unknown")
        comment_items.append(CommentItem(
            id=c.id,
            content=c.content,
            user_id=c.user_id,
            user_name=name,
            is_anonymous=c.is_anonymous,
            created_at=c.created_at,
            likes_count=len(c.likes),
            parent_id=c.parent_id
        ))

    # Privacy logic for comment analysis
    comment_analysis_visible = is_admin or session.is_comment_analysis_published

    return SessionDetail(
        id=session.id,
        title=session.title,
        theme=session.theme,
        is_published=session.is_published,
        report_content=issue_def.content if issue_def else None,
        results=[
            AnalysisResultItem(
                sub_topic=r.sub_topic,
                sentiment=r.sentiment,
                summary=r.summary,
                original_text=r.original_text,
                x=float(r.x_coordinate) if r.x_coordinate is not None else 0.0,
                y=float(r.y_coordinate) if r.y_coordinate is not None else 0.0
            ) for r in results
        ],
        comments=comment_items,
        comment_analysis=session.comment_analysis if comment_analysis_visible else None,
        is_comment_analysis_published=session.is_comment_analysis_published
    )

@router.put("/sessions/{session_id}/publish")
def publish_session(
    session_id: int,
    payload: dict,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only Admin
    # Only Admin
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
         raise HTTPException(status_code=403, detail="Permission denied")
         
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.organization_id == current_user.current_org_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.is_published = payload.get("is_published", False)
    db.commit()
    return {"message": "Updated publish status", "is_published": session.is_published}

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only Admin
    # Only Admin
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
         raise HTTPException(status_code=403, detail="Permission denied")
         
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.organization_id == current_user.current_org_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}

@router.post("/sessions/analyze")
def run_analysis_endpoint(
    payload: dict,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Payload: { survey_id: int, question_id: int, title: str }
    survey_id = payload.get("survey_id")
    question_id = payload.get("question_id")
    title = payload.get("title", "New Analysis")
    
    if not survey_id or not question_id:
        raise HTTPException(status_code=400, detail="Missing survey_id or question_id")
    
    # 1. Fetch Answers
    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    texts = [a.content for a in answers if a.content and a.content.strip()]
    timestamps = [a.created_at for a in answers if a.content and a.content.strip()]
    
    if not texts or len(texts) < 2:
        raise HTTPException(status_code=400, detail="分析には最低2件の回答が必要です。")
        
    try:
        from backend.services.analysis import analyze_clusters_logic, generate_issue_logic_from_clusters
        import pandas as pd
        
        # 2. Analyze
        # Determine theme from survey title (Mock or fetch)
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        theme = survey.title if survey else "General"
        
        results = analyze_clusters_logic(texts, theme, timestamps=timestamps)
        if not results:
             raise HTTPException(status_code=500, detail="Analysis failed to produce results")
             
        df = pd.DataFrame(results)
        issue_content = generate_issue_logic_from_clusters(df, theme)
        
        # 3. Save
        sess = AnalysisSession(
            title=title, 
            theme=theme, 
            organization_id=current_user.current_org_id,
            is_published=False
        )
        db.add(sess)
        db.commit()
        db.refresh(sess)
        
        for r in results:
            db.add(AnalysisResult(
                session_id=sess.id, 
                original_text=r['original_text'], 
                sub_topic=r['sub_topic'], 
                sentiment=r['sentiment'], 
                summary=r['summary'],
                x_coordinate=r.get('x_coordinate'),
                y_coordinate=r.get('y_coordinate'),
                cluster_id=r.get('cluster_id')
            ))
        
        db.add(IssueDefinition(session_id=sess.id, content=issue_content))
        db.commit()
        
        return {"message": "Analysis completed", "session_id": sess.id}
        
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/surveys", response_model=List[SurveySummary])
def get_surveys(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        return []
        
    query = db.query(Survey).filter(
        Survey.organization_id == current_user.current_org_id
    )
    
    # 権限によるフィルタリング
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Survey.is_active == True,
                (Survey.created_by == current_user.id) & (Survey.approval_status.in_(['pending', 'rejected', 'approved']))
            )
        )
        
    surveys = query.order_by(Survey.id.desc()).all()
    
    return [
        SurveySummary(
            id=s.id, title=s.title, uuid=s.uuid, is_active=s.is_active, 
            approval_status=s.approval_status or 'pending',
            rejection_reason=s.rejection_reason,
            created_by=s.created_by, description=s.description
        ) for s in surveys
    ]

class CreateCommentRequest(BaseModel):
    content: str
    is_anonymous: bool = False
    parent_id: Optional[int] = None

@router.post("/sessions/{session_id}/comments")
def create_comment(
    session_id: int,
    payload: CreateCommentRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify Session exists and user has access (org check)
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.organization_id == current_user.current_org_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Verify Parent if exists
    if payload.parent_id:
        parent = db.query(Comment).filter(
            Comment.id == payload.parent_id,
            Comment.session_id == session_id
        ).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent comment not found")
            
    new_comment = Comment(
        session_id=session_id,
        user_id=current_user.id,
        content=payload.content,
        is_anonymous=payload.is_anonymous,
        parent_id=payload.parent_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {"message": "Comment created", "id": new_comment.id}

@router.post("/comments/{comment_id}/like")
def like_comment(
    comment_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    # Check if already liked
    existing_like = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        db.delete(existing_like)
        liked = False
    else:
        new_like = CommentLike(comment_id=comment_id, user_id=current_user.id)
        db.add(new_like)
        liked = True
        
    db.commit()
    
    # Return new count
    count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
@router.put("/comments/{comment_id}")
def update_comment(
    comment_id: int,
    payload: CreateCommentRequest, # Re-using for content validation
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    # Check ownership
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
        
    comment.content = payload.content
    db.commit()
    
    return {"message": "Comment updated"}



@router.post("/sessions/{session_id}/analyze-comments")
def analyze_session_comments(
    session_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only Admin (System or Org)
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
         raise HTTPException(status_code=403, detail="Permission denied")
         
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.organization_id == current_user.current_org_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    comments = db.query(Comment).filter(Comment.session_id == session_id).all()
    texts = [c.content for c in comments if c.content and c.content.strip()]
    
    if not texts:
        raise HTTPException(status_code=400, detail="No comments to analyze")
        
    try:
        from backend.services.analysis import analyze_comments_logic
        analysis_result = analyze_comments_logic(texts)
        
        session.comment_analysis = analysis_result
        session.is_comment_analysis_published = False # Default to private
        db.commit()
        
        return {"message": "Analysis completed", "result": analysis_result}
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@router.put("/sessions/{session_id}/publish-comments")
def publish_comments(
    session_id: int,
    request: PublishRequest, 
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
         raise HTTPException(status_code=403, detail="Permission denied")
         
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.organization_id == current_user.current_org_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.is_comment_analysis_published = request.is_published
    db.commit()
    return {"message": "Publication status updated", "is_published": session.is_comment_analysis_published}
