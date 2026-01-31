# 本番DB接続ガイド

このガイドでは、ローカルMacのDBクライアントツールから本番環境（GCE）のPostgreSQLデータベースに安全に接続する方法を説明します。

## 前提条件

- Google Cloud CLI (gcloud) がインストール済み
- GCPプロジェクトへのアクセス権限
- DBクライアントツール（TablePlus、DBeaver、psql等）

---

## 1. gcloud CLIの初期設定

gcloud CLIをまだ初期化していない場合は、以下を実行してください：

```bash
# google-cloud-sdkディレクトリに移動
cd ~/small-voice-project/google-cloud-sdk

# gcloud初期化
./bin/gcloud init
```

初期化プロンプトで以下を選択：
1. **Google アカウントでログイン** → ブラウザが開くのでログイン
2. **プロジェクトを選択** → 本番環境のGCPプロジェクトを選択
3. **デフォルトリージョン** → `asia-northeast1` を選択（オプション）

---

## 2. SSHトンネルの作成

### 方法1: 標準SSHトンネル（推奨）

ローカルMacのターミナルで以下を実行：

```bash
# google-cloud-sdkのパスを設定
export PATH=$PATH:~/small-voice-project/google-cloud-sdk/bin

# SSHトンネル作成（ローカル5433ポート → リモート5432ポート）
gcloud compute ssh small-voice-server \
  --zone=asia-northeast1-a \
  -- -L 5433:localhost:5432 -N
```

**重要**: このコマンドは接続を維持し続けます。ターミナルを閉じないでください。

---

## 3. DBクライアントツールで接続

SSHトンネルが確立されたら、**新しいターミナルタブ**を開いて、以下の接続情報でDBクライアントに接続します。

### 接続情報

| 項目 | 値 |
|------|-----|
| **ホスト** | `localhost` |
| **ポート** | `5433` |
| **ユーザー名** | `postgres` |
| **パスワード** | `postgres` |
| **データベース名** | `small_voice_db` |

### TablePlusでの接続例

1. TablePlusを起動
2. **「新しい接続」** をクリック
3. **PostgreSQL** を選択
4. 上記の接続情報を入力
5. **「テスト」** をクリックして接続確認
6. **「接続」** をクリック

### DBeaver での接続例

1. DBeaverを起動
2. **Database → 新しいデータベース接続** を選択
3. **PostgreSQL** を選択して **次へ**
4. 接続設定:
   - **Host**: `localhost`
   - **Port**: `5433`
   - **Database**: `small_voice_db`
   - **Username**: `postgres`
   - **Password**: `postgres`
5. **接続テスト** をクリックして確認
6. **完了** をクリック

### psqlコマンドラインでの接続例

```bash
psql -h localhost -p 5433 -U postgres -d small_voice_db
# パスワード入力を求められたら: postgres
```

接続後、SQLクエリを実行できます：

```sql
-- テーブル一覧を表示
\dt

-- ユーザー一覧を取得
SELECT id, email, role, created_at FROM users;

-- 組織一覧を取得
SELECT id, name, created_at FROM organizations;
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

# 恒久的に設定（~/.zshrcに追記）
echo 'export PATH=$PATH:~/small-voice-project/google-cloud-sdk/bin' >> ~/.zshrc
source ~/.zshrc
```

### エラー: `Permission denied (publickey)`

gcloud CLIで認証が必要です：

```bash
gcloud auth login
```

### エラー: `Connection refused` (localhost:5433)

SSHトンネルが確立されていない可能性があります：
1. SSHトンネルのターミナルでエラーが出ていないか確認
2. `gcloud compute ssh` コマンドを再実行

### ポート5433が既に使用中の場合

別のポート番号を使用してください：

```bash
# ポート15432を使用する例
gcloud compute ssh small-voice-server \
  --zone=asia-northeast1-a \
  -- -L 15432:localhost:5432 -N
```

DBクライアントの接続ポートも `15432` に変更してください。

---

## セキュリティに関する注意事項

⚠️ **本番データベースに接続する際の注意点**:

1. **読み取り専用で操作** することを強く推奨します
2. **データの変更・削除は慎重に** 行ってください
3. **確認作業が終わったらすぐに切断** してください
4. **パスワードは安全に管理** してください（本ガイドの例は開発用です）

---

## まとめ

この手順により、ローカルのDBクライアントツールから本番PostgreSQLに安全に接続できます。接続は以下の流れで行います：

```
ローカルMac (TablePlus等)
  ↓ localhost:5433
SSH トンネル (gcloud compute ssh)
  ↓
GCE VM (small-voice-server)
  ↓ localhost:5432  
PostgreSQL (Dockerコンテナ)
```

何か問題が発生した場合は、トラブルシューティングセクションを参照してください。
