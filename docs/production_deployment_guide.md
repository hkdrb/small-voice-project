# 本番環境デプロイメントガイド

Google Compute Engine (GCE) を使用した Small Voice Project の本番デプロイ手順です。

---

## 前提条件

- Google Cloud Platform アカウント（有効な請求先設定済み）
- ドメイン取得済み（例：Google Domains、お名前.com）
- 基本的なLinuxコマンド操作の知識

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
| マシンタイプ | `e2-micro` |
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

> **トラブルシューティング**: sudoコマンドで権限エラーが出る場合
> 1. **「IAMと管理」→「IAM」** を開く
> 2. 自分のアカウントに **「Compute OS 管理者ログイン」** ロールを追加
> 3. SSH接続を閉じて再接続

### 2.2 Dockerのインストール

```bash
# パッケージ更新
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# Docker GPGキー追加
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Dockerリポジトリ追加
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Dockerインストール
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 現在のユーザーにDocker権限を付与
sudo usermod -aG docker $USER
```

### 2.3 スワップ領域の作成

e2-microはメモリが少ないため、スワップ領域を作成します：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2.4 ログアウトして再接続

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
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

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

## 4. トラブルシューティング

### ❌ 「接続が拒否されました」と表示される

**原因**: Nginxコンテナが起動していません。

**確認**:
```bash
docker compose -f docker-compose.prod.yml ps
```

Nginxが`Restarting`状態の場合、設定エラーです：

```bash
# エラーログを確認
docker compose -f docker-compose.prod.yml logs nginx
```

**よくあるエラーと対処法**:

| エラーメッセージ | 原因 | 対処法 |
|-----------------|------|--------|
| `cannot load certificate` | 証明書マウントが不足 | `docker-compose.prod.yml`に<br>`- /etc/letsencrypt:/etc/letsencrypt:ro`<br>を追加 |
| `bind: address already in use` | ポートが使用中 | 既存のNginxを停止:<br>`sudo systemctl stop nginx` |

修正後、再起動：
```bash
docker compose -f docker-compose.prod.yml up -d
```

### ⚠️ 「危険なサイト」と警告が表示される

**原因**: ブラウザのキャッシュが古い証明書を保持しています。

**解決策**:
1. **シークレット/プライベートウィンドウで開く**
2. または**ブラウザのキャッシュをクリア**

証明書が本当に有効か確認：
```bash
sudo certbot certificates
```

`VALID`と表示されればOKです。

### 🔄 証明書の更新（90日ごと）

Let's Encrypt証明書は90日間有効です。更新手順：

```bash
# Nginx停止
docker compose -f docker-compose.prod.yml stop nginx

# 証明書更新
sudo certbot renew

# Nginx再起動
docker compose -f docker-compose.prod.yml start nginx
```

**自動更新の設定（推奨）**:

```bash
# crontab編集
sudo crontab -e

# 以下を追加（毎月1日午前3時に自動更新）
0 3 1 * * cd /home/$USER/small-voice-project && docker compose -f docker-compose.prod.yml stop nginx && certbot renew --quiet && docker compose -f docker-compose.prod.yml start nginx
```

---

## 5. アプリケーション更新

コードを更新した場合の反映手順です。

### 方法1: サーバー上で直接ビルド（初回デプロイ時）

```bash
cd small-voice-project
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

### 方法2: GitHub Container Registry (GHCR) を使用（推奨）

更新が高速（数十秒）になります。

#### 初回準備

1. **GitHub Personal Access Tokenの作成**:
   - GitHub → Settings → Developer settings → Personal access tokens (Classic)
   - スコープ: `repo`, `read:packages` を選択
   - トークンを生成してコピー

2. **サーバーでGHCRにログイン**:
```bash
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

#### 更新手順

**ローカル（開発マシン）**:
```bash
git add .
git commit -m "Update message"
git push origin main
```

GitHub Actionsが自動的にイメージをビルド（数分）。

**サーバー**:
```bash
cd small-voice-project
git pull origin main
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

---

## 6. 運用管理

### ログ確認

```bash
# 全サービスのログ
docker compose -f docker-compose.prod.yml logs -f

# 特定サービスのログ
docker compose -f docker-compose.prod.yml logs -f backend
```

### コンテナ状態確認

```bash
docker compose -f docker-compose.prod.yml ps
```

### データバックアップ

GCPのスナップショット機能を使用：

1. **「Compute Engine」→「スナップショット」**
2. **「スナップショットを作成」** をクリック
3. ソースディスク: `small-voice-server`
4. 定期的に実行することを推奨

### デモ環境のデータリセット

> ⚠️ **警告**: 本番環境では実行しないでください。全データが削除されます。

```bash
# 全データ削除
docker compose -f docker-compose.prod.yml exec backend python scripts/reset_db_clean.py

# デモ用ダミーデータ投入
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_db.py --with-dummy-data
```

---

## 付録

### コスト目安（東京リージョン）

| 項目 | 月額コスト |
|------|-----------|
| e2-micro VM（通常） | 約 $8 |
| e2-micro VM（Spot） | 約 $3-4 |
| ディスク 30GB | 約 $4 |
| **合計** | **$7-12** |

> 💡 **節約Tips**: 米国リージョン（us-central1等）のe2-microは無料枠対象です。

### 参考リンク

- [Google Cloud DNS ドキュメント](https://cloud.google.com/dns)
- [Brevo（旧Sendinblue）](https://www.brevo.com/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Docker Compose リファレンス](https://docs.docker.com/compose/)
