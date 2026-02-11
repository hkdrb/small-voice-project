"""
雑談掲示板のテストデータ生成スクリプト

使用方法:
docker-compose -f docker-compose.dev.yml exec backend python backend/scripts/generate_casual_posts_test_data.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import SessionLocal, CasualPost, User, Organization, OrganizationMember
from datetime import datetime, timedelta
import random

# 雑談投稿のテンプレート（フォームデータと関連性のある内容）
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

def generate_casual_posts(num_posts=100):
    """雑談投稿のテストデータを生成"""
    db = SessionLocal()
    
    try:
        # 組織とユーザーを取得
        org = db.query(Organization).first()
        if not org:
            print("エラー: 組織が見つかりません。先にseed_db.pyを実行してください。")
            return
        
        users = db.query(User).join(OrganizationMember).filter(
            OrganizationMember.organization_id == org.id
        ).all()
        if not users:
            print("エラー: ユーザーが見つかりません。")
            return
        
        print(f"組織: {org.name}")
        print(f"ユーザー数: {len(users)}")
        
        # 既存の投稿を削除
        deleted_count = db.query(CasualPost).filter(CasualPost.organization_id == org.id).delete()
        db.commit()
        print(f"既存の投稿を削除しました: {deleted_count}件")
        
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
                likes_count=random.randint(0, 10)  # ランダムないいね数
            )
            db.add(post)
            posts.append(post)
        
        db.commit()
        print(f"投稿を作成しました: {num_posts}件")
        
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
        print(f"合計: {num_posts + reply_count}件の投稿・返信を作成しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 雑談掲示板テストデータ生成 ===")
    generate_casual_posts(100)
    print("完了しました！")
