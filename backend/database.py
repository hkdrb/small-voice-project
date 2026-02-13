import uuid
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timedelta, timezone
JST = timezone(timedelta(hours=9))
def now_jst():
    """Returns the current JST time as a naive datetime object for DB consistency."""
    return datetime.now(JST).replace(tzinfo=None)
import secrets
import bcrypt
import os
import logging
from dotenv import load_dotenv

from pathlib import Path

# Load .env from project root (parent of backend directory)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Logger setup
logger = logging.getLogger("uvicorn")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///voice_insight.db")

if "sqlite" in DATABASE_URL:
    logger.warning("----------------------------------------------------------------")
    logger.warning("⚠️  WARNING: Using SQLite database. NOT RECOMMENDED FOR PRODUCTION.")
    logger.warning("   Please set DATABASE_URL environment variable.")
    logger.warning("----------------------------------------------------------------")

Base = declarative_base()

connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

from sqlalchemy import event
if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ユーザー管理 ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True) # 以前の username (初期ログインID)
    username = Column(String, default="") # 以前の name (表示名)
    password_hash = Column(String)
    role = Column(String)

    # address removed per user request
    must_change_password = Column(Boolean, default=False) # 初回パスワード変更強制フラグ
    reset_token = Column(String, nullable=True, index=True) # パスワードリセット用トークン
    reset_token_expiry = Column(DateTime, nullable=True) # トークン有効期限
    comments = relationship("Comment", back_populates="user")
    answers = relationship("Answer", back_populates="user", cascade="all, delete-orphan")
    
    # Organization mappings
    organization_mappings = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    
    # Likes
    likes = relationship("CommentLike", back_populates="user", cascade="all, delete-orphan")
    
    # Sessions
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    created_surveys = relationship("Survey", back_populates="creator")
    survey_comments = relationship("SurveyComment", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: secrets.token_urlsafe(32))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=now_jst)
    expires_at = Column(DateTime)
    
    user = relationship("User", back_populates="sessions")


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now_jst)
    
    members = relationship("OrganizationMember", back_populates="organization")
    surveys = relationship("Survey", back_populates="organization", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="organization", cascade="all, delete-orphan")

class OrganizationMember(Base):
    __tablename__ = "organization_members"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(String, default="general") # admin, general (Organization Level Role)
    joined_at = Column(DateTime, default=now_jst)
    
    user = relationship("User", back_populates="organization_mappings")
    organization = relationship("Organization", back_populates="members")

# --- アンケート機能 (New) ---
class Survey(Base):
    """アンケートフォーム定義"""
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4())) # URL用ID
    title = Column(String)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True) # 公開/非公開
    created_at = Column(DateTime, default=now_jst)
    updated_at = Column(DateTime, default=now_jst, onupdate=now_jst)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True) # Link to Org
    
    # New columns for Request feature
    source = Column(String, default="manual") # manual, request, csv
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # New columns for Approval Flow
    approval_status = Column(String, default="pending") # pending, approved, rejected
    rejection_reason = Column(Text, nullable=True) # Reason for rejection
    
    questions = relationship("Question", back_populates="survey", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="survey", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="surveys")
    creator = relationship("User", back_populates="created_surveys")
    comments = relationship("SurveyComment", back_populates="survey", cascade="all, delete-orphan")

class Question(Base):
    """アンケートの設問"""
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    text = Column(String) # 質問文
    order = Column(Integer) # 表示順
    is_required = Column(Boolean, default=True) # 必須かどうか
    
    survey = relationship("Survey", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

class Answer(Base):
    """ユーザーの回答データ"""
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # ゲスト回答可能に
    content = Column(Text) # 回答内容
    created_at = Column(DateTime, default=now_jst)
    
    survey = relationship("Survey", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    user = relationship("User", back_populates="answers")

# --- 分析レポート (既存) ---
class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    theme = Column(String)
    created_at = Column(DateTime, default=now_jst)
    is_published = Column(Boolean, default=False)
    comment_analysis = Column(Text, nullable=True)
    is_comment_analysis_published = Column(Boolean, default=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True) # Link to Org
    
    results = relationship("AnalysisResult", back_populates="session", cascade="all, delete-orphan")
    report = relationship("IssueDefinition", back_populates="session", uselist=False, cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="session", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="analysis_sessions")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id"))
    original_text = Column(Text)
    sub_topic = Column(String)
    # sentiment removed
    summary = Column(String)
    x_coordinate = Column(Float, nullable=True)
    y_coordinate = Column(Float, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    # small_voice_score removed
    session = relationship("AnalysisSession", back_populates="results")

class IssueDefinition(Base):
    __tablename__ = "issue_definitions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id"))
    content = Column(Text)
    session = relationship("AnalysisSession", back_populates="report")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now_jst)
    session = relationship("AnalysisSession", back_populates="comments")
    user = relationship("User", back_populates="comments")
    
    # 階層構造（リプライ）
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan", uselist=True)
    parent = relationship("Comment", back_populates="replies", remote_side=[id])
    
    # 更新日時（編集機能用）
    updated_at = Column(DateTime, nullable=True)
    
    # いいね機能
    likes = relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")

