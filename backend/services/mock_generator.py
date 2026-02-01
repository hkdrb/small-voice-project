
import random
import json
import datetime
from typing import List, Dict, Any

# --- Sentence Parts Definitions (Copied & Adapted from generate_test_data.py) ---

INTROS = [
    "正直に言うと、", "最近思うのですが、", "以前から気になっていたのですが、", "あくまで個人的な意見ですが、", 
    "担当者として感じることですが、", "現場の声として言わせてください。", "ちょっと思ったんですけど、", 
    "改善提案なのですが、", "今のチームの課題として、", "率直な感想ですが、", "ふと思ったのですが、",
    "議論の余地はあると思いますが、", "個人的には、", "チーム全体として、", "少し気になっている点として、",
]

CLOSINGS = [
    "と思います。", "と感じています。", "という気がします。", "のではないでしょうか。", "をご検討ください。", 
    "をお願いしたいです。", "だと嬉しいです。", "はなんとかならないでしょうか。", "が急務です。", 
    "と強く感じます。", "ですね。", "につきると思います。", "このままだとマズイです。", 
    "改善されることを期待しています。", "と確信しています。", "と願っています。", 
    "の検討をお願いします。", "だと助かります。",
]

# 1. Project Management
PROJ_SUBJECTS = [
    "朝会の時間が", "スプリントプランニングが", "仕様書の更新頻度が", "タスクの粒度が", "JIRAのチケット管理が", 
    "プロダクトオーナーの意思決定が", "要件定義の詰めが", "納期のプレッシャーが", "関係部署との調整が", 
    "会議の回数が", "ドキュメント管理が", "リソース配分が", "バックログの優先順位が", "スプリントレビューの進行が",
    "Slackの通知量が", "情報の透明性が", "意思決定のスピードが", "KPTの質が", "心理的安全性が"
]

PROJ_ACTIONS = [
    "長すぎて業務を圧迫している", "曖昧なまま進んでいて不安だ", "頻繁に変わりすぎて追いつけない", 
    "荒すぎて見積もりができない", "煩雑すぎて更新が漏れる", "遅くて開発が止まることが多い", 
    "甘くて手戻りばかり発生する", "厳しすぎて品質が犠牲になっている", "うまくいかずコンフリクトばかり起きる", 
    "多すぎて作業時間が確保できない", "形骸化していて誰も見ていない", "適切でなく特定の人に負荷が偏っている",
    "不明瞭で何をすべきか迷う", "スムーズでなく時間がもったいない", "多すぎて集中できない",
    "低くて噂話で広まっている", "遅くてチャンスを逃している"
]

PROJ_REASONS = [
    "ので、もっと効率化してほしい", "ため、ルールの見直しが必要です", "から、プロセスを改善すべきです", 
    "ので、ツールを導入して自動化したい", "ため、一度チームで話し合う時間をください", 
    "という現状を打破したい", "ので、上層部の理解が必要です", "ため、専任の担当者をつけてほしい",
    "から、ガイドラインを策定すべきです", "ので、不要なものは廃止しましょう", "ため、改善MTGを開きたいです",
    "ので、リーダーの判断を仰ぎたい", "から、ワークフローを整理したい"
]

# 2. Dev Environment / Welfare
DEV_SUBJECTS = [
    "ローカル開発環境のDockerが", "CI/CDパイプラインが", "検証環境のデータが", "支給されているPCのメモリが", 
    "VPNの接続が", "社内プロキシの設定が", "AWSの権限周りが", "テスト自動化の仕組みが", 
    "使用しているライブラリのバージョンが", "GitHub Copilotの導入が", "モニターの解像度が", 
    "オフィスチェアの座り心地が", "デプロイフローが", "ログ監視ツールが", "開発用サーバーのスペックが",
    "IDEのライセンス数が", "リモートアクセスの手順が"
]

DEV_ACTIONS = [
    "重すぎて開発効率が悪い", "遅すぎて待ち時間が無駄だ", "古すぎて本番と乖離している", 
    "不足していてChromeを開くと固まる", "不安定で頻繁に切断される", "複雑すぎて新しいツールの導入が阻まれる", 
    "厳しすぎて作業が円滑に進まない", "脆弱でよく壊れる", "古すぎてセキュリティリスクがある", 
    "遅れていて競合に負けている", "低すぎて作業領域が狭い", "悪くて腰痛が悪化した", 
    "手動作業が多くてミスが怖い", "使いにくくて調査に時間がかかる", "低すぎてビルドに時間がかかる",
    "足りなくて順番待ちが発生している"
]

