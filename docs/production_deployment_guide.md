# 本番環境デプロイメントガイド

Google Compute Engine (GCE) を使用した Small Voice Project の本番デプロイ手順です。

---

## 前提条件

- Google Cloud Platform アカウント（有効な請求先設定済み）
- ドメイン取得済み（例：Google Domains、お名前.com）

---

## 1. GCEインフラ構築

### 1.1 静的IPアドレスの予約

1. [GCP Console](https://console.cloud.google.com/) にログイン
2. **「VPC ネットワーク」→「IP アドレス」** を開く
3. **「外部静的 IP アドレスを予約」** をクリック
4. 設定：
   - **名前**: `small-voice-ip`
   - **リージョン**: `asia-northeast1`（東京）
5. **割り当てられたIPアドレスをメモ**

### 1.2 VM インスタンスの作成

1. **「Compute Engine」→「VM インスタンス」→「インスタンスを作成」**
2. 以下の設定で作成：

| 項目 | 設定値 |
|------|--------|
| 名前 | `small-voice-server` |
| リージョン | `asia-northeast1`（東京）|
| マシンタイプ | `e2-small`（推奨）または `e2-micro` |
| ブートディスク | Ubuntu 22.04 LTS、30GB |
| ファイアウォール | ✓ HTTPトラフィックを許可<br>✓ HTTPSトラフィックを許可 |
| 外部IP | 手順1.1で予約したIP |

3. **「作成」** をクリック

### 1.3 DNS設定

#### Google Cloud DNSを使用する場合

1. **「Cloud DNS」** → **「ゾーンを作成」**
2. 設定：
   - **ゾーンの種類**: 一般公開
   - **DNS名**: あなたのドメイン（例：`example.com`）
3. **Aレコードを追加**：
   - DNS名: 空欄
   - タイプ: A
   - IPv4アドレス: 手順1.1のIP
4. **NSレコード4つをメモ**（例：`ns-cloud-a1.googledomains.com.`）
5. **ドメインレジストラでネームサーバーを変更**：
   - お名前.comの場合：「ネームサーバー設定」→「他のネームサーバーを利用」
   - メモした4つのNSレコードを入力

DNS反映には数分〜数時間かかります。

---

## 2. サーバー初期設定

### 2.1 SSH接続

1. GCP Console → **「VM インスタンス」**
2. `small-voice-server` の **「SSH」** ボタンをクリック

### 2.2 Dockerのインストール

以下のコマンドを一括実行して、Docker環境をセットアップします。

```bash
# 必要なパッケージのインストールとGPGキーの追加
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release git
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Dockerリポジトリの追加とインストール
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 現在のユーザーにDocker権限を付与
sudo usermod -aG docker $USER
```

### 2.3 ログアウトして再接続

Docker権限を反映するため、一度ログアウトして再接続してください：

```bash
exit
```

GCP Consoleで再度「SSH」ボタンをクリックして接続します。

---

## 3. アプリケーションデプロイ

### 3.1 リポジトリのクローン

```bash
git clone https://github.com/hkdrb/small-voice-project.git
cd small-voice-project
```

### 3.2 環境変数の設定

```bash
cp .env.example .env
nano .env
```

以下の項目を設定してください：

```ini
# Gemini API（Google AI Studioで取得）
GEMINI_API_KEY=your_actual_gemini_api_key

# AIモデル設定（タスク別に最適なモデルを使い分け）
GEMINI_MODEL_NAME=gemini-2.5-flash
GEMINI_MODEL_NAME_THINKING=gemini-2.5-flash
GEMINI_MODEL_NAME_LIGHT=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL_NAME=models/text-embedding-004

# 初期ユーザーのパスワード（安全なパスワードに変更してください）
INITIAL_SYSTEM_PASSWORD=change_this_system_password
INITIAL_ADMIN_PASSWORD=change_this_admin_password
INITIAL_USER_PASSWORD=change_this_user_password

# メール送信設定（Brevoを使用）
ENVIRONMENT=production
SMTP_SERVER=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your_brevo_login_email
SMTP_PASSWORD=your_brevo_smtp_key
SENDER_EMAIL=noreply@your-domain.com
SENDER_NAME="Small Voice"
```

#### Brevoのセットアップ方法

1. [Brevo](https://www.brevo.com/)でアカウント作成（無料プラン: 1日300通まで）
2. ログイン後、右上のアカウント名 → **「SMTP & API」** をクリック
3. **「SMTP」** タブ → **「新しいSMTPキーを作成」** をクリック
4. キー名を入力（例：`small-voice-prod`）して **「生成」**
5. 表示されたSMTPキーをコピー（再表示不可のため注意）
6. 以下の情報を`.env`に設定：
   - `SMTP_USERNAME`: Brevoのログインメールアドレス
   - `SMTP_PASSWORD`: 生成したSMTPキー

保存して終了（`Ctrl+X` → `Y` → `Enter`）

### 3.3 SSL証明書の取得

```bash
# Certbotのインストール
sudo apt-get install -y certbot

# 証明書の取得（your-domain.comを実際のドメインに置き換え）
sudo certbot certonly --standalone -d your-domain.com
```

> **注意**: メールアドレスの入力を求められた場合は入力してください。
> 証明書は `/etc/letsencrypt/live/your-domain.com/` に保存されます。

### 3.4 Nginx設定ファイルの編集

```bash
nano nginx/default.conf
```

以下のように編集（`your-domain.com`を実際のドメインに置き換え）：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    add_header X-Robots-Tag "noindex, nofollow, nosnippet, noarchive";

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3.5 docker-compose.prod.ymlの確認

`docker-compose.prod.yml` を開いて、以下の設定が含まれているか確認してください：

```bash
cat docker-compose.prod.yml
```

**nginxセクション**に以下が含まれていることを確認：

```yaml
nginx:
  ports:
    - "80:80"
    - "443:443"  # HTTPS用ポート
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro  # SSL証明書マウント
```

もし含まれていない場合は、`nano docker-compose.prod.yml` で編集してください。

### 3.6 アプリケーション起動

```bash
docker compose -f docker-compose.prod.yml up -d
```

初回起動は数分かかります。以下で進捗を確認できます：

```bash
docker compose -f docker-compose.prod.yml logs -f
```

すべてのコンテナが起動したら `Ctrl+C` で終了します。

### 3.7 動作確認

ブラウザで `https://your-domain.com` にアクセスし、以下を確認：

- ✅ HTTPSで接続できる（🔒マークが表示される）
- ✅ ログイン画面が表示される

---

## 4. アプリケーション更新

コードを更新した際は、以下の手順で本番環境に反映します。

### 4.1 更新スクリプトの実行

1. サーバーにSSH接続します。
2. 以下のコマンドを実行します。

```bash
cd small-voice-project
./scripts/deploy_prod.sh
```

このスクリプトは自動で以下の処理を行い、本番環境を最新の状態に更新します：
- ✅ 最新のコードを取得 (`git pull`)
- ✅ ディスク容量の確保 (`docker system prune`)
- ✅ 最新のDockerイメージを取得 (`docker compose pull`)
- ✅ デプロイバージョン情報の記録
- ✅ サービスの再起動 (`docker compose up -d`)

### 4.2 デプロイ反映の確認

APIのルートエンドポイントにアクセスすることで、現在デプロイされているバージョンを確認できます。

```bash
curl https://small-voice.xyz/api/
```

レスポンス例:
```json
{
  "message": "SmallVoice API is running",
  "version": "85f3a98",
  "deployed_at": "2026-02-01 12:45:00"
}
```

---

## 5. 運用管理

### コンテナ状態確認

```bash
docker compose -f docker-compose.prod.yml ps
```

### デモ環境のデータリセット

> ⚠️ **警告**: 本番環境では実行しないでください。全データが削除されます。

ローカル開発環境と同様の手順で、本番環境（デモ環境）のデータをリセットまたは生成できます。

```bash
# 1. データベースを完全リセット (全テーブル削除)
docker compose -f docker-compose.prod.yml exec backend python scripts/reset_db_clean.py

# 2. 初期セットアップ (テーブル作成 + 初期ユーザー/データ投入)

# パターンA: 初期ユーザーのみ作成 (データは空)
# ログイン確認や、手動でデータを入れたい場合に使用します。
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_db.py --init-users

# パターンB: 既存セッションにコメントを追加 (200件/回)
# (既にセッションが存在する場合のみ実行可能)
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_db.py --seed-comments

# パターンC: 雑談掲示板のテストデータを生成 (100件の投稿と返信)
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_db.py --seed-casual
```

### 議論コメントのCSVインポート (管理画面)
本番環境でも、特定の議論スレッドに対してCSVファイルからコメントを一括インポート可能です。
URLを直接叩くことでアクセスできます。

- **URL**: `https://your-domain.com/admin/csv-import`
  - (`your-domain.com` は実際のドメインに置き換えてください)
- **権限**: システム管理者 (`system_admin`) のみ実行可能
- **用途**: デモデータの投入や、外部システムからのデータ移行など

---

## 6. データベース接続

ローカルMacのDBクライアントツール（TablePlus、DBeaver等）から本番環境（GCE）のPostgreSQLデータベースに安全に接続する方法です。

### 前提条件

- Google Cloud Platform アカウント（本番環境へのアクセス権限）
- DBクライアントツール（TablePlus、DBeaver、psql等）
- gcloud CLIがインストールされていること

### 6.1 gcloud CLIのセットアップ

まだインストールしていない場合は、Homebrew等でインストールし、ログイン設定を行ってください。

```bash
brew install google-cloud-sdk
gcloud init
```
※ `gcloud init` でプロジェクトとリージョン（asia-northeast1）を選択します。

### 6.2 SSHトンネルの作成

ローカルMacのターミナルで以下を実行し、SSHトンネル（ポートフォワーディング）を作成します。

```bash
gcloud compute ssh small-voice-server \
  --zone=asia-northeast1-c \
  --tunnel-through-iap \
  -- -L 5434:localhost:5432 -N
```

**注意**:
- このコマンドは接続を維持し続けます。**ターミナルウィンドウを閉じないでください**。
- ポート `5434` を使用してローカルから接続します。

### 6.3 DBクライアントツールで接続

新しいターミナルタブやDBクライアントツールを開き、以下の情報で接続します。

| 項目 | 設定値 |
|------|-----|
| **ホスト** | `localhost` |
| **ポート** | `5434` |
| **ユーザー名** | `postgres` |
| **パスワード** | `postgres` |
| **データベース名** | `small_voice_db` |

※ パスワードは `docker-compose.prod.yml` の設定に準じます（デフォルトは `postgres`）。

### 6.4 接続の終了

作業が終わったら、SSHトンネルを実行しているターミナルで `Ctrl+C` を押して切断します。

---

## 付録

### コスト目安（東京リージョン）

| 項目 | 月額コスト |
|------|-----------|
| e2-small VM（推奨） | 約 $14 |
| e2-micro VM（最小） | 約 $8 |
| ディスク 30GB | 約 $4 |
| **合計** | **$12-18** |

> 💡 **節約Tips**:
> - VMインスタンスを「停止」している間は、CPU/メモリのリソース料金（VM料金）は発生しません。ただし、**ディスク料金（30GB分）と固定IPアドレス料金は継続して発生**します。
> - 米国リージョン（us-central1等）のe2-microは無料枠対象です。

### 参考リンク

- [Google Cloud DNS ドキュメント](https://cloud.google.com/dns)
- [Brevo（旧Sendinblue）](https://www.brevo.com/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Docker Compose リファレンス](https://docs.docker.com/compose/)
