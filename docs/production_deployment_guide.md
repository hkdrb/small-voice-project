# 本番環境デプロイメントガイド

Google Compute Engine (GCE) を使用した Small Voice Project の本番デプロイ手順です。

---

## 前提条件

- Google Cloud Platform アカウント（有効な請求先）
- ドメイン取得済み（Google Domains、お名前.comなど）
- gcloud CLI インストール済み（推奨）

---

## 1. GCEインフラ構築

### 1.1 静的IPアドレスの予約

1. GCPコンソール → **「VPC ネットワーク」→「IP アドレス」**
2. 「外部静的 IP アドレスを予約」をクリック
3. 設定値：
   - **名前**: `small-voice-ip`
   - **リージョン**: `asia-northeast1`（東京）
4. 割り当てられた**IPアドレスをメモ**

### 1.2 VM インスタンスの作成

1. **「Compute Engine」→「VM インスタンス」→「インスタンスを作成」**
2. 設定値：
   - **名前**: `small-voice-server`
   - **リージョン**: `asia-northeast1`
   - **マシンタイプ**: `e2-micro`（低コスト構成）
   - **ブートディスク**: Ubuntu 22.04 LTS、30GB以上
   - **ファイアウォール**: HTTPとHTTPSを許可
   - **外部IP**: 手順1.1で予約したIPを選択

### 1.3 DNS設定（Google Cloud DNS）

1. GCPコンソール → **「Cloud DNS」** → **「ゾーンを作成」**
2. 設定値：
   - **ゾーンの種類**: 一般公開
   - **DNS名**: あなたのドメイン（例：`small-voice.xyz`）
3. **Aレコードを追加**：
   - **DNS名**: 空欄（@相当）
   - **タイプ**: A
   - **IPv4アドレス**: 手順1.1のIPアドレス
4. **NSレコードをメモ**（`ns-cloud-a1.googledomains.com.` など4つ）
5. **ドメインレジストラ（お名前.comなど）でネームサーバーを変更**：
   - メモした4つのNSレコードを設定

---

## 2. サーバーセットアップ

### 2.1 SSH接続

GCPコンソール → **「VM インスタンス」** → 対象インスタンスの**「SSH」**ボタンをクリック

> **Tip**: sudo権限がない場合、IAMで「Compute OS 管理者ログイン」ロールを追加し、再接続してください。

### 2.2 必要ツールのインストール

```bash
# パッケージ更新とDocker準備
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# Docker公式GPGキー追加
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Dockerリポジトリ追加
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Dockerインストール
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker権限設定
sudo usermod -aG docker $USER
```

### 2.3 作業用ユーザー作成

```bash
# ユーザー作成
sudo adduser workuser --gecos "Work User" --disabled-password
echo "workuser:YourStrongPassword" | sudo chpasswd

# sudo権限付与
sudo usermod -aG sudo workuser
echo "workuser ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/workuser
```

### 2.4 スワップ領域作成（e2-micro用）

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**一度ログアウトして再接続**してください。

---

## 3. SSL証明書取得

### 3.1 Certbotインストール

```bash
sudo apt-get install -y certbot
```

### 3.2 証明書取得

```bash
# Dockerコンテナが起動していないことを確認
sudo certbot certonly --standalone -d your-domain.com
```

> ⚠️ `your-domain.com`を実際のドメインに置き換えてください。

証明書は `/etc/letsencrypt/live/your-domain.com/` に保存されます。

---

## 4. アプリケーションデプロイ

### 4.1 リポジトリ取得

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git small-voice-project
cd small-voice-project
```

### 4.2 環境変数設定

```bash
cp .env.example .env
nano .env
```

**`.env` 設定例：**

```ini
# Gemini API
GEMINI_API_KEY=your_actual_key
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# システムパスワード
INITIAL_SYSTEM_PASSWORD=secure_system_pass
INITIAL_ADMIN_PASSWORD=secure_admin_pass
INITIAL_USER_PASSWORD=secure_user_pass