DEV_REASONS = [
    "ので、M2/M3 Macへのリプレイスをお願いします", "ため、マシンスペックの底上げが必要です", 
    "から、クラウドベースの開発環境へ移行したい", "ので、ネットワークインフラの増強が急務です", 
    "ため、最新ツールの導入許可をください", "という理由でモチベーションが下がっています", 
    "ので、インフラチームのリソースを増やしてほしい", "ため、予算を確保してください",
    "ので、早急に対応をお願いします", "から、試験的にでも導入したい"
]

# 3. Tech Quality
TECH_SUBJECTS = [
    "レガシーコードの", "APIのレスポンス速度が", "ユニットテストのカバレッジが", "エラーハンドリングが", 
    "データベースのスキーマ設計が", "フロントエンドのコンポーネント設計が", "変数の命名規則が", 
    "ログの出力内容が", "コードレビューの", "技術的負債の", "ドキュメントの", "オンボーディング資料の",
    "ライブラリの依存関係が", "マイクロサービスの分割粒度が", "例外処理の統一感が", "SQLのパフォーマンスが"
]

TECH_ACTIONS = [
    "複雑さが増してメンテナンス不能になりつつある", "遅すぎてUXを損なっている", "低すぎて変更を加えるのが怖い", 
    "統一されておらずデバッグが困難だ", "破綻していてパフォーマンスが出ない", "カオス状態で再利用性が皆無だ", 
    "バラバラで可読性が著しく低い", "不十分で障害調査に役立たない", "基準が曖昧で属人化している", 
    "蓄積されすぎて爆発寸前だ", "陳腐化していて嘘ばかり書いてある", "欠如していて新人が立ち上がれない",
    "複雑に絡み合ってアップデートできない", "不適切で運用負荷が高い", "甘くてデータ整合性が取れない"
]

TECH_REASONS = [
    "ので、リファクタリング期間を設けてほしい", "ため、技術顧問を招聘して指導を仰ぎたい", 
    "から、静的解析ツールの導入を徹底すべきです", "ので、勉強会を開催して意識合わせをしたい", 
    "ため、設計から見直す必要があります", "という状況を放置すべきではありません", 
    "ので、品質保証のプロセスを強化しましょう", "ため、ドキュメントの整備をタスク化してください",
    "ので、Lintツールの導入を検討したい", "から、ペアプロをもっと導入したい"
]

# --- Small Voice & Dense Cluster Definitions ---
SMALL_VOICES = {
    "project": [
        "部門間の対立が深刻で、情報の隠蔽が起きています。",
        "今の売上目標達成のために、コンプライアンスギリギリの営業手法が罷り通っています。",
        "主要な取引先からのクレームが隠蔽されているように感じます。",
        "プロジェクトの赤字が見込まれていますが、誰も報告しようとしません。"
    ],
    "product": [
        "この機能は特定のユーザー層に対して差別的な挙動をする可能性があります。",
        "競合他社の特許を侵害している恐れがあります。",
        "ユーザーの誤操作を誘発するUIになっており、返金トラブルのリスクが高いです。",
        "アクセシビリティへの配慮が欠けており、法的な問題になるかもしれません。"
    ],
    "welfare": [
        "上司からのハラスメントで休職を考えています。",
        "オフィスの空調のカビが原因で体調不良者が続出しています。",
        "育児休暇を取得しようとしたら、評価を下げると暗に脅されました。",
        "サービス残業が常態化しており、労基署への相談を検討しています。"
    ],
    "tech": [
        "顧客の個人情報がログに平文で出力されています。",
        "メインDBのバックアップが半年間失敗し続けています。",
        "使用しているライブラリに深刻な脆弱性が見つかりましたが、放置されています。",
        "本番環境へのアクセス権限管理がずさんで、誰でもデータを削除できてしまいます。"
    ],
    "values": [
        "会社の掲げる『顧客第一』は建前で、実際は利益至上主義になっています。",
    ]
}

