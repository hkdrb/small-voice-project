import sys
import os
import random
import hashlib
from datetime import datetime
import secrets

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, User, Comment, AnalysisSession, AnalysisResult, IssueDefinition, Organization, OrganizationMember, init_db
from backend.security_utils import hash_pass
from backend.services.mock_generator import (
    generate_mock_analysis_data,
    get_comment_generator,
    get_small_voice_comment,
    get_dense_cluster_comment,
    get_value_comment_q3
)

DATA_GENERATOR_AVAILABLE = True

def create_dummy_users(db, num_users=10):
    print(f"--- Creating/Verifying {num_users} Standard Users (user1..{num_users}) ---")
    created_count = 0
    users = []
    
    # Ensure Default Org exists (should be done by init_db but safety first)
    default_org = db.query(Organization).filter(Organization.name == "株式会社サンプル").first()
    if not default_org:
        print("⚠️ 株式会社サンプル not found. Creating...")
        default_org = Organization(name="株式会社サンプル", description="Default")
        db.add(default_org)
        db.commit()

    for i in range(1, num_users + 1):
        email = f"user{i}@example.com"
        username = f"ユーザー{i}"
        
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            # Get password from env or generate strong random
            user_pw = os.getenv("INITIAL_USER_PASSWORD")
            if not user_pw:
                from backend.security_utils import generate_strong_password
                user_pw = generate_strong_password()
                print(f"  Note: Generated random password for {email}: {user_pw}")

            new_user = User(
                email=email,
                username=username,
                password_hash=hash_pass(user_pw),
                role="user",
                must_change_password=True
            )
            db.add(new_user)
            db.commit()
            
            # Assign to Org
            db.add(OrganizationMember(user_id=new_user.id, organization_id=default_org.id, role="general"))
            db.commit()
            
            users.append(new_user)
            created_count += 1
            print(f"Created: {email}")
        else:
            users.append(existing)
            # Ensure org membership
            member = db.query(OrganizationMember).filter(OrganizationMember.user_id == existing.id, OrganizationMember.organization_id == default_org.id).first()
            if not member:
                 db.add(OrganizationMember(user_id=existing.id, organization_id=default_org.id, role="general"))
                 db.commit()
    
    db.commit()
    print(f"Prepared {len(users)} users.")
    return users

def create_dummy_sessions(db):
    print("\n--- Creating Dummy Analysis Sessions ---")
    
    default_org = db.query(Organization).filter(Organization.name == "株式会社サンプル").first()
    if not default_org:
        print("⚠️ Default Org not found. Skipping session creation.")
        return []

    sessions_data = [
        {"title": "業務プロセス改善について", "theme": "project"},
        {"title": "新製品のフィードバック", "theme": "product"},
        {"title": "開発環境のアンケート結果", "theme": "dev_env"},
        {"title": "技術品質と負債について", "theme": "tech_quality"},
        {"title": "企業価値観(Values)についての対話", "theme": "value"}
    ]
    
    created_sessions = []
    for s_data in sessions_data:
        existing = db.query(AnalysisSession).filter(
            AnalysisSession.title == s_data["title"],
            AnalysisSession.organization_id == default_org.id
        ).first()
        
        if not existing:
            new_session = AnalysisSession(
                title=s_data["title"],
                theme=s_data["theme"],
                organization_id=default_org.id,
                is_published=True,
                created_at=datetime.now()
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session) # Get ID
            
            # --- Generate Mock Analysis Data ---
            # Note: We only use the report (IssueDefinition) part now.
            # AnalysisResults (points) are skipped to avoid mismatch with comments.
            print(f"  Generating mock report for {new_session.title}...")
            _, issue_content = generate_mock_analysis_data(new_session.theme, num_points=80)
            
            # Add Report Only
            db.add(IssueDefinition(session_id=new_session.id, content=issue_content))
            db.commit()
            
            created_sessions.append(new_session)
            print(f"Created Session & Report (No mock points): {new_session.title} ({new_session.theme})")
        else:
            created_sessions.append(existing)
            
    print(f"Prepared {len(created_sessions)} sessions.")
    return created_sessions

