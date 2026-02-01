
import random
import json
import datetime
from typing import List, Dict, Any

# --- Sentence Parts Definitions (Proposal Oriented - Synced with generate_test_data.py) ---

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
            "他部署の貢献を見える化する社内報の発行を提案します。"
        ]},
        {"topic": "挑戦の奨励", "templates": [
            "業務時間の10%を新しい技術検証に使ってよいルールを導入すべきです。",
            "失敗しても評価が下がらないことを明文化した『チャレンジ評価制度』を提案します。", 
            "新規事業コンテストを開催し、ボトムアップでアイデアを募集しましょう。",
            "ハッカソンを定期開催し、イノベーションの種を撒く活動を推奨します。",
            "新しいツールの導入稟議を簡素化し、スピード感を持って試せる環境にしてください。"
        ]},
        {"topic": "心理的安全性向上", "templates": [
            "無記名で経営陣に質問できるQ&Aセッションの定期開催を提案します。",
            "『Yes, And』の精神で、反対意見もまずは受け止めるルールを会議に導入しましょう。",
            "若手社員がメンター以外にも相談できる斜めの関係作りを支援する制度が必要です。",
            "心理的安全性を測るサーベイを毎月実施し、改善サイクルを回すべきです。",
            "ミスをした人を責めるのではなく、システムの問題として捉える『ポストモーテム』を徹底しましょう。"
        ]},
        {"topic": "顧客志向の徹底", "templates": [
            "開発者も定期的にカスタマーサポート業務を体験し、顧客の声を直接聞く研修を提案します。",
            "ドッグフーディングを義務化し、自分たちが一番のヘビーユーザーになるべきです。", 
            "NPS（顧客推奨度）を全社員の共通KPIに設定することを提案します。",
            "顧客インタビューの動画をランチタイムに上映し、ユーザー像を共有しましょう。",
            "ペルソナシートをオフィスの目立つ場所に貼り出し、常に顧客を意識させたいです。"
        ]},
        {"topic": "スピード重視", "templates": [
            "承認プロセスを最大2段階までに減らし、意思決定スピードを上げる提案です。",
            "完璧を目指してリリースを遅らせるより、MVPで早く市場に出す方針に転換すべきです。", 
            "会議での持ち帰り検討を禁止し、その場で決断するルールを導入しませんか。",
            "アジャイル開発の講師を招き、本格的なスクラム導入を検討すべきです。",
            "稟議書を廃止し、Slackでのスタンプ承認で進められる範囲を広げましょう。"
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
        return lambda: generate_sentence([INTROS, PROJ_SUBJECTS, PROJ_SOLUTIONS, PROJ_EFFECTS, CLOSINGS])
    elif category == 'welfare' or category == 'dev_env':
        return lambda: generate_sentence([INTROS, DEV_SUBJECTS, DEV_SOLUTIONS, DEV_EFFECTS, CLOSINGS])
    elif category == 'tech' or category == 'tech_quality':
        return lambda: generate_sentence([INTROS, TECH_SUBJECTS, TECH_SOLUTIONS, TECH_EFFECTS, CLOSINGS])
    elif category == 'values':
         # Since VALUES_THEMES etc are simplified in generate_test_data, 
         # I will just use the Dense Cluster templates here which are high quality proposals,
         # or use a simplified generator if needed.
         # For simplicity and quality, I'll use the dense cluster randomizer for 'values' general generation
         # or bring back the Q3 style.
         # Actually generate_test_data.py uses get_value_comment_q3.
         
         # To simplify this mock generator which doesn't need perfect parity,
         # I'll just use the topic clusters as they are rich now.
         return lambda: get_dense_cluster_comment('values')
    else:
        # Default analysis
        return lambda: generate_sentence([INTROS, PROJ_SUBJECTS, PROJ_SOLUTIONS, PROJ_EFFECTS, CLOSINGS])

def get_value_comment_q3():
    return get_dense_cluster_comment('values')

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
    elif any(w in theme for w in ["価値観", "value", "culture"]): category = "values"
    
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
            "description": f"「{topic}」に関する具体的な提案が多数（{random.randint(5, 15)}件）寄せられています。実現可能性の高い解決策が含まれています。",
            "urgency": urgencies[i % len(urgencies)],
            "category": "Organizational" if "制度" in topic or "会議" in topic or "文化" in topic or "称賛" in topic or "心理" in topic or "挑戦" in topic or "顧客" in topic or "スピード" in topic else "Technical"
        })
        
    # Add one small voice issue
    report_issues.append({
        "title": "【要注意】深刻な懸念（Small Voice）",
        "description": "少数ですが、コンプライアンスやハラスメントに関わる深刻な指摘が存在します。早急な事実確認が推奨されます。",
        "urgency": "high",
        "category": "organizational"
    })

    return results, json.dumps(report_issues, ensure_ascii=False)