DENSE_CLUSTERS = {
    "project": [
        {"topic": "会議過多", "templates": ["会議が多すぎて作業時間がありません。", "無駄な定例を減らすべきです。", "1日中Zoomに繋ぎっぱなしで疲弊しています。"]},
        {"topic": "リーダーシップ不足", "templates": ["リーダーが方針を示してくれません。", "責任の所在が不明確で誰も決めません。", "ビジョンの共有がなく、目の前のタスクをこなすだけになっています。"]},
        {"topic": "情報共有不足", "templates": ["決定事項が現場に降りてきません。", "他部署が何をしているのか全くわかりません。", "情報の透明性が低く、噂レベルの話しか聞こえてきません。"]}
    ],
    "product": [
        {"topic": "ドキュメント不備", "templates": ["仕様書が存在せず、実装が勘頼みになっています。", "要件定義がコロコロ変わり、手戻りが多いです。", "最新の仕様がどこにあるのか誰も知りません。"]},
        {"topic": "UX改善", "templates": ["画面遷移が複雑でユーザーが迷っています。", "もっと直感的なUIにする必要があります。", "モバイルでの操作性が著しく悪いです。"]}
    ],
    "welfare": [
        {"topic": "CI/CD遅延", "templates": ["CIが遅すぎて開発フローが詰まっています。", "デプロイ待ちで1時間無駄にしました。", "ビルド時間の短縮に投資してください。"]},
        {"topic": "PCスペック不足", "templates": ["メモリ8GBではDockerが重くて動きません。", "開発マシンのスペックを上げてください。", "古いPCを使わされており、生産性が低いです。"]}
    ],
    "tech": [
        {"topic": "技術的負債", "templates": ["レガシーコードが複雑すぎて修正できません。", "テストコードがなく、変更が怖いです。", "継ぎ接ぎの改修でアーキテクチャが破綻しています。"]},
        {"topic": "エラー頻発", "templates": ["本番環境で謎のエラーが頻発しています。", "エラーハンドリングが統一されていません。", "システムが不安定で、夜間対応が増えています。"]}
    ],
    "values": [
        {"topic": "称賛文化", "templates": [
            "私たちは互いに称賛し合う文化を作ります。", "感謝を伝える仕組み（Thanksカードなど）を積極的に活用します。", 
            "成果だけでなくプロセスも評価されるべきです。", "ポジティブなフィードバックが飛び交う組織にします。",
            "他チームの成功事例を全力で祝いましょう。"
        ]},
        {"topic": "挑戦", "templates": [
            "新しい技術への挑戦を常に推奨します。", "失敗を恐れずにチャレンジできる環境こそが重要です。", 
            "守りに入らず、攻めの姿勢を貫きます。", "イノベーションを起こすための余白を大切にします。",
            "新しいツールの導入ハードルを下げ、挑戦を加速させます。"
        ]},
        {"topic": "心理的安全性", "templates": [
            "ミスを責めるのではなく、仕組みで解決します。", "反対意見も歓迎される雰囲気を守ります。",
            "若手が自由に発言できる環境を作ります。"
        ]},
        {"topic": "顧客志向", "templates": [
            "ユーザーの声を直接聞く機会を最優先します。", "ドッグフーディングを徹底し、ユーザー視点を忘れません。", 
            "売上よりもユーザー満足度を追求します。", "カスタマーサポートからのフィードバックを宝として扱います。",
            "ペルソナに基づいた開発を徹底します。"
        ]},
        {"topic": "スピード", "templates": [
            "意思決定のスピードを上げ、競合に勝ちます。", "完璧を目指すより、まずリリースして学びます。", 
            "承認プロセスを簡略化し、スピードを落としません。", "アジャイルな開発プロセスを徹底的に実践します。"
        ]}
    ]
}

def get_small_voice_comment(category="project"):
    """Returns a specific outlier comment."""
    cat = category if category in SMALL_VOICES else "project"
    return random.choice(SMALL_VOICES[cat])

def get_dense_cluster_comment(category="project"):
    """Returns a comment from a specific topic cluster."""
    cat = category if category in DENSE_CLUSTERS else "project"
    cluster = random.choice(DENSE_CLUSTERS[cat])
    return random.choice(cluster["templates"])

def generate_sentence(parts):
    return "".join([random.choice(p) for p in parts if p])

def get_comment_generator(category):
    if category == 'project':
        return lambda: generate_sentence([INTROS, PROJ_SUBJECTS, PROJ_ACTIONS, PROJ_REASONS, CLOSINGS])
    elif category == 'welfare' or category == 'dev_env':
        return lambda: generate_sentence([INTROS, DEV_SUBJECTS, DEV_ACTIONS, DEV_REASONS, CLOSINGS])
    elif category == 'tech' or category == 'tech_quality':
        return lambda: generate_sentence([INTROS, TECH_SUBJECTS, TECH_ACTIONS, TECH_REASONS, CLOSINGS])
    elif category == 'values':
        # Valuesカテゴリの多様性を確保するため、トピックごとの生成器をランダムで切り替えるロジックに変更
        topics = [
            # 称賛文化
            lambda: generate_sentence([
                ["互いの成果を", "日々の感謝を", "チームメンバーの頑張りを", "些細な貢献でも"], 
                ["もっと積極的に", "言葉にして", "カードで", "朝会で"], 
                ["称賛し合うべき", "伝え合うべき", "評価すべき"], 
                ["だと思います。", "といいですね。", "文化を作りましょう。"]
            ]),
            # 挑戦
            lambda: generate_sentence([
                ["失敗を恐れずに", "新しい技術に", "未経験の分野に", "リスクを取って"],
                ["どんどん挑戦できる", "チャレンジする", "トライ＆エラーが許される"],
                ["環境が必要です", "雰囲気が大事です", "評価制度にすべきです"],
                ["と強く感じます。", "べきだと思います。", "と信じています。"]
            ]),
            # 心理的安全性/オープンさ
            lambda: generate_sentence([
                ["悪い報告こそ", "困ったときこそ", "反対意見も"],
                ["すぐに言える", "隠さずに共有できる", "歓迎される"],
                ["心理的安全性が", "オープンな場が", "信頼関係が"],
                ["組織には不可欠です。", "あるべき姿です。", "生産性を高めます。"]
            ])
        ]
        return lambda: random.choice(topics)()
    else:
        # Default
        return lambda: generate_sentence([INTROS, PROJ_SUBJECTS, PROJ_ACTIONS, PROJ_REASONS, CLOSINGS])

