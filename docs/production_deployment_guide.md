# 本番環境デプロイメントガイド

Google Compute Engine (GCE) を使用した Small Voice Project の本番デプロイ手順および運用ガイドです。
**日常的な運用手順（更新・確認）を上部に、新規構築手順（初回のみ）を下部に記載しています。**

---

## 1. 日常運用・更新

### 1.1 アプリケーションの更新

コードを更新した際は、以下の手順で本番環境に反映します。

#### 手順

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

#### 更新確認

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

### 1.2 サービス状態確認・ログ確認

#### コンテナ稼働状態の確認
すべてのコンテナが `Up` 状態であることを確認します。

```bash
docker compose -f docker-compose.prod.yml ps
```

#### ログの確認
リアルタイムでログを確認するには以下を実行します。

```bash
# 全コンテナのログ
docker compose -f docker-compose.prod.yml logs -f

# 特定のコンテナ（例: backend）のログのみ
docker compose -f docker-compose.prod.yml logs -f backend
```
終了するには `Ctrl+C` を押します。

### 1.3 データベース接続 (ローカルから)

ローカルMacのDBクライアントツール（TablePlus、DBeaver等）から本番環境（GCE）のPostgreSQLデータベースに安全に接続する方法です。

#### 接続手順

1. **SSHトンネルの作成**:
   ローカルMacのターミナルで以下を実行し、SSHトンネル（ポートフォワーディング）を作成します。
   ※ `gcloud` コマンドが未セットアップの場合は、下部の「新規構築」セクションを参照してください。

   ```bash
   gcloud compute ssh small-voice-server \
     --zone=asia-northeast1-c \
     --tunnel-through-iap \
     -- -L 5434:localhost:5432 -N
   ```
   **注意**: このターミナルウィンドウは接続中閉じないでください。

2. **DBクライアントツールで接続**:
   以下の情報で接続します。

   | 項目 | 設定値 |
   |------|-----|
   | **ホスト** | `localhost` |
   | **ポート** | `5434` |
   | **ユーザー名** | `postgres` |
   | **パスワード** | `postgres` (または設定したパスワード) |
   | **データベース名** | `small_voice_db` |

3. **終了**:
   作業終了後は、SSHトンネルを実行しているターミナルで `Ctrl+C` を押して切断します。

### 1.4 データ管理・メンテナンス

#### デモ環境のデータリセット
> ⚠️ **警告**: 本番運用中の環境では実行しないでください。全データが削除されます。デモ環境のリセット用です。

```bash
# 1. データベースを完全リセット (全テーブル削除)
docker compose -f docker-compose.prod.yml exec backend python scripts/reset_db_clean.py

# 2. 初期シードデータの投入
# パターンA: 初期ユーザーのみ作成
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_db.py --init-users

# パターンB: 雑談掲示板のテストデータを生成
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_db.py --seed-casual
```

#### 議論コメントのCSVインポート
管理画面から議論スレッド用のCSVデータを一括インポート可能です。
- **URL**: `https://your-domain.com/admin/csv-import`
- **権限**: システム管理者 (`system_admin`)

---

## 2. 新規環境構築ガイド

ここからは、初回のみ実施するサーバー構築手順です。

### 2.1 前提条件

- Google Cloud Platform アカウント（有効な請求先設定済み）
- ドメイン取得済み（例：Google Domains、お名前.com）

### 2.2 GCEインフラ構築