# メール設定（Brevo推奨）
ENVIRONMENT=production
SMTP_SERVER=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your_brevo_email@example.com
SMTP_PASSWORD=your_brevo_smtp_key
SENDER_EMAIL=noreply@your-domain.com
SENDER_NAME="Small Voice System"
```

### 4.3 Nginx設定ファイル確認

`nginx/default.conf` が以下の内容になっているか確認：

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

> ⚠️ `your-domain.com` を実際のドメインに置き換えてください。

### 4.4 docker-compose.prod.yml 確認

以下の内容が含まれているか確認：

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"  # HTTPS用ポート
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro  # 証明書マウント
    depends_on:
      - backend
      - frontend
    restart: always

  frontend:
    image: ghcr.io/your_username/your_repo/frontend:latest
    restart: always
    # ポート公開なし（Nginx経由のみでアクセス）
    environment:
      - NEXT_PUBLIC_API_URL=/api
    depends_on:
      - backend

  backend:
    image: ghcr.io/your_username/your_repo/backend:latest
    restart: always
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@db:5432/small_voice_db
      # その他環境変数...
    depends_on:
      - db

  db:
    image: postgres:14
    restart: always
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=small_voice_db
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data

volumes:
  postgres_data_prod:
```

> 🔒 **セキュリティ推奨**: frontendの`ports`は削除し、すべてのアクセスをNginx（HTTPS）経由にします。

### 4.5 起動

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4.6 動作確認

ブラウザで `https://your-domain.com` にアクセスし、🔒マークが表示されることを確認してください。

---

## 5. トラブルシューティング

### ❌ 「このサイトにアクセスできません」（接続が拒否されました）

**原因**: Nginxコンテナが起動していない

**確認方法**:
```bash
docker compose -f docker-compose.prod.yml ps
```

Nginxが`Restarting`状態の場合：

**解決策**:
```bash
# ログを確認
docker compose -f docker-compose.prod.yml logs nginx

# よくあるエラー: 証明書ファイルが見つからない
# → docker-compose.prod.ymlに証明書マウントがあるか確認
# volumes:
#   - /etc/letsencrypt:/etc/letsencrypt:ro

# 443番ポートが公開されているか確認
# ports:
#   - "80:80"
#   - "443:443"
```

設定を修正後：
```bash
docker compose -f docker-compose.prod.yml up -d
```

### ⚠️ 「危険なサイト」警告が表示される

**原因**: ブラウザのキャッシュ

**解決策**:
1. **シークレットモード/プライベートウィンドウ**でアクセス
2. または**ブラウザのキャッシュとCookieをクリア**

証明書が有効か確認：
```bash
sudo certbot certificates
```

### 🔄 証明書の更新

Let's Encryptの証明書は**90日間有効**です。更新手順：

```bash
# Nginx一時停止
docker compose -f docker-compose.prod.yml stop nginx

# 更新実行
sudo certbot renew

# Nginx再起動
docker compose -f docker-compose.prod.yml start nginx
```

**自動更新（推奨）**:
```bash
# crontabに追加（毎月1日午前3時に実行）
sudo crontab -e

# 以下を追加
0 3 1 * * docker compose -f /path/to/small-voice-project/docker-compose.prod.yml stop nginx && certbot renew --quiet && docker compose -f /path/to/small-voice-project/docker-compose.prod.yml start nginx
```

---

## 6. アプリケーション更新

### GitHub Actions + GHCR を使用した高速デプロイ

#### 初回準備

1. **GitHub PATの作成**: Settings → Developer settings → Personal access tokens
   - スコープ: `repo`, `read:packages`

2. **サーバーでログイン**:
```bash
echo "YOUR_PAT" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

#### 更新手順

**ローカル**:
```bash
git push origin main
```

GitHub Actionsが自動的にイメージをビルド・プッシュします（数分）。

**サーバー**:
```bash
cd small-voice-project
git pull origin main
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker image prune -f  # 不要イメージ削除
```

---

## 7. 運用

### ログ確認
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### データバックアップ
GCEのスナップショット機能を利用して定期的にバックアップを取得してください。

### デモ環境のデータリセット

> ⚠️ **警告**: 本番環境では絶対に実行しないでください！全データが削除されます。

```bash
# 全データ削除
docker compose -f docker-compose.prod.yml exec backend python scripts/reset_db_clean.py

# ダミーデータ投入
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_db.py --with-dummy-data
```

---

## 参考: コスト目安（東京リージョン）

- **e2-micro VM**: 約 $8/月
- **e2-micro Spot**: 約 $3-4/月（停止リスクあり）
- **ディスク (30GB)**: 約 $4/月
- **合計**: **$7-12/月**

> 💡 **無料枠**: 米国リージョン（us-central1等）ならe2-microは無料枠対象です。
