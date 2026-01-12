import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import hashlib
from datetime import datetime
from backend.database import SessionLocal, User, Comment, AnalysisSession, Organization, OrganizationMember, init_db
from backend.security_utils import hash_pass
import sys
import os
import secrets

# --- Dummy Data Pools (Imported to avoid duplication) ---
try:
    from generate_test_data import (
        get_project_comment,
        get_dev_env_comment,
        get_tech_quality_comment,
        get_value_comment_q3
    )
    
    # Generate data using the new combinatorial functions
    PROPOSAL_COMMENTS_SALES = [get_project_comment() for _ in range(50)]
    PROPOSAL_COMMENTS_PRODUCT = [get_tech_quality_comment() for _ in range(50)]
    PROPOSAL_COMMENTS_WELFARE = [get_dev_env_comment() for _ in range(50)]
    PROPOSAL_COMMENTS_THEME = [get_project_comment() for _ in range(50)]
    PROPOSAL_COMMENTS_VALUES = [get_value_comment_q3() for _ in range(50)]

    PROPOSAL_COMMENTS = (
        PROPOSAL_COMMENTS_SALES +
        PROPOSAL_COMMENTS_PRODUCT +
        PROPOSAL_COMMENTS_WELFARE +
        PROPOSAL_COMMENTS_THEME +
        PROPOSAL_COMMENTS_VALUES
    )
except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback if generate_test_data.py is missing or structure changed
    print("⚠️  Could not import from generate_test_data.py. Using fallback simple list.")
    PROPOSAL_COMMENTS = [
        "業務効率化のための新しいツール導入を検討すべきです。",
        "コミュニケーション不足解消のため、定例ミーティングを見直しましょう。",
        "顧客からのフィードバックを製品開発にもっと迅速に反映させる仕組みが必要です。",
        "リモートワークの手当を充実させることで、社員の満足度が向上すると思います。",
        "若手社員の教育プログラムを強化し、早期戦力化を図るべきです。"
    ]

# hash_pass imported from security_utils

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
                # If for some reason env is missing, generate a random strong one
                # Note: This might make it hard to login if not logged, but better than "user1234"
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
            db.commit() # Get ID
            
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
                 print(f"  -> Linked {email} to Default Org")
            
    # print(f"Exists: {email}")
            
    db.commit()
    print(f"Prepared {len(users)} users.")
    return users

