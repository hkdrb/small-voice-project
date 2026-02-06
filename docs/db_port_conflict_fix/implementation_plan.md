# 実装計画 - データベースポートの競合解消

## 概要
ホストマシンで既に PostgreSQL がポート 5432 を使用しているため、Docker コンテナの PostgreSQL ポートを 5433 に変更して競合を回避します。

## ユーザー確認事項
- クライアントツール（TablePlus、pgAdminなど）から接続する際は、ポートを **5433** に設定する必要があります。
- アプリケーション内部（Backend から DB への接続）は Docker ネットワーク内で行われるため、設定変更の必要はありません。

## 変更内容

### Docker 設定の変更

#### [MODIFY] [docker-compose.yml](file:///Users/koderahayato/small-voice-project/docker-compose.yml)
- `db` サービスの `ports` を `"5432:5432"` から `"5433:5432"` に変更します。

#### [MODIFY] [docker-compose.dev.yml](file:///Users/koderahayato/small-voice-project/docker-compose.dev.yml)
- `db` サービスの `ports` を `"5432:5432"` から `"5433:5432"` に変更します。

## 検証計画

### 手動検証
1. `docker-compose -f docker-compose.dev.yml up -d` を実行してコンテナを再起動します。
2. ホストマシンから `lsof -i :5433` を実行し、Docker が 5433 ポートをリッスンしていることを確認します。
3. クライアントツールから `localhost:5433` で接続できることを確認します。
