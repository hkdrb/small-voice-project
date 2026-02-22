from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import json
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import random
import csv
import io
import re
from urllib.parse import quote

from backend.database import SessionLocal, AnalysisSession, AnalysisResult, IssueDefinition, Survey, Comment, CommentLike, Answer, get_db, OrganizationMember, User
from backend.api.auth import get_current_user, UserResponse
from backend.services.notification_service import create_notification, notify_organization_members, notify_organization_admins

router = APIRouter()

def get_issue_info_for_comment(db: Session, comment_id: int) -> Optional[dict]:
    """Finds the issue info associated with a thread by tracing back to the root comment."""
    curr = db.query(Comment).filter(Comment.id == comment_id).first()
    while curr and curr.parent_id:
        curr = db.query(Comment).filter(Comment.id == curr.parent_id).first()
    
    if curr:
        res = {"title": None, "id": None}
        
        # Match by ID tag
        id_match = re.search(r'<!-- issue_id:(.*?) -->', curr.content)
        if id_match:
            res["id"] = id_match.group(1)
            
        # Match by hidden comment tag: <!-- issue:TITLE -->
        title_match = re.search(r'<!-- issue:(.*?) -->', curr.content)
        if title_match:
            res["title"] = title_match.group(1)
        else:
            # Match by visible legacy format: 【議題: TITLE】
            legacy_match = re.search(r'【議題: (.*?)】', curr.content)
            if legacy_match:
                res["title"] = legacy_match.group(1)
        
        if res["title"]:
            return res
    return None

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
    summary: str
    original_text: str
    x: float
    y: float
    cluster_id: Optional[int] = None
    is_noise: Optional[bool] = False

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
                summary=r.summary,
                original_text=r.original_text,
                x=float(r.x_coordinate) if r.x_coordinate is not None else 0.0,
                y=float(r.y_coordinate) if r.y_coordinate is not None else 0.0,
                cluster_id=r.cluster_id,
                is_noise=r.cluster_id == -1 if r.cluster_id is not None else False
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

    if session.is_published:
        notify_organization_members(
            db,
            session.organization_id,
            "report_published",
            "新しいレポート公開",
            f"レポート「{session.title}」が閲覧可能になりました。",
            f"/dashboard?tab=reports",
            exclude_user_id=current_user.id
        )

    return {"message": "Updated publish status", "is_published": session.is_published}

@router.put("/sessions/{session_id}/publish-analysis")
def publish_analysis(
    session_id: int,
    payload: dict,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        
    session.is_comment_analysis_published = payload.get("is_published", False)
    db.commit()

    if session.is_comment_analysis_published:
        notify_organization_members(
            db,
            session.organization_id,
            "report_published",
            "AI分析公開",
            f"レポート「{session.title}」のAI分析結果が公開されました。",
            f"/dashboard/sessions/{session_id}",
            exclude_user_id=current_user.id
        )

    return {"message": "Updated analysis publish status", "is_published": session.is_comment_analysis_published}

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
    # Payload: { survey_id: int, question_id: int, title: str, mock: bool }
    survey_id = payload.get("survey_id")
    question_id = payload.get("question_id")
    title = payload.get("title", "New Analysis")
    is_mock = payload.get("mock", False)
    
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
        from backend.services.mock_generator import generate_mock_analysis_data
        import pandas as pd
        
        # 2. Analyze
        # Determine theme from survey title (Mock or fetch)
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        theme = survey.title if survey else "General"
        
        if is_mock:
            # Mock Analysis
            print(f"Running MOCK analysis for theme: {theme}")
            results, issue_content = generate_mock_analysis_data(theme, num_points=len(texts))
            # Adjust generated mock results to map to actual original texts if possible, 
            # OR just use the generated ones (which implies ignoring actual user input)
            # User request: "Insert test data report". implying we use the test data content.
            # So we will use the results from generator which contain "original_text" from the generator.
        else:
            # Real Analysis
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
                summary=r['summary'],
                x_coordinate=r.get('x_coordinate'),
                y_coordinate=r.get('y_coordinate'),
                cluster_id=r.get('cluster_id')
                # small_voice_score removed
            ))
        
        if issue_content:
            import json
            db.add(IssueDefinition(
                session_id=sess.id, 
                content=json.dumps(issue_content, ensure_ascii=False)
            ))
            
        db.commit()
        
        return {"message": "Analysis completed", "session_id": sess.id}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
    
    # Notify based on publication status
    issue_info = get_issue_info_for_comment(db, new_comment.id)
    url_suffix = ""
    if issue_info:
        title_part = f"title={quote(issue_info['title'])}"
        id_part = f"&issue_id={issue_info['id']}" if issue_info.get('id') else ""
        url_suffix = f"?{title_part}{id_part}"
    
    if session.is_published:
        # Everyone can see it
        notify_organization_members(
            db,
            session.organization_id,
            "chat_new",
            "レポートチャット新着",
            f"レポート「{session.title}」に新しいコメントが投稿されました。",
            f"/dashboard/sessions/{session_id}{url_suffix}",
            exclude_user_id=current_user.id
        )
    else:
        # Only admins can see it
        notify_organization_admins(
            db,
            session.organization_id,
            "chat_new",
            "レポートチャット新着 (未公開)",
            f"未公開レポート「{session.title}」に管理者コメントが投稿されました。",
            f"/dashboard/sessions/{session_id}{url_suffix}",
            exclude_user_id=current_user.id
        )
    
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
    return {"message": "Like updated", "count": count, "liked": liked}

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