def create_dummy_comments(db, users, num_comments=200):
    print(f"\n--- Checking Sessions for Comment Generation ---")
    
    sessions = db.query(AnalysisSession).all()
    if not sessions:
        print("ℹ️ No Analysis Sessions provided. Skipping comment generation.")
        return

    total_created = 0

    for session in sessions:
        theme_text = (str(session.theme) + " " + str(session.title)).lower()
        
        # Map session to generator category
        category = "project" # default
        
        if any(w in theme_text for w in ["営業", "sales", "project", "プロジェクト"]):
            category = "project"
        elif any(w in theme_text for w in ["製品", "product", "プロダクト"]):
            category = "product"
        elif any(w in theme_text for w in ["福利厚生", "welfare", "dev_env", "開発環境"]):
            category = "welfare" # Maps to dev_env/welfare in generator
        elif any(w in theme_text for w in ["技術", "tech", "quality", "tech_quality"]):
            category = "tech"
        elif any(w in theme_text for w in ["価値観", "values", "value"]):
            category = "values"

        # Get the generator function for this category
        generator_func = get_comment_generator(category)

        print(f"Processing Session: ID={session.id} '{session.title}' -> Category: {category}")

        session_created_count = 0
        
        # Distribution Strategy:
        # 5% Small Voices (Outliers)
        # 85% Dense Clusters (Clear signals)
        # 10% General Noise (Combinatorial sentences)
        
        n_small_voices = max(2, int(num_comments * 0.05))
        n_dense_clusters = int(num_comments * 0.85) # Increased to 85% for clearer signals
        n_general = num_comments - n_small_voices - n_dense_clusters
        
        comments_payload = []
        
        # 1. ADD SMALL VOICES
        for _ in range(n_small_voices):
            content = get_small_voice_comment(category)
            comments_payload.append(content)
            
        # 2. ADD DENSE CLUSTERS
        for _ in range(n_dense_clusters):
            content = get_dense_cluster_comment(category)
            comments_payload.append(content)
            
        # 3. ADD GENERAL NOISE
        for _ in range(n_general):
            content = generator_func()
            comments_payload.append(content)
            
        # Shuffle to mix them up
        random.shuffle(comments_payload)
        
        for content in comments_payload:
            user = random.choice(users)
            is_anonymous = random.choice([True, False, False])

            # Rich text and variation logic
            enrich_type = random.choice(['bold', 'list', 'quote', 'mixed', 'none'])
            final_content = content
            
            if enrich_type == 'bold':
                if random.random() < 0.5:
                     final_content = f"**{content}**"
            elif enrich_type == 'list':
                 final_content = f"{content}\n\n- 要点1\n- 要点2"
            
            comment = Comment(
                session_id=session.id,
                user_id=user.id,
                content=final_content,
                is_anonymous=is_anonymous,
                created_at=datetime.now()
            )
            db.add(comment)
            db.commit()
            session_created_count += 1
            total_created += 1

        print(f"  -> Added {session_created_count} comments (incl. {n_small_voices} Small Voices).")

    print(f"✅ Successfully created total {total_created} comments.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed the database with initial users and optional dummy data.")
    parser.add_argument("--init-users", action="store_true", help="Create or verify initial dummy users.")
    parser.add_argument("--seed-sessions", action="store_true", help="Create dummy analysis sessions.")
    parser.add_argument("--seed-comments", action="store_true", help="Add dummy comments to EXISTING sessions.")
    parser.add_argument("--with-dummy-data", action="store_true", help="(Legacy) Run all seeds (users, sessions, comments).")
    
    args = parser.parse_args()

    init_db() # Ensure tables exist
    db = SessionLocal()
    
    try:
        # 1. Users
        users = []
        if args.init_users or args.with_dummy_data:
            users = create_dummy_users(db, num_users=10)
        
        # If we need to seed comments but didn't init users, fetch them
        if (args.seed_comments) and not users:
            users = db.query(User).filter(User.email.like("user%@example.com")).all()
            if not users:
                print("⚠️ No dummy users found. Generating them automatically to proceed with comments...")
                users = create_dummy_users(db, num_users=10)

        # 2. Sessions
        if args.seed_sessions or args.with_dummy_data:
            create_dummy_sessions(db)
            
        # 3. Comments (Existing sessions only)
        if args.seed_comments or args.with_dummy_data:
            if not users:
                 # Should be covered above, but safety check
                 print("❌ No users available to author comments.")
            else:
                 create_dummy_comments(db, users, num_comments=200)

        if not (args.init_users or args.seed_sessions or args.seed_comments or args.with_dummy_data):
            print("\nℹ️  No actions selected. Use flags:")
            print("  --init-users     : Create users")
            print("  --seed-sessions  : Create session containers")
            print("  --seed-comments  : Add comments to sessions")
            print("  --with-dummy-data: Run all")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()
