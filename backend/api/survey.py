from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
JST = timezone(timedelta(hours=9))
def now_jst():
    return datetime.now(JST).replace(tzinfo=None)
import csv
import io

from backend.database import SessionLocal, Survey, Question, Answer, User, OrganizationMember, SurveyComment, get_db
from backend.api.auth import get_current_user, UserResponse
from backend.services.notification_service import create_notification, notify_organization_admins, notify_organization_members

router = APIRouter()

# --- Pydantic Models ---

class QuestionBase(BaseModel):
    text: str
    is_required: bool
    order: int

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    
    class Config:
        from_attributes = True

class SurveyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[QuestionCreate]

class SurveyResponse(BaseModel):
    id: int
    uuid: str
    title: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    questions: List[QuestionResponse] = []
    has_answered: bool = False
    
    class Config:
        from_attributes = True

class AnswerSubmit(BaseModel):
    question_id: int
    content: str

class SurveySubmit(BaseModel):
    answers: List[AnswerSubmit]

class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Endpoints ---

@router.post("", response_model=SurveyResponse)
def create_survey(
    survey_data: SurveyCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        raise HTTPException(status_code=403, detail="No organization context")

    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    
    new_survey = Survey(
        title=survey_data.title,
        description=survey_data.description,
        created_by=current_user.id,
        organization_id=current_user.current_org_id,
        is_active=False, # Default to inactive/draft
        source="manual" if is_admin else "request",
        approval_status="approved" if is_admin else "pending"
    )
    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)
    
    for q in survey_data.questions:
        new_q = Question(
            survey_id=new_survey.id,
            text=q.text,
            is_required=q.is_required,
            order=q.order
        )
        db.add(new_q)
    
    db.commit()
    db.refresh(new_survey)
    
    # Notify Admins if it's a request
    if new_survey.source == "request":
        notify_organization_admins(
            db, 
            new_survey.organization_id,
            "form_applied",
            "新規フォーム申請",
            f"「{new_survey.title}」の申請が届きました。",
            f"/dashboard?tab=surveys",
            exclude_user_id=current_user.id
        )

    return new_survey

