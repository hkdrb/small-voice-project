# 本番環境デプロイメントガイド (Google Compute Engine 編)

このガイドでは、**Google Compute Engine (GCE)** を使用して Small Voice Project を本番環境にデプロイする手順を説明します。
Google Cloud Platform (GCP) の堅牢なインフラを活用し、安全かつ安定した運用を目指します。

## 前提条件

- **Google Cloud Platform アカウント**: 有効な請求先アカウントが設定されていること
- **ドメイン**: 取得済みであること（Google Domains, お名前.comなど）
- **gcloud CLI**: ローカルマシンにインストール済みであること（推奨）
    - 未インストールの場合はブラウザの Cloud Shell でも代用可能です。

---

## 1. GCE インフラストラクチャの構築

### 1.1 プロジェクトの作成

Google Cloud Console にアクセスし、新しいプロジェクトを作成します（例: `small-voice-prod`）。

### 1.2 静的IPアドレスの予約

サーバーのIPアドレスが変わらないように、静的IPを予約します。

1.  Console 左メニューから **「VPC ネットワーク」 > 「IP アドレス」** を選択。
2.  「外部静的 IP アドレスを予約」をクリック。
3.  **名前**: `small-voice-ip` (任意)
4.  **リージョン**: `asia-northeast1` (東京) など、ユーザーに近い場所。
5.  「予約」をクリックし、割り当てられた **外部IPアドレス** をメモします。

### 1.3 VM インスタンスの作成

1.  メニューから **「Compute Engine」 > 「VM インスタンス」** を選択し、「インスタンスを作成」をクリック。
2.  **名前**: `small-voice-server`
3.  **リージョン**: IPアドレスと同じリージョンを選択（例: `asia-northeast1`）。
4.  **マシン構成**:
    - **シリーズ**: `E2`
    - **マシンタイプ**: `e2-micro` (2 vCPU, 1GB メモリ)
    - **VMプロビジョニングモデル**: 「スポット（Spot）」を選択すると、さらに大幅に安くなります（約60-90% OFF）。
        - ※ デモ用途で「落ちても再起動すれば良い」場合はスポットが最強のコストパフォーマンスです。
5.  **ブートディスク**:
    - 「変更」をクリック。
    - **OS**: `Ubuntu`
    - **バージョン**: `Ubuntu 22.04 LTS` (x86/64)
    - **ディスクの種類**: `バランス永続ディスク`
    - **サイズ**: `30 GB` 以上


    > **参考コスト（東京リージョン・最低コスト構成）**
    > - **VM (e2-micro 標準)**: 約 $8/月
    > - **VM (e2-micro Spot)**: **約 $3〜4/月** (強制停止のリスクあり)
    > - **ディスク**: 約 $4/月
    > - **合計**: **$7〜12/月** 目安
    > - **無料枠**: 米国リージョン(us-central1等)ならe2-microは無料枠対象ですが、東京は対象外です。

6.  **ファイアウォール**:
    - 「HTTP トラフィックを許可する」にチェック。
    - 「HTTPS トラフィックを許可する」にチェック。
7.  **詳細オプション > ネットワーク インターフェース**:
    - 外部 IPv4 アドレスで、先ほど予約した `small-voice-ip` を選択。
8.  「作成」をクリック。

### 1.4 ドメインとDNSの設定 (Google Cloud DNS を使用)

DNSの反映を高速かつ確実にするため、**Google Cloud DNS** を使用します。

1.  GCPコンソールの検索バーで **「Cloud DNS」** を検索し、選択します。
2.  **「ゾーンを作成」** をクリック。
    - **ゾーンの種類**: `一般公開`
    - **ゾーン名**: `small-voice-zone` (任意)
    - **DNS名**: あなたのドメイン名 (例: `early-bird.xyz`)
    - 「作成」をクリック。
3.  **レコードセットの追加**:
    - 「レコードセットを追加」をクリック。
    - **DNS名**: 空欄（`@`相当）
    - **リソースレコードのタイプ**: `A`
    - **IPv4 アドレス**: 手順1.2で取得した **外部IPアドレス**
    - 「作成」をクリック。
4.  **ネームサーバーの確認**:
    - 設定画面の右上（または一覧）にある `NS` レコードを探します。
    - `ns-cloud-a1.googledomains.com.` などの4つのアドレスをメモします。
5.  **レジストラ（お名前.com等）側の設定変更**:
    - ドメイン管理画面（お名前.com Naviなど）にログイン。
    - 「ネームサーバーの変更」→ **「他のネームサーバーを利用」** を選択。
    - メモした4つのアドレス（`ns-cloud-...`）を入力して保存します。

これでDNS管理がGoogle Cloud側に委譲されます。反映は比較的早いです（数分〜数十分）。

---

## 2. サーバーのセットアップ

### 2.1 ブラウザからの SSH 接続

1. GCP コンソールにログインし、左側メニューの **Compute Engine → VM インスタンス** を開く。
2. 対象のインスタンス（例: `small-voice-server`）の行にある **SSH** ボタンをクリック。
3. ブラウザ上にターミナルが起動し、直接コマンドを入力できるようになる。
   - 初回は自動的に SSH 鍵が作成・登録され、以降は同じブラウザで再利用できる。

> **トラブルシューティング: `sudo` が使えない場合**
>
> ブラウザから接続しても `sudo apt-get ...` で「権限がない」と言われる場合は、IAM 権限が不足しています。
> 1. GCP コンソール「IAM と管理」→「IAM」を開く。
> 2. 自分のアカウントの行末にある「編集（鉛筆）」をクリック。
> 3. 「ロールを追加」で **「Compute OS 管理者ログイン (roles/compute.osAdminLogin)」** を追加して保存する。
> 4. ブラウザ SSH を一度閉じ、再度「SSH」ボタンから接続し直す。

