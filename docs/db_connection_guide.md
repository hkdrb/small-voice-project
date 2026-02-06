# 本番DB接続ガイド

このガイドでは、ローカルMacのDBクライアントツールから本番環境（GCE）のPostgreSQLデータベースに安全に接続する方法を説明します。

## 前提条件

- Google Cloud Platform アカウント（本番環境へのアクセス権限）
- DBクライアントツール（TablePlus、DBeaver、psql等）

---

## 1. gcloud CLIのインストール（初回のみ）

### インストール済みの確認

```bash
gcloud --version
```

バージョン情報が表示されればスキップしてください。

### インストール手順

1. **Python 3.12のインストール** （gcloud CLIがPython 3.13に対応していないため）

```bash
brew install python@3.12
```

2. **gcloud CLIのダウンロードとインストール**

```bash
cd ~/small-voice-project
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-darwin-arm.tar.gz
tar -xzf google-cloud-cli-darwin-arm.tar.gz
CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.12 ./google-cloud-sdk/install.sh --quiet
```

3. **PATHの設定**

```bash
echo 'export PATH=$PATH:~/small-voice-project/google-cloud-sdk/bin' >> ~/.zshrc
source ~/.zshrc
```

4. **gcloud CLIの初期化**

```bash
gcloud init
```

プロンプトで以下を選択：
- Google アカウントでログイン
- プロジェクト: `gen-lang-client-0893762716` を選択
- デフォルトリージョン: `asia-northeast1` を選択

---

## 2. SSHトンネルの作成

ローカルMacのターミナルで以下を実行：

```bash
gcloud compute ssh small-voice-server \
  --zone=asia-northeast1-c \
  --tunnel-through-iap \
  -- -L 5434:localhost:5432 -N
```

**重要な注意点**:
- このコマンドは接続を維持し続けます（画面は停止したように見えますが正常です）
- **ターミナルウィンドウを閉じないでください**
- NumPyのインストール警告が表示されますが、無視して問題ありません

---

## 3. DBクライアントツールで接続

SSHトンネルが確立されたら、**新しいターミナルタブ**（⌘+T）を開いて、以下の接続情報でDBクライアントに接続します。

### 接続情報

| 項目 | 値 |
|------|-----|
| **ホスト** | `localhost` |
| **ポート** | `5434` |
| **ユーザー名** | `postgres` |
| **パスワード** | `postgres` |
| **データベース名** | `small_voice_db` |

### TablePlusでの接続

1. TablePlusを起動
2. **⌘+N** または **「新しい接続」** をクリック
3. **PostgreSQL** を選択
4. 接続情報を入力:
   - **Name**: `Small Voice Production DB` （任意の名前）
   - **Host**: `localhost`
   - **Port**: `5434`
   - **User**: `postgres`
   - **Password**: `postgres`
   - **Database**: `small_voice_db`
5. **「Test」** をクリックして接続確認
6. **「Connect」** をクリック

### DBeaverでの接続

1. DBeaverを起動
2. **Database → 新しいデータベース接続** を選択
3. **PostgreSQL** を選択して **「次へ」**
4. 接続設定を入力:
   - **Host**: `localhost`
   - **Port**: `5434`
   - **Database**: `small_voice_db`
   - **Username**: `postgres`
   - **Password**: `postgres`
5. **「接続テスト」** をクリックして確認
6. **「完了」** をクリック

### Posticoでの接続（Mac専用）

1. Posticoを起動
2. **「New Favorite」** をクリック
3. 接続情報を入力:
   - **Nickname**: `Small Voice Production` （任意）
   - **Host**: `localhost`
   - **Port**: `5434`
   - **User**: `postgres`
   - **Password**: `postgres`
   - **Database**: `small_voice_db`
4. **「Connect」** をクリック

### psqlコマンドラインでの接続

```bash
psql -h localhost -p 5434 -U postgres -d small_voice_db
# パスワード入力: postgres
```

接続後、以下のコマンドが使用できます：