class ThreadAnalysisRequest(BaseModel):
    parent_comment_id: int

@router.post("/sessions/{session_id}/analyze-thread")
def analyze_thread(
    session_id: int,
    payload: ThreadAnalysisRequest,
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
        
    # 1. Fetch Comments for Thread
    # Parent
    parent = db.query(Comment).filter(Comment.id == payload.parent_comment_id, Comment.session_id == session_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent comment not found")
        
    # Children
    children = db.query(Comment).filter(Comment.parent_id == payload.parent_comment_id, Comment.session_id == session_id).order_by(Comment.created_at.asc()).all()
    
    # Prepare list for service
    # Combine parent + children sorted by time
    thread_comments = [parent] + children
    
    # Convert to simple objects for service
    formatted_comments = []
    for c in thread_comments:
        name = "匿名" if c.is_anonymous else (c.user.username if c.user else "Unknown")
        formatted_comments.append({
            "content": c.content,
            "user_name": name,
            "created_at": c.created_at
        })
        
    try:
        from backend.services.analysis import analyze_thread_logic
        result = analyze_thread_logic(formatted_comments)
        
        # Update Session JSON
        # Structure: { "threads": { "parent_id": { ...result... } }, ...other_existing_data... }
        current_data = {}
        if session.comment_analysis:
            try:
                current_data = json.loads(session.comment_analysis)
            except:
                current_data = {}
        
        if "threads" not in current_data:
            current_data["threads"] = {}
            
        current_data["threads"][str(payload.parent_comment_id)] = result
        
        session.comment_analysis = json.dumps(current_data, ensure_ascii=False)
        db.commit()
        
        # Notify organization members only if the AI analysis is actually published
        issue_info = get_issue_info_for_comment(db, payload.parent_comment_id)
        url_suffix = ""
        if issue_info:
            title_part = f"title={quote(issue_info['title'])}"
            id_part = f"&issue_id={issue_info['id']}" if issue_info.get('id') else ""
            url_suffix = f"?{title_part}{id_part}"

        if session.is_comment_analysis_published:
            notify_organization_members(
                db,
                session.organization_id,
                "report_published",
                "AI分析更新",
                f"レポート「{session.title}」のAIスレッド分析が更新されました。",
                f"/dashboard/sessions/{session_id}{url_suffix}",
                exclude_user_id=current_user.id
            )
        else:
            # Notify admins even if it's not published to general members
            notify_organization_admins(
                db,
                session.organization_id,
                "report_published",
                "AI分析更新 (未公開)",
                f"レポート「{session.title}」のAIスレッド分析（内部確認用）が更新されました。",
                f"/dashboard/sessions/{session_id}{url_suffix}",
                exclude_user_id=current_user.id
            )
        
        return {"message": "Thread analysis completed", "result": result}
        
    except Exception as e:
        print(f"Thread Analysis error: {e}")
        raise HTTPException(status_code=500, detail="Thread analysis failed")

@router.get("/sessions/{session_id}/issues")
def get_session_issues(
    session_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check access
    if not current_user.current_org_id:
        return []
        
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id,
        AnalysisSession.organization_id == current_user.current_org_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Get Issue Definition
    issue_def = db.query(IssueDefinition).filter(IssueDefinition.session_id == session_id).first()
    if not issue_def or not issue_def.content:
        return []
        
    try:
        issues = json.loads(issue_def.content)
        if isinstance(issues, list):
            return [{"id": issue.get("id"), "title": issue.get("title")} for issue in issues if issue.get("title")]
        return []
    except:
        return []

@router.post("/sessions/{session_id}/comments/import")
def import_session_comments(
    session_id: int,
    issue_title: str = Form(...),
    issue_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. System Admin Only
    if current_user.role != 'system_admin':
         raise HTTPException(status_code=403, detail="System Admin access required")
         
    # 2. Validate Session
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 3. Find or Create System Root for Issue
    hidden_tag = f"<!-- issue:{issue_title} -->"
    id_tag = f"<!-- issue_id:{issue_id} -->" if issue_id else ""
    
    # Check for existing root
    # We look for a comment in this session that is a root (parent_id is None) and contains the tag
    # Priority to issue_id if provided
    root_query = db.query(Comment).filter(
        Comment.session_id == session_id,
        Comment.parent_id == None
    )
    
    if issue_id:
        root_comment = root_query.filter(Comment.content.like(f"%{id_tag}%")).first()
    else:
        root_comment = root_query.filter(Comment.content.like(f"%{hidden_tag}%")).first()
    
    if not root_comment:
        # Create new root
        system_content = f"System Root for Issue: {issue_title}\n\n{id_tag}{hidden_tag} <!-- system_root -->"
        root_comment = Comment(
            session_id=session_id,
            user_id=current_user.id, # System Admin owns the root
            content=system_content,
            is_anonymous=False
        )
        db.add(root_comment)
        db.commit()
        db.refresh(root_comment)
        
    # 4. Get Org Members for Random Assignment
    if not session.organization_id:
         raise HTTPException(status_code=400, detail="Session has no organization")
         
    members = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == session.organization_id
    ).all()
    
    member_user_ids = [m.user_id for m in members]
    if not member_user_ids:
        # Fallback to current user if no members (unlikely)
        member_user_ids = [current_user.id]

    # 5. Process CSV using pandas or csv module. Using csv module for simplicity with Stream
    import pandas as pd
    try:
        content = file.file.read()
        # Auto-detect encoding? Assume utf-8 first
        try:
            df = pd.read_csv(io.BytesIO(content))
        except UnicodeDecodeError:
            # Try Shift-JIS just in case for excel exports
            df = pd.read_csv(io.BytesIO(content), encoding='shift-jis')
            
        if 'content' not in df.columns:
             raise HTTPException(status_code=400, detail="CSV must have 'content' column")
             
        comments_to_add = []
        for _, row in df.iterrows():
            text = str(row['content']).strip()
            if not text or text.lower() == 'nan':
                continue
                
            # Random User
            uid = random.choice(member_user_ids)
            
            # Random Anonymity (50/50 is default? or maybe bias towards one?)
            # User said "Random is fine"
            is_anon = random.choice([True, False])
            
            new_comment = Comment(
                session_id=session_id,
                user_id=uid,
                content=text,
                is_anonymous=is_anon,
                parent_id=root_comment.id
            )
            comments_to_add.append(new_comment)
            
        if comments_to_add:
            db.add_all(comments_to_add)
            db.commit()
            
        return {"message": f"Imported {len(comments_to_add)} comments", "root_id": root_comment.id}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