def get_value_comment_q3():
    # Helper to match original script interface if needed, or just use the generator
    return generate_sentence([INTROS, PROJ_SUBJECTS, PROJ_ACTIONS, PROJ_REASONS, CLOSINGS])

def generate_mock_analysis_data(theme: str, num_points: int = 50):
    """
    Generates mock analysis results and a mock report.
    Returns: (results_list, report_json_string)
    """
    
    # Detemine category from theme
    category = "project"
    if any(w in theme for w in ["製品", "product", "プロダクト"]): category = "product"
    elif any(w in theme for w in ["福利厚生", "welfare", "dev_env", "開発環境"]): category = "welfare"
    elif any(w in theme for w in ["技術", "tech", "quality", "tech_quality"]): category = "tech"
    
    # 1. Generate Results (Points)
    results = []
    
    # Clusters in 2D space (Mock coordinates)
    # Define some centers for clusters
    centers = [
        (5.0, 5.0), (-5.0, 5.0), (5.0, -5.0), (-5.0, -5.0), (0.0, 8.0)
    ]
    
    dense_data = DENSE_CLUSTERS.get(category, DENSE_CLUSTERS["project"])
    small_voices = SMALL_VOICES.get(category, SMALL_VOICES["project"])
    
    # Generators
    gen_func = get_comment_generator(category)

    # Create Cluster Points
    used_topics = []
    if dense_data:
        for i, cluster_def in enumerate(dense_data):
            center = centers[i % len(centers)]
            topic = cluster_def["topic"]
            used_topics.append(topic)
            templates = cluster_def["templates"]
            
            # Generate 10-15 points per cluster
            n_cluster_points = random.randint(8, 12)
            for _ in range(n_cluster_points):
                # Jitter
                x = center[0] + random.gauss(0, 1.0)
                y = center[1] + random.gauss(0, 1.0)
                
                text = random.choice(templates)
                results.append({
                    "original_text": text,
                    "sub_topic": topic,
                    # sentiment removed
                    "summary": text[:30] + "...",
                    "x_coordinate": x,
                    "y_coordinate": y,
                    "cluster_id": i
                })

    # Create Outliers (Small Voices)
    for sv_text in small_voices:
        # Place far away
        x = random.choice([12.0, -12.0]) + random.gauss(0, 1.0)
        y = random.choice([12.0, -12.0]) + random.gauss(0, 1.0)
        
        results.append({
            "original_text": sv_text,
            "sub_topic": "個別意見",
            # sentiment removed
            "summary": sv_text[:30] + "...",
            "x_coordinate": x,
            "y_coordinate": y,
            "cluster_id": -1 # Noise
        })
        
    # Create Noise (Random Generated)
    remaining = max(0, num_points - len(results))
    for _ in range(remaining):
        x = random.uniform(-10, 10)
        y = random.uniform(-10, 10)
        text = gen_func()
        
        results.append({
            "original_text": text,
            "sub_topic": "その他",
            # sentiment removed
            "summary": text[:30] + "...",
            "x_coordinate": x,
            "y_coordinate": y,
            "cluster_id": 99 # Misc cluster
        })
        
    # 2. Generate Report (IssueDefinition)
    # Create a mock report based on the used clusters
    report_issues = []
    
    urgencies = ["high", "medium", "medium", "low"]
    
    for i, topic in enumerate(used_topics):
        report_issues.append({
            "title": topic,
            "description": f"「{topic}」に関する意見が多数（{random.randint(5, 15)}件）寄せられています。現場のボトルネックとなっている可能性が高いです。",
            "urgency": urgencies[i % len(urgencies)],
            "category": "organizational" if "制度" in topic or "会議" in topic else "technical"
        })
        
    # Add one small voice issue
    report_issues.append({
        "title": "【要注意】深刻な懸念（Small Voice）",
        "description": "少数ですが、コンプライアンスやハラスメントに関わる深刻な指摘が存在します。早急な事実確認が推奨されます。",
        "urgency": "high",
        "category": "organizational"
    })

    return results, json.dumps(report_issues, ensure_ascii=False)
