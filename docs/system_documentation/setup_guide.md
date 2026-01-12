# セットアップ & 運用ガイド

## 前提条件
- **Backend / DB**:
    - Python 3.10 以上
    - データベース:
        - **開発用 (デフォルト)**: SQLite (設定不要)
        - **本番用 (推奨)**: PostgreSQL 14 以上
    - Google Account (Gemini APIキー取得用)
- **Frontend**:
    - Node.js 18.17 以上 (推奨: LTS)
    - npm, yarn, または pnpm
- **Tools**:
    - Git

## インストール手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd small-voice-project
```

### 2. Backend (FastAPI) のセットアップ

#### 仮想環境の作成と有効化
```bash
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

#### 依存ライブラリのインストール
```bash
pip install -r requirements.txt
```

#### 環境設定 (.env)
プロジェクトルートに `.env` ファイルを作成し、以下の情報を設定してください。

```ini
# (必須) AI / Google Gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# (任意) PostgreSQLを使用する場合。未設定時はSQLite (backend/voice_insight.db) が使用されます。
# DATABASE_URL=postgresql://user:password@localhost/voice_insight_db

# (推奨) 初期ユーザーのパスワード設定
# 未設定の場合、初回起動時にランダムな強力なパスワードが生成され、ログに出力されます。
INITIAL_SYSTEM_PASSWORD=your_password
INITIAL_ADMIN_PASSWORD=your_password
INITIAL_USER_PASSWORD=your_password
```

#### データベースの初期化
サーバー起動時に自動的に初期化 (`init_db`) が行われますが、PostgreSQLを使用する場合は事前にデータベースを作成しておく必要があります。

```bash
# PostgreSQLを使用する場合のみ
createdb voice_insight_db
```

### 3. Frontend (Next.js) のセットアップ

```bash
cd frontend

# パッケージインストール
npm install
```

## アプリケーションの実行

### 1. Backendの起動
```bash
# プロジェクトルート (または venv有効化状態) で
cd backend
uvicorn main:app --reload --port 8000
```
APIサーバーが `http://localhost:8000` で起動します。
初回起動時にデータベースがない場合は、自動的に作成・シードデータの投入が行われます。

### 2. Frontendの起動
別のターミナルを開き、Frontendディレクトリで実行します。
```bash
cd frontend
npm run dev
```
ブラウザで `http://localhost:3000` にアクセスしてください。

### 3. 初期アカウント
`.env` ファイルの設定に基づき、以下の初期アカウントが作成されます。
**パスワードを設定していない場合、Backendの起動ログを確認してください。**

**デフォルト設定 (推奨):**
- **システム管理者**: `system@example.com`
- **組織管理者**: `admin@example.com`
- **一般ユーザー**: `user1@example.com`

## 運用・開発ガイド

### テストデータの生成
分析用のデモデータ（CSV）を生成するには以下を実行します。エンジニア組織向けの多様なフィードバックデータ（1000件以上の価値観データなど）が生成されます。
```bash
python scripts/generate_test_data.py
```
`outputs/test_data/` 配下に分析用CSVが生成されます。Frontendの「設定」または「インポート」画面から読み込むことができます。

### ダミーデータの一括投入 (Seeding)
以下のコマンドで、初期ユーザー(System Admin, Org Admin, 10名の一般ユーザー)を作成します。
※ `main.py` 起動時にも実行されますが、手動でリセットしたい場合などに使用します。

```bash
# 基本: 初期ユーザーと組織のみ作成
python scripts/seed_db.py
```

さらに、開発用の分析セッションデータや数百件のコメントを追加したい場合は、オプションを指定してください。
```bash
# オプション: ダミーデータ(セッション・コメント)も含めて投入
python scripts/seed_db.py --with-dummy-data
```

### データベースのリセット (完全初期化)
開発環境などでデータベースを完全にクリーンな状態に戻し、初期データのみを投入し直したい場合は以下を実行します。
```bash
# 全テーブルを削除
python scripts/reset_db_clean.py

# 初期ユーザーのみ再作成
python scripts/seed_db.py
```
**注意**: 全ての既存データが削除されます。

### パスワードリセット (開発環境)
メール送信機能はモック化されています。パスワードリセットをリクエストすると、**Backend側のコンソールログ**にリセットトークン付きのURLが出力されます。
ログ内の `http://localhost:3000/forgot-password?token=...` のようなURLをコピーしてアクセスしてください。

### Linting / Formatting
- **Backend (Python)**: `flake8 .`
- **Frontend (TS/JS)**: `npm run lint`
