import pandas as pd
import random
import os
import shutil
from datetime import datetime, timedelta
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Configuration ---
NUM_ROWS_VALUES = 1000
NUM_ROWS_OTHERS = 1000
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "test_data")

# --- Utility Functions ---
def generate_random_date():
    start_date = datetime.now() - timedelta(days=90)
    random_days = random.randint(0, 90)
    random_seconds = random.randint(0, 86400)
    dt = start_date + timedelta(days=random_days, seconds=random_seconds)
    return dt.strftime("%Y/%m/%d %H:%M")

def generate_combinatorial_sentence(parts):
    """
    parts: list of lists
    """
    sentence = ""
    for part_list in parts:
        if not part_list: continue
        fragment = random.choice(part_list)
        if fragment:
            sentence += fragment
    return sentence

def generate_unique_sentence_list(generator_func, count, max_retries=10):
    """Generates a list of unique sentences."""
    seen = set()
    result = []
    
    for i in range(count):
        sentence = generator_func()
        retries = 0
        while sentence in seen and retries < max_retries:
            sentence = generator_func()
            retries += 1
        
        # If still duplicate after retries, just use it (duplicates are acceptable)
        seen.add(sentence)
        result.append(sentence)
    
    return result

# --- Sentence Parts Definitions (Proposal Oriented) ---

INTROS = [
    "改善提案ですが、", "もっと良くするために、", "効率化の提案として、", "個人的なアイデアですが、", 
    "チームの生産性を上げるために、", "以前から考えていたのですが、", "解決策として提案します。", 
    "この課題に対する打ち手として、", "将来的には、", "理想を言えば、", "試してみたいこととして、",
    "議論したい点として、", "解決案ですが、", "思い切って提案しますが、", "ご検討いただきたいのですが、",
    "", "", "", "", "", ""
]

CLOSINGS = [
    "を導入すべきだと思います。", "に変更するのはどうでしょうか。", "を試してみたいです。", 
    "とすることで解決できるはずです。", "の実施を強く推奨します。", "を検討してください。", 
    "で進めるのがベストだと思います。", "のルール化をお願いします。", "への投資が必要だと思います。", 
    "を次回のMTGで議論したいです。", "を標準化しましょう。", "に切り替えるべきです。", 
    "という方向で進めませんか？", "の運用を開始したいです。", "をトライアル導入してはどうでしょう。", 
    "の徹底をお願いしたいです。", "という施策が有効だと思います。", "が良いと思います。", 
    "", "", ""
]

# 1. Project Management
PROJ_SUBJECTS = [
    "朝会の時間については、", "スプリントプランニングの方法は、", "仕様書の更新フローは、", "タスクの粒度に関しては、", "JIRAの運用は、", 
    "意思決定のプロセスについては、", "要件定義の進め方は、", "納期の調整については、", "他部署との連携方法は、", 
    "会議の頻度については、", "ドキュメント管理については、", "リソース配分は、", "バックログの優先順位付けは、", "スプリントレビューは、",
    "Slackの運用ルールは、", "情報の透明性確保については、", "KPTのやり方は、", "心理的安全性向上のため、"
]

PROJ_SOLUTIONS = [
    "15分以内に制限し、延長は禁止する", "非同期コミュニケーションに移行する", "自動化ツールを導入して工数を削減する", 
    "担当者をローテーション制にする", "テンプレート化して品質を統一する", "承認フローを簡略化する", 
    "事前にアジェンダを共有し、準備を義務付ける", "外部の専門家を招いて知見を借りる", "専任のPMをアサインする", 
    "不要な会議を廃止し、Slackでの報告のみにする", "Notionに情報を集約し、検索性を高める", "明確なガイドラインを策定する", 
    "定期的な1on1を実施してフォローする", "すべての履歴をオープンにし、誰でも見れるようにする", "ボトムアップでの提案を推奨する"
]

PROJ_EFFECTS = [
    "ことで、開発時間を確保できます", "ことで、属人化を解消できます", "ことで、意思決定スピードが上がります", 
    "ことで、チームの士気が高まります", "ことで、ミスの発生を防げます", "ことで、無駄な待ち時間をなくせます", 
    "ことで、新人のオンボーディングがスムーズになります", "ことで、本来の業務に集中できます", 
    "ことで、手戻りを最小限に抑えられます", "ことで、心理的負担を軽減できます"
]

# 2. Dev Environment
DEV_SUBJECTS = [
    "ローカル開発環境については、", "CI/CDパイプラインは、", "検証環境のデータ管理は、", "PCのスペックについては、", 
    "VPNの接続問題は、", "社内プロキシの設定は、", "AWSの権限管理は、", "自動テストの運用は、", 
    "ライブラリの更新方針は、", "Copilotの活用については、", "モニターの支給については、", 
    "デプロイフローに関しては、", "ログ監視の仕組みは、", "開発サーバーの増強は、"
]

DEV_SOLUTIONS = [
    "Dockerコンテナを軽量化する", "並列実行数を増やして高速化する", "マスキング済みの本番データを使えるようにする", 
    "M3 Macを一括導入する", "クラウドベースの開発環境(GitHub Codespaces等)に移行する", "より高速なVPNサービスに乗り換える", 
    "IaC(Terraform)ですべて管理する", "E2Eテストを拡充する", 
    "Renovateを導入して自動更新する", "全エンジニアにCopilotライセンスを付与する", "4Kモニターを標準支給する", 
    "ブルーグリーンデプロイを導入する", "Datadog等の専用ツールを導入する"
]