#### 手順1: 静的IPアドレスの予約
1. [GCP Console](https://console.cloud.google.com/) にログイン
2. **「VPC ネットワーク」→「IP アドレス」** を開き、**「外部静的 IP アドレスを予約」** をクリック
3. 設定例：
   - **名前**: `small-voice-ip`
   - **リージョン**: `asia-northeast1`（東京）
4. **割り当てられたIPアドレスをメモ**

#### 手順2: VM インスタンスの作成
1. **「Compute Engine」→「VM インスタンス」→「インスタンスを作成」**
2. 設定例：
   - **名前**: `small-voice-server`
   - **リージョン**: `asia-northeast1`（東京）
   - **マシンタイプ**: `e2-small`（推奨）または `e2-micro`
   - **ブートディスク**: Ubuntu 22.04 LTS、30GB
   - **ファイアウォール**: 「HTTPトラフィックを許可」「HTTPSトラフィックを許可」にチェック
   - **詳細オプション → ネットワーク**: 外部IPに手順1で予約したIPを指定
3. **「作成」** をクリック

#### 手順3: DNS設定
1. **「Cloud DNS」** またはドメイン管理画面でAレコードを設定
2. **Aレコード**:
   - ホスト名: 空欄（または `@`）
   - 値: 手順1のIPアドレス
3. 反映を待ちます（数分〜数時間）

#### 手順4: メール配信設定 (Brevo & Cloud DNS)

本番環境からのメール（招待、PWリセット等）が迷惑メール判定されないよう、Brevo（旧Sendinblue）を使用し、適切なDNS設定を行います。

1. **Brevoアカウント設定**:
   - [Brevo](https://www.brevo.com/) でアカウントを作成し、「Transactional Emails」機能を有効化します。
   - SMTPキーを取得します（ログインパスワードとは異なります）。

2. **DNSレコードの設定 (Cloud DNS)**:
   Google Cloud DNS に以下のレコードを追加してください。これは**必須設定**です。

   | 設定項目 | ホスト名 | タイプ | 値 (データ) | 備考 |
   |---|---|---|---|---|
   | **SPF** | (空欄) | TXT | `v=spf1 include:spf.brevo.com ~all` | 正当な送信元としてBrevoを許可 |
   | **DMARC** | `_dmarc` | TXT | `v=DMARC1; p=none; rua=mailto:admin@small-voice.xyz` | 認証失敗時のポリシー (レポート先は自社管理者に変更可) |
   | **DKIM1** | `brevo1._domainkey` | CNAME | `b1.small-voice-xyz.dkim.brevo.com.` | **重要**: 値はBrevo管理画面 (`Senders & IP` > `Domains`) で指定されたものを使用してください |
   | **DKIM2** | `brevo2._domainkey` | CNAME | `b2.small-voice-xyz.dkim.brevo.com.` | 同上 |

   > **注意**: DKIMのホスト名（`brevo1`など）や値はBrevoのアカウントごとに異なる場合があります。必ずBrevoの管理画面で表示される値を設定してください。


### 2.3 サーバー初期設定

#### 手順1: SSH接続
GCP Consoleの「SSH」ボタンをクリックして接続します。

#### 手順2: Dockerのインストール
以下のコマンドを一括実行してセットアップします。

```bash
# 必要なパッケージのインストールとGPGキーの追加
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release git
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Dockerリポジトリの追加
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# インストール
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 権限付与
sudo usermod -aG docker $USER
```

完了したら、**一度ログアウト（`exit`）して再接続**してください。

### 2.4 アプリケーションデプロイ（初回）

#### 手順1: リポジトリのクローン
```bash
git clone https://github.com/small-voice/small-voice-project.git
cd small-voice-project
```

#### 手順2: 環境変数の設定
```bash
cp .env.example .env
nano .env
```
`.env` 内の以下の項目を適切に設定してください：
- `GEMINI_API_KEY`: Google AI Studioで取得
- `INITIAL_SYSTEM_PASSWORD` 等: 初期パスワード
- **メール送信設定 (Brevo)**:
  - `SMTP_SERVER`: `smtp-relay.brevo.com`
  - `SMTP_PORT`: `587`
  - `SMTP_USERNAME`: Brevoのログインメールアドレス
  - `SMTP_PASSWORD`: Brevoで取得したSMTPキー (ログインパスワードではありません)
  - `SENDER_EMAIL`: 送信元アドレス (例: `noreply@small-voice.xyz`)
- `ENVIRONMENT`: `production`
- `BASIC_AUTH_USER`: Basic認証のユーザー名 (指定しない場合は admin)
- `BASIC_AUTH_PASSWORD`: Basic認証のパスワード (指定しない場合は admin)

#### 手順3: SSL証明書の取得
```bash
# Certbotインストール
sudo apt-get install -y certbot

# 証明書取得 (80番ポートを使用するため、Nginx起動前に実行)
sudo certbot certonly --standalone -d your-domain.com
```

#### 手順4: Nginx設定
```bash
nano nginx/default.conf
```
`server_name` を実際のドメインに書き換え、SSL証明書のパスが正しいか確認してください（`nginx/default.conf` の内容はリポジトリ内のファイルをベースに適宜修正）。

#### 手順5: 初回起動
```bash
docker compose -f docker-compose.prod.yml up -d
```
起動後、ブラウザで `https://your-domain.com` にアクセスして動作を確認します。

---

## 3. 付録

### コスト目安（東京リージョン）
| 項目 | 月額コスト |
|------|-----------|
| e2-small VM（推奨） | 約 $14 |
| e2-micro VM（最小） | 約 $8 |
| ディスク 30GB | 約 $4 |
| **合計** | **$12-18** |

### 参考リンク
- [Google Cloud DNS ドキュメント](https://cloud.google.com/dns)
- [Brevo（旧Sendinblue）](https://www.brevo.com/)
- [Let's Encrypt](https://letsencrypt.org/)