class CommentLike(Base):
    __tablename__ = "comment_likes"
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=now_jst)
    
    comment = relationship("Comment", back_populates="likes")
    user = relationship("User")

# --- 雑談掲示板 (Casual Chat / Daily Thoughts) ---
class CasualPost(Base):
    """みんなの雑談掲示板の投稿"""
    __tablename__ = "casual_posts"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True) # ユーザー削除後も残す
    parent_id = Column(Integer, ForeignKey("casual_posts.id"), nullable=True)  # 返信機能用
    content = Column(Text)
    created_at = Column(DateTime, default=now_jst)
    likes_count = Column(Integer, default=0) # Simple counter for now, or relationship if needed
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
    likes = relationship("CasualPostLike", back_populates="post", cascade="all, delete-orphan")
    children = relationship("CasualPost", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("CasualPost", back_populates="children", remote_side=[id])

class CasualPostLike(Base):
    """雑談投稿へのいいね"""
    __tablename__ = "casual_post_likes"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("casual_posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=now_jst)
    
    post = relationship("CasualPost", back_populates="likes")
    user = relationship("User")

class CasualAnalysis(Base):
    """雑談からの分析・推奨レポート"""
    __tablename__ = "casual_analyses"
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=now_jst)
    
    # Analysis Scope
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Content (JSON)
    # Expected format: { "recommendations": [ { "title": "...", "reason": "...", "suggested_questions": [...] } ] }
    result_json = Column(Text)
    
    is_published = Column(Boolean, default=False) # 公開/非公開
    
    organization = relationship("Organization")

class SurveyComment(Base):
    """申請フォーム上のチャットコメント"""
    __tablename__ = "survey_comments"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=now_jst)
    
    survey = relationship("Survey", back_populates="comments")
    user = relationship("User", back_populates="survey_comments")

class Notification(Base):
    """通知管理"""
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    type = Column(String) # survey_released, report_published, casual_suggestion, chat_new, form_rejected, form_applied
    title = Column(String)
    content = Column(Text)
    link = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(JST))

    user = relationship("User", back_populates="notifications")
    organization = relationship("Organization")

# --- 初期化 ---
def init_db():
    Base.metadata.create_all(bind=engine)
    # DBマイグレーション (削除: Alembicへ移行のため手動マイグレーションロジックを廃止)
    # 以前のPRAGMA table_infoやALTER TABLE文は削除されました。
    # スキーマ変更は alembic upgrade head を使用してください。

    db = SessionLocal()
    
    # ユーザー作成 (テーブル更新後のカラム名で処理)
    # ユーザー作成・初期データ投入

    # 1. System Admin
    system_emails = ["system@example.com", "system2@example.com", "system3@example.com", "system4@example.com", "system5@example.com"]
    sys_password = os.getenv("INITIAL_SYSTEM_PASSWORD", "SystemAdmin1234!")
    
    for email in system_emails:
        if not db.query(User).filter(User.email == email).first():
            sys_user = User(
                email=email, 
                username=f"システム管理者 ({email.split('@')[0]})", 
                password_hash=bcrypt.hashpw(sys_password.encode(), bcrypt.gensalt()).decode(), 
                role="system_admin",
                must_change_password=True
            )
            db.add(sys_user)
    db.commit()

    # 2. Default Organization
    default_org = db.query(Organization).filter(Organization.name == "株式会社サンプル").first()
    if not default_org:
        default_org = Organization(name="株式会社サンプル", description="初期作成された組織")
        db.add(default_org)
        db.commit()
    
    # 3. Organization Admin (for Default Org)
    org_admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not org_admin:
        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "OrgAdmin1234!")

        org_admin = User(
            email="admin@example.com", 
            username="組織管理者", 
            password_hash=bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode(), 
            role="system_user", # System context: system_user
            must_change_password=True
        )
        db.add(org_admin)
        db.commit()
        # Assign as Admin to Default Org
        db.add(OrganizationMember(user_id=org_admin.id, organization_id=default_org.id, role="admin"))
        db.commit()

    # 4. General Users (10 users) - requested as initial state
    # Checking for the first one to avoid duplicate runs
    if not db.query(User).filter(User.email == "user1@example.com").first():
        for i in range(1, 11):
            email = f"user{i}@example.com"
            user_password = os.getenv("INITIAL_USER_PASSWORD", "GeneralUser1234!")

            gen_user = User(
                email=email,
                username=f"ユーザー{i}",
                password_hash=bcrypt.hashpw(user_password.encode(), bcrypt.gensalt()).decode(),
                role="system_user", # System context: system_user
                must_change_password=True
            )
            db.add(gen_user)
            db.commit() # Commit to get ID
            
            # Assign as General to Default Org
            db.add(OrganizationMember(user_id=gen_user.id, organization_id=default_org.id, role="general"))
        db.commit()

    
    db.close()