DEV_EFFECTS = [
    "ことで、開発効率が劇的に向上します", "ことで、デプロイ待ち時間を削減できます", "ことで、環境差異によるバグを撲滅できます", 
    "ことで、ストレスなくコーディングできます", "ことで、場所を選ばず働けます", 
    "ことで、セキュリティリスクを低減できます", "ことで、障害時の復旧が早くなります", 
    "ことで、優秀なエンジニアを採用しやすくなります"
]

# 3. Tech Quality
TECH_SUBJECTS = [
    "レガシーコードの解消は、", "APIのパフォーマンス改善は、", "ユニットテストのカバレッジ向上は、", "エラーハンドリングの統一は、", 
    "DBスキーマの見直しは、", "コンポーネント設計の共通化は、", "命名規則の統一は、", 
    "ログ設計については、", "コードレビューの質向上は、", "技術的負債の返済は、", "ドキュメントの整備は、", 
    "マイクロサービス化については、", "例外処理の実装は、", "クエリの最適化は、"
]

TECH_SOLUTIONS = [
    "毎週金曜日をリファクタリングデーにする", "キャッシュ戦略を見直してRedisを導入する", "テストカバレッジ80%をCIの必須条件にする", 
    "共通のエラーハンドリングミドルウェアを実装する", "正規化を徹底し、インデックスを適切に貼る", 
    "Design Systemを構築して再利用する", "Linter/Formatterのルールを厳格化する", 
    "構造化ログ(JSON)を徹底する", "ペアプログラミングを積極的に導入する", 
    "技術的負債返済のためのスプリントを設ける", "Swagger/OpenAPIからコードを自動生成する", 
    "ドメイン駆動設計(DDD)を取り入れる"
]

TECH_EFFECTS = [
    "ことで、保守性が向上します", "ことで、ユーザー体験が改善されます", "ことで、バグの混入を防げます", 
    "ことで、障害調査が容易になります", "ことで、新規メンバーの参画コストが下がります", 
    "ことで、変更に強いシステムになります", "ことで、コードの品質が均一化されます", 
    "ことで、長期的な開発コストを下げられます"
]

# 4. Values (Combinatorial Explosion needed here)
# Q1: あなたが仕事をする上で、大切にしている価値観を教えてください

# テーマごとにグループ化して、クラスタリングが適切に機能するようにする
VALUES_THEMES_GROUPED = {
    "感謝・称賛": [
        "私は感謝の気持ちとリスペクトを大切にしています。",
        "仕事ではチームワークを何より大切にしています。",
        "常に仲間への信頼を重視しています。",
        "何よりも助け合いの精神を大事にしています。",
        "特に感謝を伝えることを心がけています。",
        "日々の業務で相互尊重を大切にしています。",
        "チームで働く上で協力し合うことを重視しています。",
        "プロとして感謝の気持ちを忘れないようにしています。"
    ],
    "挑戦": [
        "私は新しいことに挑戦する姿勢を大事にしています。",
        "仕事では失敗を恐れない心を持ち続けたいと思っています。",
        "常に変化への適応を心がけています。",
        "何よりも野心的な目標に向かって進むことを大切にしています。",
        "特にイノベーションを追求することを重視しています。",
        "日々の業務で新しい挑戦を楽しんでいます。",
        "チームで働く上で挑戦的な姿勢を大事にしています。",
        "プロとして成長し続けることを心がけています。"
    ],
    "心理的安全性": [
        "私は心理的安全性を大事にしています。",
        "仕事では透明性を重視しています。",
        "常に情報をオープンにすることを心がけています。",
        "何よりも率直な対話を大切にしています。",
        "特に風通しの良さを重視しています。",
        "日々の業務でオープンなコミュニケーションを心がけています。",
        "チームで働く上で安心して意見を言える環境を大事にしています。",
        "プロとして誠実であることを大切にしています。"
    ],
    "顧客・品質": [
        "私は顧客第一の考え方を軸にしています。",
        "仕事では品質にこだわることを大切にしています。",
        "常にプロフェッショナルとしての責任を重視しています。",
        "何よりもユーザー視点を意識しています。",
        "特に誠実な対応を心がけています。",
        "日々の業務で顧客満足を最優先にしています。",
        "チームで働く上で品質への妥協をしないことを大事にしています。",
        "プロとして顧客の期待を超えることを目指しています。"
    ],
    "スピード・効率": [
        "私はスピード感を持って動くことを心がけています。",
        "仕事では効率を追求することを心がけています。",
        "常に自律的に行動することを重視しています。",
        "何よりも無駄を排除することを大事にしています。",
        "特に迅速な意思決定を心がけています。",
        "日々の業務でスピードと品質の両立を目指しています。",
        "チームで働く上で効率的な働き方を重視しています。",
        "プロとして素早く価値を届けることを大切にしています。"
    ]
}

# For Q3 (shared values proposals)
VALUES_THEMES = [
    "誠実な行動", "プロフェッショナルとしての責任", "チームワーク", "挑戦する姿勢", 
    "顧客第一主義", "圧倒的なスピード", "感謝とリスペクト", "楽しむ心", 
    "論理的思考", "継続的な学習", "心理的安全性", "情報のオープン化", 
    "自律的な行動", "Give & Give", "健康第一", "当事者意識", 
    "透明性", "多様性の受容", "効率の追求", "品質へのこだわり"
]




# Q2: その価値観を大切にするようになったきっかけは？（実際のエピソード）
VALUES_EPISODE_TRIGGERS = [
    "新人の頃、", "入社当時、", "前職で、", "あるプロジェクトで、", 
    "リーダーになった時、", "大きな失敗をした時、", "先輩から学んだのは、", 
    "顧客からのクレームで、", "チームが危機に陥った時、", "昔、", "以前、"
]