```sql
-- テーブル一覧を表示
\dt

-- ユーザー一覧を取得
SELECT id, email, role, created_at FROM users LIMIT 10;

-- 組織一覧を取得
SELECT id, name, created_at FROM organizations LIMIT 10;

-- 接続を終了
\q
```

---

## 4. 接続の終了

作業が終わったら、以下の手順で接続を閉じます：

1. **DBクライアントツールを閉じる**
2. **SSHトンネルのターミナルで `Ctrl+C` を押す**

---

## トラブルシューティング

### エラー: `gcloud: command not found`

PATHが設定されていない可能性があります：

```bash
# 一時的に設定
export PATH=$PATH:~/small-voice-project/google-cloud-sdk/bin

# 恒久的に設定
echo 'export PATH=$PATH:~/small-voice-project/google-cloud-sdk/bin' >> ~/.zshrc
source ~/.zshrc
```

### エラー: `Permission denied (publickey)`

gcloud CLIで認証が必要です：

```bash
gcloud auth login
```

### エラー: `Connection refused` または `channel open failed`

**原因**: サーバー側でPostgreSQLコンテナが起動していない、またはポートバインディングが設定されていない

**解決方法**:

1. GCP ConsoleでVMにSSH接続
2. 以下を実行:

```bash
su - h_kodera0019  # または適切なユーザー名
cd small-voice-project
docker compose -f docker-compose.prod.yml ps
```

3. `db` コンテナの `PORTS` が `127.0.0.1:5432->5432/tcp` となっているか確認
4. なっていない場合:

```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d
```

### ポート5434が既に使用中の場合

別のポート番号を使用してください：

```bash
# ポート15432を使用する例
gcloud compute ssh small-voice-server \
  --zone=asia-northeast1-c \
  --tunnel-through-iap \
  -- -L 15432:localhost:5432 -N
```

DBクライアントの接続ポートも `15432` に変更してください。

### VMが見つからないエラー

**エラー例**: `The resource 'projects/.../zones/asia-northeast1-a/instances/small-voice-server' was not found`

**原因**: ゾーンが間違っている

**解決方法**:

```bash
# VMのゾーンを確認
gcloud compute instances list

# 正しいゾーンでコマンドを実行（通常は asia-northeast1-c）
gcloud compute ssh small-voice-server \
  --zone=asia-northeast1-c \
  --tunnel-through-iap \
  -- -L 5433:localhost:5432 -N
```

---

## セキュリティに関する注意事項

⚠️ **本番データベースに接続する際の重要な注意点**:

1. **読み取り専用で操作することを強く推奨**
   - データの確認・分析のみに使用してください
   - 本番データの変更は極力避けてください

2. **データの変更・削除は慎重に**
   - 必要な場合は、事前にバックアップを取得してください
   - トランザクション内でテストしてからコミットしてください

3. **確認作業が終わったらすぐに切断**
   - 長時間接続したままにしないでください
   - 作業終了後は必ずSSHトンネルを切断してください

4. **パスワード管理**
   - 本ガイドのパスワード（`postgres`）は開発用です
   - 本番環境では強力なパスワードに変更することを推奨します

---

## まとめ

この手順により、ローカルのDBクライアントツールから本番PostgreSQLに安全に接続できます。

**接続の流れ**:

```
ローカルMac (TablePlus/DBeaver/psql)
  ↓ localhost:5434
SSH トンネル (IAP経由)
  ↓
GCE VM (small-voice-server)
  ↓ localhost:5432
PostgreSQL (Dockerコンテナ)
```

**次回以降の接続手順**:

1. ターミナルでSSHトンネルを作成:
   ```bash
   gcloud compute ssh small-voice-server \
     --zone=asia-northeast1-c \
     --tunnel-through-iap \
     -- -L 5434:localhost:5432 -N
   ```

2. 新しいターミナルタブまたはDBクライアントツールで `localhost:5434` に接続

何か問題が発生した場合は、トラブルシューティングセクションを参照してください。
