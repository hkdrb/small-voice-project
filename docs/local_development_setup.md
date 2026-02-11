# ローカル開発環境セットアップガイド (Local Development)

このガイドでは、**Docker** を使用して Small Voice Project の **ローカル開発環境** を構築する手順を説明します。
**エンジニアが手元のマシンで開発・テストを行うための手順** です。本番環境やデモ環境の構築には `production_deployment_guide.md` を参照してください。

Python や Node.js をローカルマシンにインストールする必要はなく、環境差異のないクリーンな開発環境を利用できます。

## 前提条件
- **Docker**: 最新版のインストール
- **Docker Compose**: 最新版 (Docker Desktopに含まれています)
- **Git**
- **Google Account** (Gemini APIキー取得用)

## セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd small-voice-project
```

### 2. 環境設定 (.env)
プロジェクトルートに `.env` ファイルを作成し、APIキーを設定してください。

```ini
# (必須) AI / Google Gemini
GEMINI_API_KEY=your_api_key_here

# AIモデル設定（タスク別に最適なモデルを使い分け）
GEMINI_MODEL_NAME=gemini-2.5-flash
GEMINI_MODEL_NAME_THINKING=gemini-2.5-flash
GEMINI_MODEL_NAME_LIGHT=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL_NAME=models/text-embedding-004

# 開発用はコンテナ内のPostgreSQLを使用するため、DATABASE_URLの設定は不要です (docker-compose.yml内で自動設定されます)。
# 初期パスワードの固定設定 (任意)
INITIAL_USER_PASSWORD=admin

# メール機能について
# ローカル環境(デフォルト)では、メールは実際には送信されず、
# バックエンドのコンソールログに内容が出力されます。
# 本番環境(GCE等)で Brevo 等のSMTP設定を行うことで、実際のメール送信が有効になります。
```

## アプリケーションの実行

以下のコマンドを実行するだけで、バックエンド、フロントエンド、データベースが一括して起動します。
初回起動時はイメージのビルドが行われるため、数分かかります。

```bash
docker-compose -f docker-compose.dev.yml up --build
```
正常に起動すると、以下のURLでアクセスできます。

- **Frontend**: http://localhost:3000 (ホットリロード有効)
- **Backend API**: http://localhost:8000 (自動リロード有効)
- **Database**: `localhost:5433` (ホスト側からもアクセス可能)

停止するには `Ctrl+C` を押すか、別のターミナルで以下を実行します。
```bash
docker-compose -f docker-compose.dev.yml down
```

## 開発ツール・コマンド

データ生成やLintなどのコマンドは、コンテナ内で実行します。`docker compose exec` を使用するか、コンテナのシェルに入って実行してください。

### テストデータの生成
分析機能のテスト用に、大量のダミーデータを生成します。

```bash
# Backendコンテナ内でスクリプトを実行
docker-compose -f docker-compose.dev.yml exec backend python scripts/generate_test_data.py
```
`outputs/test_data/` 配下に分析用CSVが生成されます。

### データベースのリセット (Re-seeding)
データベースを初期状態に戻す、またはダミーデータを再投入する場合に使用します。

```bash
# 1. データベースを完全リセット (全テーブル削除)
# ⚠️ 注意: ローカルの全てのデータが消去されます！
docker-compose -f docker-compose.dev.yml exec backend python scripts/reset_db_clean.py

# 2. 初期セットアップ (テーブル作成 + 初期ユーザー/データ投入)
# パターンA: 初期ユーザーのみ作成 (データは空)
# ログイン確認や、手動でデータを入れたい場合に使用します。
docker-compose -f docker-compose.dev.yml exec backend python scripts/seed_db.py --init-users

# パターンB: デモ用フルセット投入 (ユーザー + セッション + コメント一括)
# すぐにデモを行いたい場合に使用します（Legacy: --with-dummy-data）
docker-compose -f docker-compose.dev.yml exec backend python scripts/seed_db.py --with-dummy-data

# パターンC: 個別にデータ投入 (ステップ実行)
# 1. ダミーセッション(分析データ枠)のみ作成
docker-compose -f docker-compose.dev.yml exec backend python scripts/seed_db.py --seed-sessions

# 2. 既存セッションにコメントを追加 (200件/回)
# (既にセッションが存在する場合のみ実行可能。何度でも実行してコメントを増やせます)
docker-compose -f docker-compose.dev.yml exec backend python scripts/seed_db.py --seed-comments
```

### 議論コメントのCSVインポート (Web UI)
コマンドライン以外に、管理画面（Web UI）からもテスト用コメントを投入できます。
特定の議論スレッドに対して、自作のCSVデータを投入したい場合に便利です。
- URL: `http://localhost:3000/admin/csv-import`

```

### データベースへの接続
ホストマシンのクライアントツール（TablePlus, DBeaver, pgAdminなど）からデータベースに接続する場合は、以下の情報を使用してください。

- **Host**: `localhost` (または `127.0.0.1`)
- **Port**: `5433`
- **User**: `postgres`
- **Password**: `postgres`
- **Database**: `voice_insight_db`

### Linting / Formatting
コードをコミットする前に実行してください。

**Backend (Python)**
```bash
docker-compose -f docker-compose.dev.yml exec backend flake8 .
```


**Frontend (TypeScript/JavaScript)**
```bash
docker-compose -f docker-compose.dev.yml exec frontend npm run lint
```

## 🔑 デモ用ログイン情報 (初期設定)

初回起動時に以下のユーザーが自動作成されます。パスワードはログ出力を確認するか、`.env` で `INITIAL_***_PASSWORD` を設定してください。

| 役割 | Email | 説明 |
| --- | --- | --- |
| **System Admin** | `system@example.com` | システム管理者 |
| **Org Admin** | `admin@example.com` | 組織管理者 |
| **User** | `user1@example.com` | 一般ユーザー |

---

## 手動セットアップ (Dockerを使用しない場合)
Dockerを使用せず、ローカルマシンに直接環境を構築する場合の手順です。

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
# AIモデル設定
GEMINI_MODEL_NAME=gemini-2.0-flash
GEMINI_MODEL_NAME_THINKING=gemini-1.5-pro
GEMINI_MODEL_NAME_LIGHT=gemini-1.5-flash
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