VALUES_EPISODE_SITUATIONS = [
    "納期に間に合わず顧客に迷惑をかけた経験から", 
    "チームメンバーの助けで難局を乗り越えた経験から",
    "正直に報告したことで信頼を得られた経験から",
    "隠蔽が大きな問題に発展するのを見て",
    "失敗を責められて萎縮した経験から",
    "上司が率先して動く姿を見て",
    "顧客の笑顔を直接見られた経験から",
    "品質を妥協して後悔した経験から",
    "スピードを重視して成功した経験から",
    "情報共有不足でトラブルになった経験から",
    "感謝の言葉で救われた経験から",
    "チャレンジを応援してもらえた経験から",
    "健康を害してしまった経験から",
    "多様な意見が良い結果を生んだ経験から",
    "効率化で時間を生み出せた経験から"
]

VALUES_EPISODE_LEARNINGS = [
    "この価値観の重要性に気づきました。",
    "この考え方を大切にするようになりました。",
    "これを忘れてはいけないと思うようになりました。",
    "この姿勢が必要だと痛感しました。",
    "この価値観を軸にしようと決めました。",
    "これこそが大事だと学びました。",
    "この考えを持ち続けようと思いました。"
]


# Q3 Expansion (Already somewhat proposal oriented, specifically modifying to be stronger)
Q3_PREFIXES = [
    "これからは、", "改めて提案しますが、", "まずは、", "チームとして、", "私たちには、", 
    "組織全体で、", "もっと強く、", "今こそ、", "リーダー層が率先して、", "新入社員も含めて、",
    "開発部全体で、", "ビジネスサイドも含めて、", "会社として、", "行動指針として、", "会議の場でも、"
]

Q3_TEMPLATES = [
    "「{}」という文化を定着させる施策を実施しましょう。", 
    "全員が「{}」を実践するためのワークショップを開催したい。", 
    "「{}」を評価の最重要項目に設定する提案です。", 
    "「{}」を体現した人を表彰する制度を作りませんか。",
    "「{}」を毎朝の朝会で確認するルーチンを導入したい。",
    "言葉だけでなく行動で「{}」を示すキャンペーンを行いましょう。",
    "採用基準に「{}」への共感を必須条件にすべきです。",
    "「{}」を阻害する要因を取り除きましょう。",
    "常に「{}」を問いかける時間を設けたい。",
    "「{}」に基づいた360度フィードバックを導入しましょう。"
]

Q3_SUFFIXES = [
    "そうすれば組織は変わります。", "それが一番の近道です。", "と強く提案します。", 
    "という風土を作っていきたいです。", "実現には不可欠です。", "と信じています。",
    "やってみる価値は大きいです。", "から始めてみませんか？", "という意識改革が必要です。",
    "でなければ生き残れません。", "が成功のカギです。", "に立ち返るべきです。"
]

# --- Small Voice & Dense Cluster Definitions (Proposal Oriented) ---

SMALL_VOICES = {
    "project": [
        "部長の経費私的流用疑惑について、第三者委員会による調査を提案します。",
        "役員への虚偽報告を防ぐため、監査ログの自動送信システムを導入すべきです。",
        "機密情報流出を防ぐため、USBポートの物理封鎖とログ監視の強化を求めます。",
        "ハラスメント防止のため、外部機関による匿名通報窓口の設置を即時に行うべきです。"
    ],
    "product": [
        "脆弱性対応のため、リリースを延期し、セキュリティ監査を完了させることを提案します。",
        "差別的なUIを修正するため、アクセシビリティ専門家の監修を受けるべきです。",
        "過剰徴収バグについて、ユーザーへの正直な謝罪と全額返金を直ちに行うべきです。",
        "著作権侵害リスク回避のため、該当コードの完全書き直しを提案します。"
    ],
    "welfare": [
        "監視カメラによる監視をやめ、信頼に基づくマネジメントへの転換を求めます。",
        "サービス残業撤廃のため、PCの強制シャットダウンシステムの導入を提案します。",
        "ハラスメント相談窓口を人事から独立した外部機関に委託することを提案します。",
        "耐震性の問題について、即時のビル移転または補強工事の実施を求めます。"
    ],
    "tech": [
        "顧客情報の平文保存をやめ、DBレベルでの暗号化を即時実施するよう提案します。",
        "ソースコード流出を防ぐため、プライベートリポジトリの権限棚卸しを提案します。",
        "バックアップ失敗の対策として、リストア訓練を含むDR計画の策定を求めます。",
        "退職者のアクセス権限を自動削除するID管理システムを導入すべきです。"
    ],
    "values": [
        "心理的安全性を担保するため、無記名での組織サーベイ実施を提案します。",
        "多様性を確保するため、採用における学歴フィルターの廃止を提案します。",
        "下請け法遵守のため、発注プロセスの透明化と監査を求めます。",
        "失敗を許容する文化醸成のため、失敗事例発表会の定期開催を提案します。"
    ],
    "values_episode": [
        "大きな不正を目撃したが報告できなかった無力感から、組織の透明性を何より大切にするようになりました。",
        "過労で倒れた同僚を見て、健康を犠牲にする働き方は間違っていると強く思うようになりました。",
        "育休取得を妨害された経験から、多様性を尊重する文化の重要性を痛感しました。",
        "内部告発者が不当に扱われるのを見て、心理的安全性の確保が最優先だと考えるようになりました。"
    ],
    "values_theme": [
        "多様性の受容", "健康第一", "社会貢献", "コンプライアンス遵守", 
        "サステナビリティ", "公平性", "ワークライフバランス"
    ]
}