def create_dummy_sessions(db):
    print("\n--- Creating Dummy Analysis Sessions ---")
    
    # Ensure Default Org exists
    default_org = db.query(Organization).filter(Organization.name == "株式会社サンプル").first()
    if not default_org:
        print("⚠️ Default Org not found (unexpected). Skipping session creation.")
        return []

    sessions_data = [
        {"title": "業務プロセス改善について", "theme": "project"},
        {"title": "新製品のフィードバック", "theme": "product"},
        {"title": "開発環境のアンケート結果", "theme": "dev_env"},
        {"title": "オフィス環境に関する意見", "theme": "theme"},
        {"title": "企業価値観(Values)についての対話", "theme": "values"}
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
            created_sessions.append(new_session)
            print(f"Created Session: {new_session.title} ({new_session.theme})")
        else:
            created_sessions.append(existing)
            
    print(f"Prepared {len(created_sessions)} sessions.")
    return created_sessions

def create_dummy_comments(db, users, num_comments=50):
    print(f"\n--- Checking Sessions for Comment Generation ---")
    
    # 1. Get ALL Analysis Sessions
    sessions = db.query(AnalysisSession).all()
    
    if not sessions:
        print("ℹ️ No Analysis Sessions provided. Skipping comment generation.")
        return

    total_created = 0

    for session in sessions:
        # Check Theme/Title to decide which pool to use
        theme_text = (str(session.theme) + " " + str(session.title)).lower()
        
        pool = []
        if any(w in theme_text for w in ["営業", "sales", "project", "プロジェクト"]):
            pool = PROPOSAL_COMMENTS_SALES
            print(f"Processing Session: ID={session.id} '{session.title}' -> Using SALES(Project) data")
        elif any(w in theme_text for w in ["製品", "product", "プロダクト"]):
            pool = PROPOSAL_COMMENTS_PRODUCT
            print(f"Processing Session: ID={session.id} '{session.title}' -> Using PRODUCT data")
        elif any(w in theme_text for w in ["福利厚生", "welfare", "dev_env", "開発環境"]):
            pool = PROPOSAL_COMMENTS_WELFARE
            print(f"Processing Session: ID={session.id} '{session.title}' -> Using WELFARE(DevEnv) data")
        elif any(w in theme_text for w in ["組織", "theme", "office", "オフィス"]):
            pool = PROPOSAL_COMMENTS_THEME
            print(f"Processing Session: ID={session.id} '{session.title}' -> Using THEME/OFFICE data")
        elif any(w in theme_text for w in ["価値観", "values"]):
            pool = PROPOSAL_COMMENTS_VALUES
            print(f"Processing Session: ID={session.id} '{session.title}' -> Using VALUES data")
        elif any(w in theme_text for w in ["技術", "tech", "quality", "tech_quality"]):
            pool = PROPOSAL_COMMENTS_PRODUCT # Reuse product/tech quality comments
            print(f"Processing Session: ID={session.id} '{session.title}' -> Using TECH/PRODUCT data")
        else:
            print(f"⏩ Skipping Session ID={session.id} '{session.title}' (Theme: '{session.theme}') - No matching test data category.")
            continue
        
        if not pool:
            continue

        session_created_count = 0
        
        for _ in range(num_comments):
            user = random.choice(users)
            content = random.choice(pool)
            is_anonymous = random.choice([True, False, False]) # 1/3 anon
            
            # Add slight variation and Rich Text (Markdown) randomly
            if random.random() > 0.5:
                content = f"{content} ({random.randint(1, 100)})"
            
            # Apply Markdown enrichment to showcase Rich Text Editor
            if random.random() < 0.4: # 40% chance of rich text
                enrich_type = random.choice(['bold', 'list', 'quote', 'mixed'])
                
                if enrich_type == 'bold':
                    # Bold the whole sentence or part
                    if random.random() < 0.5:
                        content = f"**{content}**"
                    else:
                        content = content.replace("。", "。**重要**")
                
                elif enrich_type == 'list':
                    # Append a list
                    items = ["コスト削減", "効率化", "品質向上", "リスク管理"]
                    selected_items = random.sample(items, 2)
                    list_md = "\n".join([f"- {item}" for item in selected_items])
                    content = f"{content}\n\n具体的なメリット:\n{list_md}"
                    
                elif enrich_type == 'quote':
                    content = f"> 以前の提案: {content}\n\nこれについて再考しました。"
                
                elif enrich_type == 'mixed':
                    content = f"### 提案の概要\n{content}\n\n**詳細:**\n1. 現状の課題\n2. 解決策\n3. スケジュール"

            comment = Comment(
                session_id=session.id,
                user_id=user.id,
                content=content,
                is_anonymous=is_anonymous,
                created_at=datetime.now()
            )
            db.add(comment)
            db.commit() # Commit to get ID
            session_created_count += 1
            total_created += 1
            
            # 30% chance to add a reply
            if random.random() < 0.3:
                reply_user = random.choice(users)
                
                # Randomize reply sentiment
                reply_type = random.choice(['positive', 'neutral', 'negative'])
                
                if reply_type == 'positive':
                    reply_pool = [
                        "良いアイデアですね！", "賛成です。", "素晴らしい視点です。", "私も同感です。", 
                        "まさにその通りだと思います。", "前向きに進めたいですね。"
                    ]
                elif reply_type == 'neutral':
                    reply_pool = [
                        "実現可能性はどうでしょうか？", "もっと具体的に詰めていきたいですね。", 
                        "一理あると思います。", "詳しい背景を教えてください。", 
                        "他の選択肢も検討すべきかもしれません。", "数字で根拠が出せると良さそうです。"
                    ]
                else: # negative
                    reply_pool = [
                        "少し時期尚早かもしれません。", "コスト面での懸念があります。", 
                        "現場の負担が増えそうです。", "慎重に検討すべき課題ですね。", 
                        "既存のプロセスと競合する恐れがあります。", "優先順位を見直す必要がありそうです。"
                    ]

                reply_content = random.choice(reply_pool)
                
                reply = Comment(
                    session_id=session.id,
                    user_id=reply_user.id,
                    content=reply_content,
                    is_anonymous=random.choice([True, False]),
                    parent_id=comment.id,
                    created_at=datetime.now()
                )
                db.add(reply)
                db.commit()
                session_created_count += 1
                total_created += 1
        
        print(f"  -> Added {session_created_count} comments.")

    print(f"✅ Successfully created total {total_created} comments.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed the database with initial users and optional dummy data.")
    parser.add_argument("--with-dummy-data", action="store_true", help="Also generate dummy sessions and comments.")
    args = parser.parse_args()

    init_db() # Ensure tables exist
    db = SessionLocal()
    try:
        # Always ensure users/orgs exist (Base Infrastructure)
        users = create_dummy_users(db, num_users=10)
        
        # Only create heavy dummy data if requested
        if args.with_dummy_data:
            all_dummy_users = db.query(User).filter(User.email.like("user%@example.com")).all()
            if not all_dummy_users:
                print("❌ No dummy users found (unexpected).")
            else:
                # Skip dummy session creation as per user request
                # existing_session_count = db.query(AnalysisSession).count()
                # if existing_session_count == 0:
                #     create_dummy_sessions(db)
                
                create_dummy_comments(db, all_dummy_users, num_comments=50)
        else:
            print("\nℹ️  Skipping dummy data (sessions/comments). Use '--with-dummy-data' to generate them.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()
