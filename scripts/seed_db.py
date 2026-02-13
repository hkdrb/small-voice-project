import sys
import os
import random
import hashlib
from datetime import datetime
import secrets

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, User, Comment, AnalysisSession, AnalysisResult, IssueDefinition, Organization, OrganizationMember, CasualPost, CasualPostLike, init_db
from backend.security_utils import hash_pass
from backend.services.mock_generator import (
    generate_mock_analysis_data,
    get_comment_generator,
    get_small_voice_comment,
    get_dense_cluster_comment,
    get_value_comment_q3
)

DATA_GENERATOR_AVAILABLE = True

def create_dummy_users(db):
    print("\n--- Rebuilding Organization Structure and Users ---")
    
    # 1. Ensure/Create Organizations
    org_names = ["サンプル部署", "サンプル案件1", "サンプル案件2"]
    orgs = {}
    for name in org_names:
        org = db.query(Organization).filter(Organization.name == name).first()
        if not org:
            org = Organization(name=name, description=f"{name}のリサーチ用組織")
            db.add(org)
            db.commit()
            db.refresh(org)
        orgs[name] = org

    # Helper to hash password
    admin_pw = os.getenv("INITIAL_ADMIN_PASSWORD", "OrgAdmin1234!")
    hashed_admin_pw = hash_pass(admin_pw)

    # 2. Create Managers (3 members)
    # admin1: Both projects (掛け持ち)
    # admin2: Project 1
    # admin3: Project 2
    managers_info = [
        {"email": "admin1@example.com", "username": "管理者1 (兼務)", "orgs": ["サンプル部署", "サンプル案件1", "サンプル案件2"]},
        {"email": "admin2@example.com", "username": "管理者2 (案件1責任者)", "orgs": ["サンプル部署", "サンプル案件1"]},
        {"email": "admin3@example.com", "username": "管理者3 (案件2責任者)", "orgs": ["サンプル部署", "サンプル案件2"]},
        {"email": "admin4@example.com", "username": "管理者4 (兼務)", "orgs": ["サンプル部署", "サンプル案件1", "サンプル案件2"]},
        {"email": "admin5@example.com", "username": "管理者5 (兼務)", "orgs": ["サンプル部署", "サンプル案件1", "サンプル案件2"]},
        {"email": "admin6@example.com", "username": "管理者6 (兼務)", "orgs": ["サンプル部署", "サンプル案件1", "サンプル案件2"]},
    ]
    
    all_users = []
    for m in managers_info:
        user = db.query(User).filter(User.email == m["email"]).first()
        if not user:
            user = User(email=m["email"], username=m["username"], password_hash=hashed_admin_pw, role="system_user", must_change_password=True)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Assign memberships
        for o_name in m["orgs"]:
            role = "admin" # 全ての所属組織で管理者権限を与える
            existing_member = db.query(OrganizationMember).filter_by(user_id=user.id, organization_id=orgs[o_name].id).first()
            if not existing_member:
                db.add(OrganizationMember(user_id=user.id, organization_id=orgs[o_name].id, role=role))
        all_users.append(user)

    # 3. Create General Members (10 members)
    # user1, user2: Both projects
    # user3-6: Project 1
    # user7-10: Project 2
    # All: Department
    for i in range(1, 11):
        email = f"user{i}@example.com"
        username = f"ユーザー{i}"
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, username=username, password_hash=hashed_admin_pw, role="system_user", must_change_password=True)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Determine target orgs
        target_org_names = ["サンプル部署"]
        if i in [1, 2]:
            target_org_names.extend(["サンプル案件1", "サンプル案件2"])
        elif 3 <= i <= 6:
            target_org_names.append("サンプル案件1")
        elif 7 <= i <= 10:
            target_org_names.append("サンプル案件2")
            
        for o_name in target_org_names:
            existing_member = db.query(OrganizationMember).filter_by(user_id=user.id, organization_id=orgs[o_name].id).first()
            if not existing_member:
                db.add(OrganizationMember(user_id=user.id, organization_id=orgs[o_name].id, role="general"))
        
        all_users.append(user)
    
    db.commit()
    print(f"✅ Prepared {len(all_users)} users across refined organization structure.")
    return all_users

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
        {"title": "企業価値観(Values)についての対話", "theme": "value"},
        # New Forms
        {"title": "今月の業務振り返り (KPT)", "theme": "kpt"},
        {"title": "部会についてのフィードバック", "theme": "bukai"},
        {"title": "サービス精神についての意見", "theme": "service_spirit"},
        {"title": "組織・開発体制についての意見", "theme": "organization"},
        {"title": "1on1・ユニット活動についての意見", "theme": "oneonone_unit"}
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
            
            # Check if this is a new form
            new_form_themes = ['kpt', 'bukai', 'service_spirit', 'organization', 'oneonone_unit']
            if s_data["theme"] in new_form_themes:
                # Generate simple report for new forms
                import json
                report_templates = {
                    "kpt": [
                        {"title": "振り返りプロセスの改善", "description": "KPTの運用方法や振り返りの質向上に関する提案が多数寄せられています。", "urgency": "medium", "category": "Organizational"},
                        {"title": "継続的改善の仕組み化", "description": "Keepの標準化、Problemの根本原因分析、Tryのフォローアップなど、PDCAサイクルを回す仕組みづくりの提案が集まっています。", "urgency": "medium", "category": "Organizational"},
                        {"title": "心理的安全性の確保", "description": "率直な意見を言いやすい環境づくりや、評価への影響を懸念する声があります。", "urgency": "high", "category": "Organizational"},
                        {"title": "【要注意】深刻な懸念（Small Voice）", "description": "少数ですが、ハラスメントや強制的な業務に関する深刻な指摘が存在します。", "urgency": "high", "category": "Organizational"}
                    ],
                    "bukai": [
                        {"title": "情報共有の改善", "description": "部会の資料事前共有、議事録公開、録画配信など、情報の透明性向上に関する提案が多数あります。", "urgency": "medium", "category": "Organizational"},
                        {"title": "運営方法の改善", "description": "部会の時間短縮、頻度の見直し、ハイブリッド形式の導入など、効率的な運営方法の提案が集まっています。", "urgency": "medium", "category": "Organizational"},
                        {"title": "内容の充実", "description": "成功事例の共有、技術トレンドの紹介、現場の課題のボトムアップ共有など、部会の内容をより充実させる提案があります。", "urgency": "low", "category": "Organizational"},
                        {"title": "【要注意】深刻な懸念（Small Voice）", "description": "少数ですが、情報の透明性や意思決定プロセスに関する深刻な指摘が存在します。", "urgency": "high", "category": "Organizational"}
                    ],
                    "service_spirit": [
                        {"title": "サービス精神の定義と共有", "description": "サービス精神の具体的な行動例の明文化や、ベストプラクティスの共有に関する提案が多数あります。", "urgency": "medium", "category": "Organizational"},
                        {"title": "評価と表彰の仕組み", "description": "サービス精神を評価制度に組み込む、表彰制度を新設する、ピアボーナスを導入するなどの提案が集まっています。", "urgency": "medium", "category": "Organizational"},
                        {"title": "実践と浸透の施策", "description": "リーダー層の率先実践、ワークショップ開催、顧客の声の共有など、サービス精神を組織に浸透させる施策の提案があります。", "urgency": "low", "category": "Organizational"},
                        {"title": "【要注意】深刻な懸念（Small Voice）", "description": "少数ですが、サービス精神の名のもとに過度な負担が正当化されることへの懸念が存在します。", "urgency": "high", "category": "Organizational"}
                    ],
                    "organization": [
                        {"title": "組織構造の改善", "description": "部署間連携の強化、意思決定プロセスの明確化、リソース配分の最適化など、組織構造の改善に関する提案が多数あります。", "urgency": "high", "category": "Organizational"},
                        {"title": "評価制度の改善", "description": "評価基準の明文化、フィードバックの充実、評価者研修の実施など、評価制度の透明性向上に関する提案が集まっています。", "urgency": "high", "category": "Organizational"},
                        {"title": "開発体制の最適化", "description": "チーム構成の見直し、コードレビューの改善、技術的負債の返済など、開発体制の最適化に関する提案があります。", "urgency": "medium", "category": "Technical"},
                        {"title": "【要注意】深刻な懸念（Small Voice）", "description": "少数ですが、評価の不公平性や属人化、技術的負債の蓄積に関する深刻な指摘が存在します。", "urgency": "high", "category": "Organizational"}
                    ],
                    "oneonone_unit": [
                        {"title": "1on1の質向上", "description": "時間延長、アジェンダの事前共有、評価との切り離しなど、1on1の質を向上させる提案が多数あります。", "urgency": "medium", "category": "Organizational"},
                        {"title": "1on1の運用改善", "description": "頻度の見直し、満足度測定、メンター制度の拡充など、1on1の運用を改善する提案が集まっています。", "urgency": "medium", "category": "Organizational"},
                        {"title": "ユニット活動の活性化", "description": "目的の明確化、成果の可視化、知見の組織還元など、ユニット活動を活性化させる提案があります。", "urgency": "low", "category": "Organizational"},
                        {"title": "【要注意】深刻な懸念（Small Voice）", "description": "少数ですが、1on1の守秘義務違反やユニット活動の強制参加に関する深刻な指摘が存在します。", "urgency": "high", "category": "Organizational"}
                    ]
                }
                issue_content = json.dumps(report_templates.get(s_data["theme"], []), ensure_ascii=False)
            else:
                # Use existing generator for old forms
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
        
        # New Forms (check first for exact matches)
        if any(w in theme_text for w in ["kpt", "振り返り"]):
            category = "kpt"
        elif any(w in theme_text for w in ["bukai", "部会"]):
            category = "bukai"
        elif any(w in theme_text for w in ["service_spirit", "サービス精神"]):
            category = "service_spirit"
        elif any(w in theme_text for w in ["organization", "組織", "開発体制"]):
            category = "organization"
        elif any(w in theme_text for w in ["oneonone_unit", "1on1", "ユニット"]):
            category = "oneonone_unit"
        # Existing categories
        elif any(w in theme_text for w in ["営業", "sales", "project", "プロジェクト"]):
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