@router.get("/{survey_id}", response_model=SurveyResponse)
def get_survey(
    survey_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    survey = db.query(Survey).options(joinedload(Survey.questions)).filter(
        Survey.id == survey_id,
        Survey.organization_id == current_user.current_org_id
    ).first()
    
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    return survey

    # Check Org Membership
    if survey.organization_id:
        member = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.organization_id == survey.organization_id
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
            
    # Check if user has answered
    has_answered = db.query(Answer).filter(
        Answer.survey_id == survey.id,
        Answer.user_id == current_user.id
    ).first() is not None
    
    survey.has_answered = has_answered
    
    return survey

@router.post("/{survey_id}/response")
def submit_response(
    survey_id: int,
    submission: SurveySubmit,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify access again
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    if survey.organization_id:
         member = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.organization_id == survey.organization_id
        ).first()
         if not member:
             raise HTTPException(status_code=403, detail="Access denied")

    # 1. Fetch existing answers
    existing_answers = db.query(Answer).filter(
        Answer.survey_id == survey.id,
        Answer.user_id == current_user.id
    ).all()
    
    if existing_answers:
         raise HTTPException(status_code=400, detail="回答済みです。重複回答はできません。")

    existing_map = {a.question_id: a for a in existing_answers}
    
    # 2. Process submission
    for ans in submission.answers:
        if not ans.content.strip():
            continue
            
        if ans.question_id in existing_map:
            existing_map[ans.question_id].content = ans.content
        else:
            new_ans = Answer(
                survey_id=survey.id,
                question_id=ans.question_id,
                user_id=current_user.id,
                content=ans.content
            )
            db.add(new_ans)
            
    db.commit()
    return {"message": "Response submitted successfully"}
@router.post("/import")
def import_csv(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    selected_columns: str = Form(None), # Comma-separated list of column names
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.current_org_id:
        raise HTTPException(status_code=403, detail="No organization context")
        
    import pandas as pd
    import io
    
    try:
        contents = file.file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Filter columns if selected_columns is provided
        if selected_columns:
            target_cols = [c.strip() for c in selected_columns.split(',') if c.strip()]
            # Validate columns exist
            target_cols = [c for c in target_cols if c in df.columns]
            if not target_cols:
                 raise HTTPException(status_code=400, detail="No valid columns selected")
        else:
            target_cols = df.columns.tolist()
        
        # 1. Create Survey
        new_survey = Survey(
            title=title,
            description=description or f"Imported from {file.filename}",
            created_by=current_user.id,
            organization_id=current_user.current_org_id,
            is_active=False,
            source="csv",
            approval_status="approved"
        )
        db.add(new_survey)
        db.commit()
        db.refresh(new_survey)
        
        # 2. Questions & Answers
        questions = []
        for i, col in enumerate(target_cols):
            q = Question(
                survey_id=new_survey.id,
                text=col,
                order=i + 1,
                is_required=False
            )
            db.add(q)
            db.commit()
            db.refresh(q)
            questions.append(q)
            
            # Answers
            col_data = df[col].dropna().astype(str).tolist()
            answers = [
                Answer(
                    survey_id=new_survey.id,
                    question_id=q.id,
                    user_id=None,
                    content=val
                ) for val in col_data if val.strip()
            ]
            db.add_all(answers)
            
        db.commit()
        return {"message": "Import successful", "survey_id": new_survey.id}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/{survey_id}/responses/csv")
def get_survey_responses_csv(
    survey_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Permission check: Admin only
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 2. Get Survey and Questions
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    questions = db.query(Question).filter(Question.survey_id == survey_id).order_by(Question.order).all()
    q_ids = [q.id for q in questions]

    # 3. Get Answers (joined with User)
    answers = db.query(Answer).options(joinedload(Answer.user)).filter(
        Answer.survey_id == survey_id
    ).all()

    # 4. Group by User
    # Since each user can only have one set of answers for a survey, we group by user_id.
    from collections import defaultdict
    user_responses = defaultdict(lambda: {"user_info": {"username": "ゲスト", "email": "-"}, "answers": {}})

    for ans in answers:
        user_id = ans.user_id if ans.user_id is not None else f"guest_{ans.id}" # Handle nulls if any
        if ans.user:
            user_responses[user_id]["user_info"] = {
                "username": ans.user.username or ans.user.email,
                "email": ans.user.email
            }
        
        user_responses[user_id]["answers"][ans.question_id] = ans.content
        if "created_at" not in user_responses[user_id] or ans.created_at > user_responses[user_id]["created_at"]:
            user_responses[user_id]["created_at"] = ans.created_at

    # 5. Generate CSV
    output = io.StringIO()
    output.write('\ufeff') # BOM for Excel
    writer = csv.writer(output)

    # Header
    header = ["回答日時", "ユーザー名", "メールアドレス"]
    for q in questions:
        header.append(f"[{q.order}] {q.text}")
    writer.writerow(header)

    # Data Rows (sorted by created_at)
    sorted_items = sorted(user_responses.values(), key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    for data in sorted_items:
        row = [
            data.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if "created_at" in data else "-",
            data["user_info"]["username"],
            data["user_info"]["email"]
        ]
        for q_id in q_ids:
            row.append(data["answers"].get(q_id, ""))
        writer.writerow(row)

    output.seek(0)
    filename = f"survey_responses_{survey_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.put("/{survey_id}", response_model=SurveyResponse)
def update_survey(
    survey_id: int,
    data: SurveyCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    # Permission check: Admin or Creator
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin and survey.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Non-admins can only edit pending or rejected surveys
    if not is_admin and survey.approval_status not in ['pending', 'rejected']:
        raise HTTPException(status_code=403, detail="Cannot edit published surveys")
        
    # Update basics
    survey.title = data.title
    survey.description = data.description
    
    # Reset status if it's a request by a non-admin
    if not is_admin and survey.source == 'request':
        survey.approval_status = 'pending'
        survey.is_active = False # Require re-approval
        survey.rejection_reason = None

    # Sync Questions
    # 1. Check for existing answers first to prevent data loss
    existing_answers_count = db.query(Answer).filter(Answer.survey_id == survey_id).count()

    if existing_answers_count > 0:
        # Check if questions have changed
        existing_questions = db.query(Question).filter(Question.survey_id == survey_id).order_by(Question.order).all()
        
        # Simple comparison: count, text, order, is_required
        questions_changed = False
        if len(existing_questions) != len(data.questions):
            questions_changed = True
        else:
            for eq, nq in zip(existing_questions, data.questions):
                if (eq.text != nq.text or 
                    eq.is_required != nq.is_required): 
                    questions_changed = True
                    break
        
        if questions_changed:
            raise HTTPException(
                status_code=400, 
                detail="このアンケートには既に回答が存在するため、質問の構成を変更できません。新しいアンケートを作成してください。"
            )
        else:
            # Questions identical, skip delete/insert logic to preserve answer links
            pass
    else:
        # No answers, safe to delete and recreate
        # 1. Delete old
        existing_questions = db.query(Question).filter(Question.survey_id == survey_id).all()
        for q in existing_questions:
            db.delete(q)
        
        # 2. Add new
        for idx, q_data in enumerate(data.questions):
            db.add(Question(
                survey_id=survey.id,
                text=q_data.text,
                is_required=q_data.is_required,
                order=idx + 1
            ))
        
    db.commit()
    db.refresh(survey)

    # Notify admins when a user updates (re-applies) a survey
    if not is_admin and survey.source == 'request':
        notify_organization_admins(
            db,
            survey.organization_id,
            "form_applied",
            "フォーム再申請",
            f"「{survey.title}」が再編集・再申請されました。",
            f"/dashboard?tab=surveys",
            exclude_user_id=current_user.id
        )

    return survey

@router.delete("/{survey_id}")
def delete_survey(
    survey_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Permission: Admin or Creator
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if not is_admin and survey.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Non-admins can only delete pending surveys
    if not is_admin and survey.approval_status != 'pending':
        raise HTTPException(status_code=403, detail="Cannot delete published or rejected surveys")
        
    db.delete(survey)
    db.commit()
    return {"message": "Survey deleted"}

@router.patch("/{survey_id}/toggle")
def toggle_survey_status(
    survey_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Permission: Admin only
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    survey.is_active = not survey.is_active
    
    # 公開にした場合は承認済みとする
    if survey.is_active:
        survey.approval_status = "approved"
        
    db.commit()

    # Notify members if it became active
    if survey.is_active:
        notify_organization_members(
            db,
            survey.organization_id,
            "survey_released",
            "新しいアンケート公開",
            f"アンケート「{survey.title}」が公開されました。",
            f"/dashboard?tab=answers",
            exclude_user_id=current_user.id
        )

    return {"message": "Toggled status", "is_active": survey.is_active}

@router.put("/{survey_id}/approve")
def approve_survey(
    survey_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Permission: Admin only
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    survey.approval_status = "approved"
    survey.is_active = False # Default to stopped after approval
    
    db.commit()

    # Notify creator on approval
    if survey.created_by:
        create_notification(
            db,
            survey.created_by,
            "form_approved",
            "フォーム申請承認",
            f"申請したフォーム「{survey.title}」が承認されました。",
            f"/dashboard?tab=requests",
            organization_id=survey.organization_id
        )

    return {"message": "Survey approved", "approval_status": survey.approval_status}

@router.put("/{survey_id}/reject")
def reject_survey(
    survey_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Permission: Admin only
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    survey.approval_status = "rejected"
    # survey.rejection_reason = reason # Removed per user request
    survey.is_active = False # Ensures it is treated as "Stopped" and hidden from general users
    
    db.commit()
    
    # Notify creator
    if survey.created_by:
        create_notification(
            db,
            survey.created_by,
            "form_rejected",
            "フォーム申請却下",
            f"申請したフォーム「{survey.title}」が却下されました。",
            f"/dashboard?tab=requests",
            organization_id=survey.organization_id
        )

    return {"message": "Survey rejected", "approval_status": survey.approval_status}

@router.get("/{survey_id}/comments", response_model=List[CommentResponse])
def get_survey_comments(
    survey_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    # Permission check: Admin or Creator
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin and survey.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    comments = db.query(SurveyComment).options(joinedload(SurveyComment.user)).filter(
        SurveyComment.survey_id == survey_id
    ).order_by(SurveyComment.created_at).all()
    
    return [
        CommentResponse(
            id=c.id,
            content=c.content,
            user_id=c.user_id,
            username=c.user.username or c.user.email if c.user else "Unknown",
            created_at=c.created_at
        ) for c in comments
    ]

@router.post("/{survey_id}/comments", response_model=CommentResponse)
def create_survey_comment(
    survey_id: int,
    comment: CommentCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    # Permission check: Admin or Creator
    is_admin = current_user.role in ['admin', 'system_admin'] or current_user.org_role == 'admin'
    if not is_admin and survey.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
        
    new_comment = SurveyComment(
        survey_id=survey_id,
        user_id=current_user.id,
        content=comment.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment, attribute_names=['user'])
    
    # Notify the other party
    if is_admin:
        # If admin commented, notify the creator
        if survey.created_by and survey.created_by != current_user.id:
            create_notification(
                db,
                survey.created_by,
                "chat_new",
                "フォームチャット新着",
                f"フォーム「{survey.title}」に関する新しいチャット通知があります。",
                f"/dashboard?tab=requests",
                organization_id=survey.organization_id
            )
    else:
        # If user commented, notify admins
        notify_organization_admins(
            db,
            survey.organization_id,
            "chat_new",
            "フォームチャット新着",
            f"フォーム「{survey.title}」に関する新しいチャット通知があります。",
            f"/dashboard?tab=surveys",
            exclude_user_id=current_user.id
        )

    return CommentResponse(
        id=new_comment.id,
        content=new_comment.content,
        user_id=new_comment.user_id,
        username=current_user.username or current_user.email,
        created_at=new_comment.created_at
    )
