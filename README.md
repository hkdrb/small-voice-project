# Small Voice 🗣️

**組織内の「小さな声」を聴き、課題解決を促進するAI搭載型ブロードリスニングシステム**

> **"多数決で失われる革新の種を、AIが見つけ出す。"**
> 
> Small Voice は、組織内に埋もれがちな「少数だが重要な意見」を可視化し、具体的なアクションプランに変えるための次世代型社内システムです。

---

## 💡 背景とコンセプト
多くの組織分析ツールは、意見を「平均化」し、多数派の声を優先します。しかし、**組織のリスク予兆やイノベーションのヒントは、往々にして「外れ値（小さな声）」に潜んでいます。**

Small Voice は、**埋め込みモデル (Sentence Transformers)** と **生成的AI (Gemini 2.0 Flash Thinking)** を組み合わせたハイブリッドAI分析により、「サイレントマジョリティ」だけでなく「ノイジーマイノリティ」でもない、**「真に価値ある小さな声」** を救い上げます。

## 🚀 主な機能

### 1. AI分析 & インサイト抽出
多数決では切り捨てられる意見を、以下のロジックで確実にピックアップします。
- **ハイブリッド分析**: `Sentence Transformers` による意味ベクトル化と `K-Means/UMAP` で意見の分布を構造化し、`Google Gemini 2.0 Flash Thinking` が深層分析を行います。
- **リスク情報の強制昇格**: バグやエラーなど、システム品質に関わる報告は、たとえ1件でも「重要課題」として優先的に抽出します。
- **ユニーク提案の発掘**: 数は少なくても、質的に優れた独自の改善案を「Notable Ideas」として別枠でレポーティングします。

### 2. 課題の可視化 (Visualization)
- **2次元セマンティックマップ**: `UMAP` による意味空間の2次元投影で、意見の類似性をマップ上にプロット。
- **直感的な操作**: マップをズーム・パンして、気になった意見をその場で詳細確認できます。

### 3. アンケート作成・収集
- **フォーム作成・申請**:
    - **管理者**: 自由にフォームを作成・公開可能。
    - **一般メンバー**: フォームの「作成申請」が可能。管理者による承認プロセスを経て公開されます。
- **データ収集**: システム内で回答を収集し、直接分析パイプラインへ連携。
- **CSVインポート**: 外部ツールデータを「フォーム」として取り込み、統一的な分析フローで処理。

### 4. コミュニティによる解決 (Community Action)
課題を見つけるだけでは終わりません。
- **みんなの提案チャット**: AIが提示した課題に対し、その場で解決策を議論できるスレッド形式の掲示板。
- **アクションプラン生成**: 議論の内容をAIが再度分析し、具体的な実行計画（アクションプラン）を自動生成します。

### 5. 堅牢なプラットフォーム
- **マルチテナント対応**: 組織ごとに完全に分離されたデータ環境。
- **セキュアな認証**: HttpOnly Cookie運用、Bcryptパスワードハッシュ化など、エンタープライズレベルのセキュリティ標準に準拠。

## 🛠️ 技術スタック

| Category | Tech Stack |
| --- | --- |
| **Frontend** | Next.js (App Router), Tailwind CSS, Lucide React, Plotly.js |
| **Backend** | FastAPI (Python), SQLAlchemy, Pydantic |
| **AI / LLM** | **Google Gemini 2.0 Flash Thinking Exp** (深層分析), **Gemini 2.0 Flash Exp** (軽量タスク) |
| **Machine Learning** | **Sentence Transformers** (intfloat/multilingual-e5-large), **HDBSCAN** (Density-based Clustering), UMAP, PyTorch |
| **Database** | PostgreSQL (Production) / SQLite (Dev) |
| **Infra** | Vercel/Render ready |

## 📦 インストールと実行手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/koderahayato/small-voice-project.git
cd small-voice-project
```

### 2. バックエンドのセットアップ
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` ファイルを作成し、Gemini APIキーとモデル設定を行ってください。
```ini
GEMINI_API_KEY=your_api_key_here
# AIモデル設定 (タスク別に最適なモデルを使い分け)
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
GEMINI_MODEL_NAME_THINKING=gemini-2.0-flash-thinking-exp
GEMINI_MODEL_NAME_LIGHT=gemini-2.0-flash-exp
# 開発用デフォルトDB設定
DATABASE_URL=sqlite:///voice_insight.db
```

サーバー起動:
```bash
cd backend
uvicorn main:app --reload --port 8000
```
※ 初回起動時にDBとデフォルトユーザーが自動生成されます。

### 3. フロントエンドのセットアップ
```bash
cd frontend
npm install
npm run dev
```
ブラウザで `http://localhost:3000` にアクセスしてください。

## 🔑 デモ用ログイン情報 (初期設定)

初回起動時に以下のユーザーが自動作成されます。パスワードはログ出力を確認するか、`.env` で `INITIAL_***_PASSWORD` を設定してください。

| 役割 | Email | 説明 |
| --- | --- | --- |
| **System Admin** | `system@example.com` | 全体管理者。新しい組織の作成が可能。 |
| **Org Admin** | `admin@example.com` | 組織管理者。フォーム作成や分析実行が可能。 |
| **User** | `user1@example.com` | 一般ユーザー。アンケート回答やチャット参加が可能。 |

## 📚 ドキュメント
- [システムアーキテクチャ詳細](docs/architecture.md)
- [データベース設計](docs/database.md)
- [セットアップガイド (Local Development)](docs/local_development_setup.md): ローカル開発環境の構築手順
- [デプロイメントガイド (Production/Demo)](docs/production_deployment_guide.md): 本番サーバーへのデプロイ・運用手順 (GCE)
- [本番DB接続ガイド](docs/db_connection_guide.md): ローカルのDBクライアントツールから本番DBに接続する手順
- [ユーザー利用マニュアル](docs/user_manual.md)