DENSE_CLUSTERS = {
    "project": [
        {"topic": "会議効率化", "templates": [
            "会議は原則30分以内とし、アジェンダなしの会議は禁止するというルールを提案します。",
            "定例会議を廃止し、Slackでの非同期報告に切り替えることを提案します。",
            "Zoom会議でのカメラON矯正をやめ、画面共有中心の進行にすべきです。", 
            "会議資料は必ず前日までに共有し、会議中は意思決定のみを行う運用にしましょう。",
            "ファシリテーター持ち回り制を導入し、進行スキルを全員で上げるべきです。"
        ]},
        {"topic": "リーダーシップ改善", "templates": [
            "リーダーの方針を明文化し、Wikiで常に確認できるようにしてほしいです。",
            "権限委譲を進めるため、決裁権限規定の見直しを提案します。", 
            "トラブル時のエスカレーションフローをチャート化し、周知徹底すべきです。",
            "マネージャーとメンバーの1on1を隔週で実施し、対話の時間を確保しましょう。",
            "ビジョン合宿を開催し、全員で方向性を再確認する場を作ることを提案します。"
        ]},
        {"topic": "見積もり精度向上", "templates": [
            "見積もりはエンジニア主導で行い、営業はそれに従うフローを確立すべきです。",
            "スケジュールには必ず20%のバッファを含めるルールを提案します。", 
            "仕様変更が発生した場合は、必ず納期の再調整を行う契約にすべきです。",
            "プランニングポーカーを導入し、見積もりの属人化を排除しましょう。",
            "過去の実績データを蓄積し、データに基づいた見積もりを行うツールを導入しませんか。"
        ]},
        {"topic": "情報共有の改善", "templates": [
            "決定事項は必ず全チャンネルでアナウンスするルールにしましょう。",
            "他部署の朝会にランダムで参加し、相互理解を深める施策を提案します。", 
            "口頭での仕様伝達を禁止し、すべてチケットに残す運用を徹底すべきです。",
            "情報の透明性を高めるため、役員会議の議事録も公開してはどうでしょうか。",
            "社内Wikiの構造を整理し、検索性を改善するためのタスクフォースを立ち上げたいです。"
        ]},
        {"topic": "評価制度の刷新", "templates": [
            "定量的な評価基準を策定し、評価の透明性を高めることを提案します。",
            "成果だけでなくプロセスも評価する『バリュー評価』の比重を上げるべきです。",
            "360度評価の結果を本人にフィードバックし、成長の糧にする運用に変えましょう。",
            "評価者研修を実施し、マネージャー間の評価基準のばらつきをなくすべきです。",
            "ピアボーナス制度を導入し、相互評価の文化を作りませんか。"
        ]}
    ],
    "product": [
        {"topic": "ドキュメント整備", "templates": [
            "仕様書がない機能の実装は行わないというルールを徹底すべきです。",
            "要件定義書をGitで管理し、変更履歴を追えるようにすることを提案します。", 
            "最新の仕様へのリンクを常にSlackのチャンネルトピックに貼る運用にしましょう。",
            "ドキュメント専任担当者を配置し、品質を維持する体制を作るべきです。",
            "Figmaと実装の乖離を防ぐため、デザインシステムの導入を提案します。"
        ]},
        {"topic": "UX改善施策", "templates": [
            "ユーザーテストを開発初期段階で実施し、手戻りを防ぐフローを提案します。",
            "直感的なUIにするため、ヒートマップツールを導入して分析すべきです。", 
            "モバイルファーストでデザインを見直すプロジェクトを立ち上げたいです。",
            "デザインの統一性を保つため、UIコンポーネントライブラリを整備しましょう。",
            "ロード時間短縮のため、画像の最適化とCDNの活用を提案します。"
        ]},
        {"topic": "アクセシビリティ対応", "templates": [
            "スクリーンリーダーでの動作確認をQA項目に追加することを提案します。",
            "配色のコントラスト比をチェックするCIツールを導入すべきです。", 
            "WAI-ARIAに準拠したマークアップを徹底するガイドラインを策定しましょう。",
            "キーボード操作のみで完結できるようにUIを改修すべきです。",
            "全画像のalt属性入力を必須化するLintルールを追加しませんか。"
        ]},
        {"topic": "多言語対応", "templates": [
            "プロの翻訳家に依頼し、機械翻訳の不自然さを解消することを提案します。",
            "日時フォーマットをライブラリで自動変換する実装に統一すべきです。", 
            "i18n対応のライブラリを導入し、テキストのハードコードを禁止しましょう。",
            "多通貨決済に対応するための決済基盤の刷新を提案します。"
        ]},
        {"topic": "検索機能強化", "templates": [
            "Elasticsearchを導入し、検索精度と速度を向上させる提案です。",
            "表記ゆれに対応するため、辞書データの整備を行うべきです。", 
            "検索結果のフィルタリングUIを改善し、使い勝手を向上させましょう。",
            "AIを活用したサジェスト機能を実装し、UXを高める提案をします。"
        ]}
    ],
    "welfare": [
        {"topic": "CI/CD高速化", "templates": [
            "CIの並列実行数を増やし、待ち時間を半減させる投資を提案します。",
            "ビルドキャッシュを活用し、デプロイ時間を短縮する設定を入れましょう。", 
            "ボトルネックになっているテストを特定し、リファクタリングする時間をください。",
            "GitHub ActionsのSelf-hosted Runnerを導入し、コストと速度を改善すべきです。",
            "デプロイ完了通知をSlackだけでなくデスクトップ通知にも連携させたいです。"
        ]},
        {"topic": "ハードウェア刷新", "templates": [
            "全エンジニアのPCをメモリ32GB以上にアップグレードすることを提案します。",
            "生産性向上のため、希望者には昇降デスクを支給してはどうでしょうか。", 
            "古いPCのリプレイス基準を明確にし、定期的に更新する制度を作りましょう。",
            "M3 Macの導入ROIを算出したので、試験導入を許可してください。", 
            "モニターを2枚支給し、開発効率を上げる投資をお願いします。"
        ]},
        {"topic": "リモート環境改善", "templates": [
            "より安定したVPNサービスへの乗り換えを強く推奨します。", 
            "リモートワーク手当を増額し、自宅の通信環境整備に充てさせるべきです。",
            "フルリモート、ハイブリッドを選択できる柔軟な勤務体系を提案します。",
            "オフィスとリモートの格差をなくすため、全会議をオンライン前提にしましょう。"
        ]},
        {"topic": "スキルアップ支援", "templates": [
            "技術書購入やUdemy受講の費用を無制限で補助する制度を提案します。",
            "国内外のカンファレンス参加費と渡航費を会社が負担する仕組みを作りましょう。", 
            "業務時間の20%を学習や研究に使ってよい『20%ルール』を導入しませんか。",
            "資格取得報奨金制度を復活させ、学習意欲を刺激すべきです。",
            "社内勉強会のランチ補助を出し、コミュニケーションを活性化させましょう。"
        ]},
        {"topic": "健康経営", "templates": [
            "人間ドックの費用補助対象を若手社員にも拡大することを提案します。",
            "産業医との面談をオンラインで気軽に予約できるシステムを導入すべきです。", 
            "メンタルヘルスチェックを義務化し、早期発見できる体制を作りましょう。",
            "インフルエンザ予防接種の社内集団接種を実施してはどうでしょうか。"
        ]}
    ],
    "tech": [
        {"topic": "技術的負債返済", "templates": [
            "機能開発を止めてリファクタリングに集中する期間を設けることを提案します。",
            "テストコードがない箇所の改修は禁止するというルールを作りましょう。", 
            "技術的負債をバックログ化し、スプリントごとに消化する運用を提案します。",
            "複雑なクラスを分割し、責務を明確にする設計見直し時間をください。",
            "古いライブラリを一掃するための特別プロジェクトを立ち上げたいです。"
        ]},
        {"topic": "エラー撲滅", "templates": [
            "エラーログの監視ツール(Sentry等)を導入し、検知を自動化すべきです。",
            "独自のエラーコード体系を廃止し、標準的なHTTPステータスに準拠しましょう。", 
            "ログにトレーシングIDを付与し、リクエストを一気通貫で追えるようにする提案です。",
            "夜間のシステムアラートを削減するため、自動復旧の仕組みを導入しませんか。",
            "エラー通知の閾値を見直し、オオカミ少年状態を解消すべきです。"
        ]},
        {"topic": "セキュリティ強化", "templates": [
            "脆弱性スキャンをパイプラインに組み込み、リリースをブロックする運用にしましょう。",
            "パスワードレス認証(WebAuthn)を導入し、セキュリティと利便性を両立させたいです。", 
            "S3バケットの公開設定を自動チェックする仕組み(Config rules)を入れましょう。",
            "個人情報を含むデータへのアクセスログを常時監視する体制を提案します。",
            "退職者アカウントの削除フローを自動化し、人的ミスをなくすべきです。"
        ]},
        {"topic": "コスト削減", "templates": [
            "AWSのコスト分析を行い、無駄なリソースを削減するタスクフォースを希望します。",
            "開発環境の自動停止スクリプトを導入し、夜間休日コストをカットしましょう。", 
            "ログの保持期間ポリシー策定と、S3ライフサイクル設定の適用を提案します。",
            "リザーブドインスタンスやSavings Plansの購入検討をお願いします。",
            "CDNのキャッシュ設定を見直し、オリジンへの負荷と転送量を減らす提案です。"
        ]},
        {"topic": "ドキュメントツール活用", "templates": [
            "社内ドキュメントツールをNotionに統一し、情報の一元化を図るべきです。",
            "Wikiの定期的な棚卸しデーを設け、古い情報をアーカイブする運用にしましょう。", 
            "API仕様書はSwagger(OpenAPI)でコードから自動生成するフローにしませんか。",
            "議事録は自動文字起こしツールを導入し、作成工数をゼロにする提案です。"
        ]}
    ],
    "values": [
        {"topic": "称賛の仕組み", "templates": [
            "Slackに『#thanks』チャンネルを作り、ボットで集計して表彰する仕組みを提案します。",
            "ピアボーナスツールを導入し、感謝を少額のボーナスとして送り合う制度にしませんか。", 
            "週次MTGの冒頭で、今週のMVPを発表する時間を設けましょう。",
            "失敗した挑戦も称賛する『ナイスチャレンジ賞』の新設を提案します。",
            "他部署の貢献を見える化する社内報の発行を提案します。",
            "『ありがとう』を言う回数をKPIにするくらいの勢いで文化を変えたいです。",
            "ポジティブフィードバックのワークショップを全員で受けませんか。"
        ]},
        {"topic": "挑戦の奨励", "templates": [
            "業務時間の10%を新しい技術検証に使ってよいルールを導入すべきです。",
            "失敗しても評価が下がらないことを明文化した『チャレンジ評価制度』を提案します。", 
            "新規事業コンテストを開催し、ボトムアップでアイデアを募集しましょう。",
            "ハッカソンを定期開催し、イノベーションの種を撒く活動を推奨します。",
            "新しいツールの導入稟議を簡素化し、スピード感を持って試せる環境にしてください。",
            "『まずはやってみる』を合言葉に、PoCのハードルを極限まで下げる提案です。",
            "失敗事例データベースを作り、ナレッジとして共有することを提案します。"
        ]},
        {"topic": "心理的安全性向上", "templates": [
            "無記名で経営陣に質問できるQ&Aセッションの定期開催を提案します。",
            "『Yes, And』の精神で、反対意見もまずは受け止めるルールを会議に導入しましょう。",
            "若手社員がメンター以外にも相談できる斜めの関係作りを支援する制度が必要です。",
            "心理的安全性を測るサーベイを毎月実施し、改善サイクルを回すべきです。",
            "ミスをした人を責めるのではなく、システムの問題として捉える『ポストモーテム』を徹底しましょう。",
            "役職呼びを禁止し、『さん付け』またはニックネームで呼ぶ文化にしませんか。",
            "1on1は評価のためではなく、成長支援と対話のために行うよう再定義すべきです。"
        ]},
        {"topic": "顧客志向の徹底", "templates": [
            "開発者も定期的にカスタマーサポート業務を体験し、顧客の声を直接聞く研修を提案します。",
            "ドッグフーディングを義務化し、自分たちが一番のヘビーユーザーになるべきです。", 
            "NPS（顧客推奨度）を全社員の共通KPIに設定することを提案します。",
            "顧客インタビューの動画をランチタイムに上映し、ユーザー像を共有しましょう。",
            "ペルソナシートをオフィスの目立つ場所に貼り出し、常に顧客を意識させたいです。",
            "機能リリース後の利用状況を分析し、使われていない機能は削除する勇気を持ちませんか。",
            "クライアントに招待され、現場を見学するツアーを企画したいです。"
        ]},
        {"topic": "スピード重視", "templates": [
            "承認プロセスを最大2段階までに減らし、意思決定スピードを上げる提案です。",
            "完璧を目指してリリースを遅らせるより、MVPで早く市場に出す方針に転換すべきです。", 
            "会議での持ち帰り検討を禁止し、その場で決断するルールを導入しませんか。",
            "アジャイル開発の講師を招き、本格的なスクラム導入を検討すべきです。",
            "稟議書を廃止し、Slackでのスタンプ承認で進められる範囲を広げましょう。",
            "まずは小さく試して、ダメならすぐ撤退できる『サンクコスト無視』の文化を作りたいです。",
            "リリースサイクルを週1回から毎日変更するための自動化投資を提案します。"
        ]}
    ],
    "values_episode": [
        {"topic": "信頼構築の経験", "templates": [
            "新人の頃、正直にミスを報告したら上司が一緒に解決してくれて、誠実さの大切さを学びました。",
            "前職で、隠蔽が大問題に発展するのを見て、透明性の重要性を痛感しました。",
            "あるプロジェクトで、チーム全員で情報を共有したことで危機を乗り越え、オープンさの価値に気づきました。",
            "顧客に正直に状況を伝えたら逆に信頼してもらえた経験から、誠実な対応を心がけるようになりました。",
            "先輩が常に真実を語る姿勢を見て、この価値観を大切にしようと決めました。"
        ]},
        {"topic": "チームワークの学び", "templates": [
            "大きな障害対応で、チーム全員が助け合って乗り越えた経験から、協力の大切さを実感しました。",
            "一人で抱え込んで失敗した経験から、チームワークの重要性に気づきました。",
            "他部署との連携がうまくいってプロジェクトが成功した時、協働の価値を学びました。",
            "困っている時に同僚が手を差し伸べてくれて、助け合いの精神を持ち続けようと思いました。",
            "リーダーになった時、一人では何もできないと痛感し、チームの力を信じるようになりました。"
        ]},
        {"topic": "挑戦の価値", "templates": [
            "新しい技術に挑戦して成功した経験から、チャレンジする姿勢を大切にするようになりました。",
            "失敗を恐れずに提案したら採用されて、挑戦の重要性を実感しました。",
            "上司が失敗を責めずに次のチャンスをくれたことで、挑戦する勇気を持てるようになりました。",
            "前職で保守的すぎて機会を逃した経験から、積極的に挑む姿勢が必要だと学びました。",
            "先輩が常に新しいことに挑戦する姿を見て、この価値観を持ち続けようと思いました。"
        ]},
        {"topic": "顧客志向の目覚め", "templates": [
            "顧客から直接感謝された経験から、ユーザー第一の考え方を大切にするようになりました。",
            "自分が作った機能で誰かが喜んでいるのを見て、顧客視点の重要性に気づきました。",
            "クレーム対応で顧客の立場に立って考えたら解決できた経験から、この姿勢を持ち続けようと決めました。",
            "社内都合で判断して失敗した経験から、常に顧客目線で考えるべきだと痛感しました。",
            "カスタマーサポートを経験して、ユーザーの声を聞く大切さを学びました。"
        ]},
        {"topic": "スピードと効率", "templates": [
            "素早く対応したことで顧客に喜ばれた経験から、スピードの価値を実感しました。",
            "完璧を求めすぎて機会を逃した経験から、まず動くことの大切さを学びました。",
            "効率化によって時間を生み出し、より価値ある仕事ができた経験から、この考え方を持つようになりました。",
        ]}
    ],
    "values_theme": [
        {"topic": "感謝・称賛", "templates": [
            "私は感謝の気持ちとリスペクトを大切にしています。",
            "チームワークを何より大切にしています。",
            "仲間への信頼を重視しています。",
            "助け合いの精神を大事にしています。"
        ]},
        {"topic": "挑戦", "templates": [
            "新しいことに挑戦する姿勢を大事にしています。",
            "失敗を恐れない心を持ち続けたいと思っています。",
            "変化への適応を心がけています。",
            "野心的な目標に向かって進むことを大切にしています。"
        ]},
        {"topic": "心理的安全性", "templates": [
            "心理的安全性を大事にしています。",
            "透明性を重視しています。",
            "情報をオープンにすることを心がけています。",
            "率直な対話を大切にしています。"
        ]},
        {"topic": "顧客・品質", "templates": [
            "顧客第一の考え方を軸にしています。",
            "品質にこだわることを大切にしています。",
            "プロフェッショナルとしての責任を重視しています。",
            "ユーザー視点を常に意識しています。",
            "誠実であることを大切にしています。"
        ]},
        {"topic": "スピード", "templates": [
            "スピード感を持って動くことを心がけています。",
            "効率を追求することを心がけています。",
            "自律的に行動することを重視しています。",
            "無駄を排除することを大事にしています。"
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

# --- Data Generation Logic ---

def get_project_comment():
    # Use Combinatorial Generation for Variety
    parts = [INTROS, PROJ_SUBJECTS, PROJ_SOLUTIONS, PROJ_EFFECTS, CLOSINGS]
    return generate_combinatorial_sentence(parts)

def get_dev_env_comment():
    parts = [INTROS, DEV_SUBJECTS, DEV_SOLUTIONS, DEV_EFFECTS, CLOSINGS]
    return generate_combinatorial_sentence(parts)

def get_tech_quality_comment():
    parts = [INTROS, TECH_SUBJECTS, TECH_SOLUTIONS, TECH_EFFECTS, CLOSINGS]
    return generate_combinatorial_sentence(parts)

def get_value_comment_q1():
    """Q1: あなたが仕事をする上で、大切にしている価値観を教えてください"""
    # テーマからランダムに選択
    theme = random.choice(list(VALUES_THEMES_GROUPED.keys()))
    # そのテーマ内からランダムに文を選択
    return random.choice(VALUES_THEMES_GROUPED[theme])


def get_value_comment_q2():
    """Q2: その価値観を大切にするようになったきっかけは？"""
    trigger = random.choice(VALUES_EPISODE_TRIGGERS)
    situation = random.choice(VALUES_EPISODE_SITUATIONS)
    learning = random.choice(VALUES_EPISODE_LEARNINGS)
    return f"{trigger}{situation}{learning}"

def get_value_comment_q3(index=0):
    """Q3: 社内で共有されたら嬉しい価値観は？"""
    prefix = random.choice(Q3_PREFIXES) if random.random() > 0.3 else ""
    val = random.choice(VALUES_THEMES)
    tmpl = random.choice(Q3_TEMPLATES).format(val)
    suffix = random.choice(Q3_SUFFIXES) if random.random() > 0.3 else ""
    comment = f"{prefix}{tmpl} {suffix}".strip()
    return comment


DEPARTMENTS = ["SREチーム", "フロントエンド", "バックエンド", "モバイルアプリ", "QAチーム", "デザイン", "PdM", "データ分析"]

def generate_mixed_comments_list(count, category):
    """
    Generates a list of UNIQUE comments with balanced cluster distribution:
    - 5% Small Voice (Outliers) - Clear outliers that stand out
    - 80% Dense Clusters - BALANCED (each cluster gets roughly equal comments)
    - 15% General Noise - For diversity
    
    IMPORTANT: All comments are unique, creating distinct opinions within each cluster
    """
    n_small_voices = max(int(count * 0.05), 1)
    n_dense_clusters = int(count * 0.80)
    n_general = count - n_small_voices - n_dense_clusters
    
    comments = []
    seen = set()
    
    # Get generator function based on category
    gen_func = get_project_comment
    if category == "product": gen_func = get_tech_quality_comment 
    elif category == "welfare" or category == "dev_env": gen_func = get_dev_env_comment
    elif category == "tech": gen_func = get_tech_quality_comment
    elif category == "values": gen_func = get_value_comment_q3
    elif category == "values_episode": gen_func = get_value_comment_q2
    elif category == "values_theme": gen_func = get_value_comment_q1
    
    # 1. ADD SMALL VOICES (Rare outliers) - ensure uniqueness
    cat = category if category in SMALL_VOICES else "project"
    available_small_voices = SMALL_VOICES[cat].copy()
    random.shuffle(available_small_voices)
    
    for i in range(min(n_small_voices, len(available_small_voices))):
        comment = available_small_voices[i]
        if comment not in seen:
            comments.append(comment)
            seen.add(comment)
        
    # 2. ADD DENSE CLUSTERS - WITH BALANCED DISTRIBUTION
    cat = category if category in DENSE_CLUSTERS else "project"
    available_clusters = DENSE_CLUSTERS[cat]
    
    if available_clusters:
        # Create BALANCED distribution: each cluster gets roughly equal comments
        num_clusters = len(available_clusters)
        comments_per_cluster = n_dense_clusters // num_clusters
        remainder = n_dense_clusters % num_clusters
        
        # Assign comments to clusters evenly
        cluster_assignments = []
        for i, cluster in enumerate(available_clusters):
            # Give each cluster equal share, plus 1 extra for first 'remainder' clusters
            cluster_count = comments_per_cluster + (1 if i < remainder else 0)
            cluster_assignments.extend([cluster] * cluster_count)
        
        random.shuffle(cluster_assignments)
        
        # Generate UNIQUE comments from assigned clusters
        # Track which templates we've used from each cluster
        cluster_template_indices = {i: list(range(len(cluster["templates"]))) for i, cluster in enumerate(available_clusters)}
        for cluster_idx, cluster in enumerate(available_clusters):
            random.shuffle(cluster_template_indices[cluster_idx])
        
        for cluster in cluster_assignments[:n_dense_clusters]:
            cluster_idx = available_clusters.index(cluster)
            templates = cluster["templates"]
            
            # Try to get an unused template from this cluster
            max_attempts = 50
            for attempt in range(max_attempts):
                if cluster_template_indices[cluster_idx]:
                    # Use next template in shuffled order
                    template_idx = cluster_template_indices[cluster_idx].pop(0)
                    comment = templates[template_idx]
                    
                    # If we've exhausted templates, reshuffle and reuse with variation
                    if not cluster_template_indices[cluster_idx]:
                        cluster_template_indices[cluster_idx] = list(range(len(templates)))
                        random.shuffle(cluster_template_indices[cluster_idx])
                else:
                    # Fallback: pick random template
                    comment = random.choice(templates)
                
                # Add variation if duplicate
                if comment in seen:
                    # Skip this duplicate and try to generate a new one
                    continue
                
                if comment not in seen:
                    comments.append(comment)
                    seen.add(comment)
                    break
            else:
                # If still can't find unique after max attempts, generate from general function
                for _ in range(20):
                    comment = gen_func()
                    if comment not in seen:
                        comments.append(comment)
                        seen.add(comment)
                        break
    
    # 3. ADD GENERAL NOISE - ensure uniqueness
    attempts = 0
    max_attempts = n_general * 10
    while len(comments) < count and attempts < max_attempts:
        comment = gen_func()
        if comment not in seen:
            comments.append(comment)
            seen.add(comment)
        attempts += 1
    
    # Fill any remaining slots if we couldn't generate enough unique comments
    fill_attempts = 0
    max_fill_attempts = 1000
    while len(comments) < count and fill_attempts < max_fill_attempts:
        comment = gen_func()
        if comment not in seen:
            comments.append(comment)
            seen.add(comment)
        fill_attempts += 1
    
    # If still not enough after max attempts, allow duplicates
    while len(comments) < count:
        comments.append(gen_func())
    
    random.shuffle(comments)
    return comments[:count]

def generate_csv_files():
    # 1. Project Management
    print("Generating Project Management data...")
    # Apply "project" category logic to both columns roughly
    project_comments_1 = generate_mixed_comments_list(NUM_ROWS_OTHERS, "project")
    project_comments_2 = generate_mixed_comments_list(NUM_ROWS_OTHERS, "project")
    
    project_data = []
    for i in range(NUM_ROWS_OTHERS):
        project_data.append({
            "日時": generate_random_date(),
            "部署": random.choice(DEPARTMENTS),
            "プロセスへのコメント": project_comments_1[i],
            "会議へのコメント": project_comments_2[i]
        })
    pd.DataFrame(project_data).to_csv(os.path.join(OUTPUT_DIR, "project.csv"), index=False, encoding="utf-8-sig")

    # 2. Dev Environment
    print("Generating Dev Environment data...")
    dev_comments_1 = generate_mixed_comments_list(NUM_ROWS_OTHERS, "welfare") # Use welfare/dev_env category
    dev_comments_2 = generate_mixed_comments_list(NUM_ROWS_OTHERS, "welfare")

    dev_data = []
    for i in range(NUM_ROWS_OTHERS):
        dev_data.append({
            "日時": generate_random_date(),
            "部署": random.choice(DEPARTMENTS),
            "ハードウェアへのコメント": dev_comments_1[i],
            "ソフトウェアへのコメント": dev_comments_2[i]
        })
    pd.DataFrame(dev_data).to_csv(os.path.join(OUTPUT_DIR, "dev_env.csv"), index=False, encoding="utf-8-sig")

    # 3. Tech Quality
    print("Generating Tech Quality data...")
    tech_comments_1 = generate_mixed_comments_list(NUM_ROWS_OTHERS, "tech")
    tech_comments_2 = generate_mixed_comments_list(NUM_ROWS_OTHERS, "tech")

    tech_data = []
    for i in range(NUM_ROWS_OTHERS):
        tech_data.append({
            "日時": generate_random_date(),
            "部署": random.choice(DEPARTMENTS),
            "コードベースへのコメント": tech_comments_1[i],
            "テストへのコメント": tech_comments_2[i]
        })
    pd.DataFrame(tech_data).to_csv(os.path.join(OUTPUT_DIR, "tech_quality.csv"), index=False, encoding="utf-8-sig")

    # 4. Values (Large dataset)
    print("Generating Values data...")
    
    q1_list = generate_mixed_comments_list(NUM_ROWS_VALUES, "values_theme")
    q2_list = generate_mixed_comments_list(NUM_ROWS_VALUES, "values_episode")
    q3_list = generate_mixed_comments_list(NUM_ROWS_VALUES, "values")
    
    values_data = []
    for i in range(NUM_ROWS_VALUES):
        values_data.append({
            "日時": generate_random_date(),
            "大切にしている価値観": q1_list[i],  # Q1: あなたが仕事をする上で、大切にしている価値観を教えてください
            "きっかけのエピソード": q2_list[i],  # Q2: その価値観を大切にするようになったきっかけは？
            "共有したい価値観": q3_list[i]  # Q3: 社内で共有されたら嬉しい価値観は？
        })

    pd.DataFrame(values_data).to_csv(os.path.join(OUTPUT_DIR, "values.csv"), index=False, encoding="utf-8-sig")

    print(f"✅ Generated data: All files have {NUM_ROWS_VALUES} rows.")

# --- Main ---
if __name__ == "__main__":
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        print(f"Cleaned directory: {OUTPUT_DIR}")
    
    os.makedirs(OUTPUT_DIR)
    print(f"Created directory: {OUTPUT_DIR}")

    print("🚀 Starting engineer-focused data generation (Proposal Mode)...")
    
    generate_csv_files()

    print("\n✨ Data generation completed!")