def create_casual_posts(db, users, num_posts=100):
    """雑談掲示板のテストデータを生成"""
    from datetime import timedelta
    
    print(f"\n--- Generating Casual Chat Board Test Data ---")
    
    # 雑談投稿のテンプレート
    CASUAL_POST_TEMPLATES = [
        # チームワーク・コミュニケーション関連
        "最近、チーム内のコミュニケーションがスムーズになってきた気がします。朝会の効果かな？",
        "他部署との連携がもっとスムーズになればいいのにな",
        "今日のミーティング、すごく建設的だった！こういう雰囲気いいですね",
        "リモートワークだと雑談が減って、ちょっと寂しい",
        "新しく入ったメンバーとの交流、もっと増やしたいな",
        "チーム内の情報共有、もう少し効率化できないかな",
        "今日の朝会、短くて的確でよかった！",
        "部署間の壁を感じることがある。もっと気軽に話せる雰囲気があるといいな",
        "プロジェクトの進捗共有、週1でちょうどいい感じ",
        "オンラインだと表情が読みにくくて、意図が伝わりにくいことがある",
        
        # 業務環境・ツール関連
        "新しいツール導入されたけど、使い方がまだよくわからない",
        "作業環境、もう少し静かだと集中できるんだけどな",
        "リモート環境、快適になってきた。モニター2台は必須！",
        "会議室の予約システム、もっと使いやすくならないかな",
        "オフィスの空調、ちょっと寒い日が多い気がする",
        "新しいプロジェクト管理ツール、慣れるまで時間かかりそう",
        "デスク周りの整理整頓、定期的にやらないとすぐ散らかる",
        "リモートワークの日、集中できていい感じ",
        "オフィスに出社する日は、直接話せるから効率いい",
        "ノイズキャンセリングイヤホン、買ってよかった",
        
        # 業務プロセス・効率化関連
        "定例会議、もう少し短くできないかな",
        "承認フロー、もう少しシンプルになるといいな",
        "ドキュメント管理、もっと整理されているといいのに",
        "日報の書き方、テンプレートがあると助かる",
        "タスク管理、自分なりのやり方が確立してきた",
        "会議の議事録、もっと簡潔にまとめられるようになりたい",
        "業務の優先順位付け、いつも悩む",
        "ルーティンワーク、自動化できないかな",
        "報告書のフォーマット、統一されるといいな",
        "メールの返信、もっと早くできるようになりたい",
        
        # スキル・成長関連
        "新しいスキル、習得するのに時間かかるけど楽しい",
        "先輩の仕事の進め方、参考になる",
        "研修で学んだこと、実務で活かせてる",
        "もっと技術的な知識を深めたい",
        "プレゼンスキル、もっと磨きたいな",
        "最近読んだビジネス書、すごく参考になった",
        "資格取得、目指してみようかな",
        "フィードバックもらえると、成長を実感できる",
        "失敗から学ぶこと、多いな",
        "メンターとの1on1、すごく有意義",
        
        # モチベーション・やりがい関連
        "今日のプロジェクト、うまく進んで達成感がある！",
        "お客様から感謝の言葉をもらえると、やる気出る",
        "チームで目標達成できたとき、すごく嬉しい",
        "新しいチャレンジ、ワクワクする",
        "自分の提案が採用されると、モチベーション上がる",
        "成果が見えると、やりがいを感じる",
        "困難な課題を乗り越えたとき、成長を実感",
        "チームメンバーに頼られると、責任感が増す",
        "目標が明確だと、頑張れる",
        "小さな成功体験の積み重ねが大事だな",
        
        # ワークライフバランス関連
        "最近、残業が減ってきて嬉しい",
        "フレックス制度、うまく活用できてる",
        "有給、もっと気軽に取れる雰囲気があるといいな",
        "リフレッシュ休暇、取ってよかった",
        "仕事とプライベートのバランス、大事にしたい",
        "定時で帰れる日が増えてきた",
        "週末しっかり休めると、月曜から頑張れる",
        "趣味の時間、大切にしたい",
        "健康第一。無理しすぎないようにしないと",
        "家族との時間、もっと大切にしたい",
        
        # 職場の雰囲気・文化関連
        "職場の雰囲気、和やかでいいな",
        "困ったときに助け合える文化、ありがたい",
        "意見を言いやすい環境、大事だと思う",
        "チャレンジを応援してくれる雰囲気、好き",
        "失敗を責めない文化、心理的安全性がある",
        "多様性を尊重する風土、素晴らしい",
        "オープンなコミュニケーション、大切",
        "感謝を伝え合う文化、いいですね",
        "イノベーションを推奨する雰囲気、刺激的",
        "フラットな組織、意見が通りやすい",
        
        # 改善提案・アイデア関連
        "こういう仕組みがあったら便利だな、と思うことがある",
        "業務フロー、見直せる部分がありそう",
        "新しいアイデア、試してみたい",
        "他社の事例、参考になりそう",
        "小さな改善の積み重ねが大事",
        "ボトムアップの提案、もっと活発になるといいな",
        "イノベーションミーティング、面白い",
        "改善提案制度、もっと活用したい",
        "ユーザー視点での改善、常に意識したい",
        "効率化のアイデア、チームで共有したい",
        
        # 人間関係・チームビルディング関連
        "チームランチ、楽しかった！",
        "新人歓迎会、盛り上がった",
        "部署の飲み会、久しぶりで楽しかった",
        "チームビルディング、もっとやりたいな",
        "同僚との雑談、息抜きになる",
        "先輩の経験談、勉強になる",
        "後輩の成長、嬉しい",
        "チームの絆、強くなってきた気がする",
        "信頼関係、大切にしたい",
        "お互いをリスペクトする関係、理想的",
        
        # その他日常的な気づき
        "今日は集中できた！",
        "ちょっと疲れたけど、充実した一日だった",
        "明日からまた頑張ろう",
        "週の真ん中、踏ん張りどころ",
        "金曜日、あと少し！",
        "月曜日、新しい週のスタート",
        "今週の目標、達成できそう",
        "予定より早く終わった、ラッキー",
        "想定外のことが起きたけど、なんとかなった",
        "今日学んだこと、メモしておこう",
    ]
    
    # 返信のテンプレート
    REPLY_TEMPLATES = [
        "わかります！私も同じこと感じてました",
        "いいですね！参考にさせてもらいます",
        "確かにそうですよね",
        "その視点、なるほどです",
        "共感します",
        "私も同じ経験あります",
        "それ、いいアイデアですね",
        "ぜひ試してみたいです",
        "勉強になります",
        "その通りだと思います",
        "私も気になってました",
        "一緒に改善していきましょう",
        "前向きな意見、素晴らしいです",
        "そういう考え方もあるんですね",
        "参考になりました、ありがとうございます",
    ]
    
    # 全ての組織を取得
    orgs = db.query(Organization).all()
    if not orgs:
        print("エラー: 組織が見つかりません。")
        return

    total_posts_created = 0
    total_replies_created = 0

    for org in orgs:
        users = db.query(User).join(OrganizationMember).filter(
            OrganizationMember.organization_id == org.id
        ).all()
        
        if not users:
            print(f"スキップ: 組織 '{org.name}' にユーザーがいません。")
            continue
        
        print(f"\n--- 組織: {org.name} ---")
        print(f"ユーザー数: {len(users)}")
        
        # 既存の投稿を削除
        # まず関連するいいねを削除（外部キー制約回避）
        existing_posts = db.query(CasualPost).filter(CasualPost.organization_id == org.id).all()
        existing_post_ids = [p.id for p in existing_posts]
        
        if existing_post_ids:
            db.query(CasualPostLike).filter(CasualPostLike.post_id.in_(existing_post_ids)).delete(synchronize_session=False)
            # 自己参照（返信）の制約回避のため、返信（parent_idがあるもの）を先に削除（念のため）
            db.query(CasualPost).filter(CasualPost.organization_id == org.id, CasualPost.parent_id.isnot(None)).delete(synchronize_session=False)

        deleted_count = db.query(CasualPost).filter(CasualPost.organization_id == org.id).delete(synchronize_session=False)
        db.commit()
        print(f"既存の投稿を削除しました: {deleted_count}件 (関連データ含む)")
        
        # 投稿を生成
        posts = []
        now = datetime.now()
        
        # 過去30日間に分散して投稿を作成
        for i in range(num_posts):
            user = random.choice(users)
            content = random.choice(CASUAL_POST_TEMPLATES)
            
            # ランダムな日時（過去30日間）
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            created_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            post = CasualPost(
                organization_id=org.id,
                user_id=user.id,
                content=content,
                created_at=created_at,
                likes_count=random.randint(0, 10)
            )
            db.add(post)
            posts.append(post)
        
        db.commit()
        print(f"投稿を作成しました: {num_posts}件")
        total_posts_created += num_posts
        
        # 投稿のIDを取得するためにリフレッシュ
        for post in posts:
            db.refresh(post)
        
        # 返信を生成（投稿の約30%に1-3件の返信を追加）
        reply_count = 0
        for post in posts:
            if random.random() < 0.3:  # 30%の確率で返信を追加
                num_replies = random.randint(1, 3)
                for _ in range(num_replies):
                    user = random.choice(users)
                    reply_content = random.choice(REPLY_TEMPLATES)
                    
                    # 元の投稿より後の日時
                    hours_after = random.randint(1, 48)
                    minutes_after = random.randint(0, 59)
                    reply_created_at = post.created_at + timedelta(hours=hours_after, minutes=minutes_after)
                    
                    # 未来の日時にならないようにチェック
                    if reply_created_at > now:
                        reply_created_at = now - timedelta(minutes=random.randint(1, 60))
                    
                    reply = CasualPost(
                        organization_id=org.id,
                        user_id=user.id,
                        parent_id=post.id,
                        content=reply_content,
                        created_at=reply_created_at,
                        likes_count=random.randint(0, 5)
                    )
                    db.add(reply)
                    reply_count += 1
        
        db.commit()
        print(f"返信を作成しました: {reply_count}件")
        total_replies_created += reply_count

    print(f"\n=== 完了 ===")
    print(f"全組織合計: {total_posts_created + total_replies_created}件の投稿・返信を作成しました")



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed the database with initial users and optional dummy data.")
    parser.add_argument("--init-users", action="store_true", help="Create or verify initial dummy users.")
    parser.add_argument("--seed-sessions", action="store_true", help="Create dummy analysis sessions.")
    parser.add_argument("--seed-comments", action="store_true", help="Add dummy comments to EXISTING sessions.")
    parser.add_argument("--seed-casual", action="store_true", help="Generate casual chat board test data (100 posts with replies).")
    parser.add_argument("--with-dummy-data", action="store_true", help="(Legacy) Run all seeds (users, sessions, comments).")
    
    args = parser.parse_args()

    init_db() # Ensure tables exist
    db = SessionLocal()
    
    try:
        # 1. Users
        users = []
        if args.init_users or args.with_dummy_data:
            users = create_dummy_users(db)
        
        # If we need to seed comments/casual but didn't init users, fetch them
        if (args.seed_comments or args.seed_casual) and not users:
            users = db.query(User).filter(User.email.like("user%@example.com")).all()
            if not users:
                print("⚠️ No dummy users found. Generating them automatically to proceed...")
                users = create_dummy_users(db)

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
        
        # 4. Casual Chat Board Posts
        if args.seed_casual:
            if not users:
                print("❌ No users available to author casual posts.")
            else:
                create_casual_posts(db, users, num_posts=100)

        if not (args.init_users or args.seed_sessions or args.seed_comments or args.seed_casual or args.with_dummy_data):
            print("\nℹ️  No actions selected. Use flags:")
            print("  --init-users     : Create users")
            print("  --seed-sessions  : Create session containers")
            print("  --seed-comments  : Add comments to sessions")
            print("  --seed-casual    : Generate casual chat board test data")
            print("  --with-dummy-data: Run all (except casual)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

