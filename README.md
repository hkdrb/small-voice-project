# Small Voice 🗣️

**組織内の「小さな声」を聴き、課題解決を促進するAI搭載型ブロードリスニングシステム**

## 🔍 ブロードリスニングとは
「ブロードリスニング」とは、一方的な情報発信である「ブロードキャスト」と対をなす概念です。個々の異なる意見を収集・分析することで、組織や社会全体の傾向、あるいは感覚的には捉えきれていない「不可視の課題」を俯瞰的に把握する手法を指します。

単なるアンケートに留まらず、大多数の意見に埋もれがちな**「外れ値（Small Voice）」にもリーチできる点**が大きな強みです。ブロードキャストによって生じがちな情報の偏りを是正し、統計的な分析によって浮き彫りになった課題に対し、対話を通じて異なる意見の「架け橋」を見出したり、意思決定の質を高めたりすることを目的としています。

## 💡 Small Voice（外れ値）の救い上げ
本システムは、統計的な分析の過程で切り捨てられがちな「少数の意見」を、組織の重要な兆しとして扱います。大多数の声に埋もれた外れ値を独立したトピックとして抽出・保持することで、潜在的なリスクや革新的なアイデアを確実に対話のテーブルへと導きます。

## 🚀 主な機能

### データ収集と集計
- **柔軟なインプット**: CSVインポートによる一括登録、またはシステム内でのフォーム作成・集計に対応。
- **メンバーからの申請**: 管理者側からの収集だけでなく、メンバーが自発的にフォームから申請・投稿できるボトムアップな設計。

### シームレスな広聴と対話空間の設計
収集した声を孤立させず、解決まで一気通貫で繋げる「シームレス・ブロードリスニング」を実現します。
- **クラスタリング**: 収集された多種多様な意見をAI（Sentence Transformers & Gemini）が分類・構造化。
- **課題リスト**: クラスタリング結果に基づき、取り組むべき課題を抽出・リスト化。
- **課題ごとの議論チャット**: 各課題に専用のチャット空間を生成し、具体的な対話を促進。
- **議論のAI分析**: 対話の内容をAIが分析し、構造的な理解や意思決定をサポート。アクションプランの自動生成も行います。

### 柔軟な組織管理（マルチテナント構成）
- **多重所属に対応**: システム内のユーザーは複数の組織（部署や案件）に同時に属することが可能。
- **実態に即した管理**: 部署単位だけでなく、参画案件やプロジェクト単位での柔軟な管理・運用を実現します。
- **セキュアな分離**: データは組織ごとに論理的に分離され、安心して利用できます。

### 3つの権限設計
本システムでは以下の3つの役割（ロール）を提供し、スムーズな運用をサポートします。

| 役割 | システム上の表記 | 権限範囲 |
| :--- | :--- | :--- |
| **システム管理者** | `System Admin` | システム全体の統括。組織の作成や全ユーザーの管理権限を持ちます。 |
| **組織管理者** | `Org Admin` | 所属する組織内におけるフォーム作成や管理、分析の実行や分析結果の管理を行います。 |
| **一般ユーザー** | `Member` / `User` | フォームへの回答や申請、分析結果の閲覧、議論（チャット）への参加が可能です。 |

---

## 🛠️ 技術スタック


| Category | Tech Stack |
| --- | --- |
| **Frontend** | Next.js 15 (App Router), Tailwind CSS v4, Lucide React, Plotly.js |
| **Backend** | FastAPI (Python), SQLAlchemy, Pydantic |
| **AI / LLM** | **Google Gemini 2.0 Flash** (Main), **Gemini 1.5 Pro** (Deep Analysis) |
| **Machine Learning** | **Sentence Transformers** (multilingual-e5-large), **HDBSCAN**, UMAP, PyTorch |
| **Database** | PostgreSQL (Production) / SQLite (Dev) |
| **Infra** | Docker Native, Vercel/Render ready |

## 📦 インストールと実行手順


本プロジェクトは **Docker** での動作を推奨しています。
詳細なセットアップ手順や、手動でのインストール方法は [ローカル開発環境セットアップガイド](docs/local_development_setup.md) を参照してください。

### Quick Start (Docker)
```bash
git clone https://github.com/koderahayato/small-voice-project.git
cd small-voice-project
docker-compose -f docker-compose.dev.yml up --build
```
ブラウザで `http://localhost:3000` にアクセスしてください。

初期ログイン情報は [こちら](docs/local_development_setup.md#%E3%83%87%E3%83%A2%E7%94%A8%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3%E6%83%85%E5%A0%B1-%E5%88%9D%E6%9C%9F%E8%A8%AD%E5%AE%9A) を参照してください。


## 📚 ドキュメント
- [システムアーキテクチャ詳細](docs/architecture.md)
- [データベース設計](docs/database.md)
- [セットアップガイド (Local Development)](docs/local_development_setup.md): ローカル開発環境の構築手順
- [デプロイメントガイド (Production/Demo)](docs/production_deployment_guide.md): 本番サーバーへのデプロイ・運用手順 (GCE)
- [本番DB接続ガイド](docs/db_connection_guide.md): ローカルのDBクライアントツールから本番DBに接続する手順
- [ユーザー利用マニュアル](docs/user_manual.md)