> **Tip**: ブラウザ端末は一時的な環境です。永続的に作業したい場合は次の **gcloud CLI** でも接続できます。

### 2.2 必要なツールのインストール (Docker)

```bash
# パッケージリスト更新 と 必要ツールのインストール
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# Docker 公式 GPG キーの追加
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker リポジトリの追加
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker Engine のインストール
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### 2.3 Docker の実行権限設定

```bash
sudo usermod -aG docker $USER   # ログアウト・再ログインで反映
```

### 2.4 作業用ユーザー (workuser) の作成と権限付与

```bash
# 1. ユーザー作成（パスワードなし）
sudo adduser workuser --gecos "Work User" --disabled-password

# 2. 必要ならパスワード設定（例: StrongPass123!）
echo "workuser:StrongPass123!" | sudo chpasswd

# 3. sudo グループへ追加（管理者権限）
sudo usermod -aG sudo workuser

# 4. パスワードなし sudo を許可（任意）
echo "workuser ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/workuser

# 5. SSH 鍵の設定（任意: ブラウザ接続のみならスキップ可）
# ※ ブラウザ SSH のみ使用する場合は、以下の 4 行は実行しなくて OK です
# sudo -u workuser mkdir -p /home/workuser/.ssh
#
# 下記は公開鍵を持っている場合のみ実行
# echo "ssh-rsa AAAAB3... your_key" | sudo tee -a /home/workuser/.ssh/authorized_keys
# sudo chmod 700 /home/workuser/.ssh
# sudo chmod 600 /home/workuser/.ssh/authorized_keys
# sudo chown -R workuser:workuser /home/workuser/.ssh
```

### 2.5 スワップ領域の作成（e2‑micro 用）

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

# 一度ログアウトして再ログイン（設定反映のため）
exit
```
再度 SSH 接続してください。

---

## 3. アプリケーションのデプロイ

### 3.1 リポジトリの取得

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git small-voice-projec
cd small-voice-projec
```

### 3.2 環境変数の設定

```bash
cp .env.example .env
nano .env
```

`.env` の編集例:
```ini
GEMINI_API_KEY=your_actual_key
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# セキュアなパスワードを設定
INITIAL_SYSTEM_PASSWORD=prod_sys_pass
INITIAL_ADMIN_PASSWORD=prod_admin_pass
INITIAL_USER_PASSWORD=prod_user_pass
```

### 3.3 SSL化 (HTTPS) と起動

GCEのファイアウォール設定でHTTPSは許可されていますが、サーバー内部で証明書を取得・設定する必要があります。
ここでは `certbot` を使って証明書を取得し、それを Nginx コンテナにマウントする方法を採用します。

#### 3.3.1 Certbot のインストール (ホスト側)

```bash
sudo apt-get install -y certbot
```

#### 3.3.2 証明書の取得

一時的に80番ポートを使用して証明書を取得します。Nginx等が起動していない状態で実行してください。

```bash
sudo certbot certonly --standalone -d your-domain.com
```
※ `your-domain.com` はあなたのドメインに置き換えてください。
成功すると `/etc/letsencrypt/live/your-domain.com/` に証明書が保存されます。

#### 3.3.3 Nginx設定の更新

`nginx/default.conf` を編集し、HTTPS設定を有効にします。

```bash
mkdir nginx
nano nginx/default.conf
```

**変更後の `nginx/default.conf` 例:**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    # HTTPSへのリダイレクト
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    # 検索エンジンにインデックスされないようにする
    add_header X-Robots-Tag "noindex, nofollow, nosnippet, noarchive";

    # 証明書のパス (コンテナ内のパス)
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
※ `server_name` と証明書パスのドメイン部分を書き換えてください。

#### 3.3.4 docker-compose.prod.yml の修正

証明書ディレクトリをマウントするため、`docker-compose.prod.yml` を編集します。
以下の内容でファイル全体を上書きしてください。

```bash
nano docker-compose.prod.yml
```

**`docker-compose.prod.yml` の完成形:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: small_voice_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}

  backend:
    build: 
      context: .
      dockerfile: Dockerfile.backend
    restart: always
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@db:5432/small_voice_db
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL_NAME=${GEMINI_MODEL_NAME:-gemini-pro}
      - INITIAL_SYSTEM_PASSWORD=${INITIAL_SYSTEM_PASSWORD}
      - INITIAL_ADMIN_PASSWORD=${INITIAL_ADMIN_PASSWORD}
      - INITIAL_USER_PASSWORD=${INITIAL_USER_PASSWORD}
    depends_on:
      - db

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    restart: always
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

### 3.4 起動と確認

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

ブラウザで `https://your-domain.com` にアクセスし、アプリケーションが表示されること、鍵マーク（SSL保護）がついていることを確認してください。

---

## 4. 運用・メンテナンス

### ログの確認
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### 証明書の更新
Let's Encrypt の証明書は90日で切れます。更新するには：
```bash
# 一時的にNginxを停止
docker compose -f docker-compose.prod.yml stop nginx

# 更新
sudo certbot renew

# 再起動
docker compose -f docker-compose.prod.yml start nginx
```
これをcronなどで自動化することを推奨します。

### データバックアップ
GCEのスナップショット機能を活用して、ディスク全体のバックアップを定期的に取得するのが最も簡単で確実です。
