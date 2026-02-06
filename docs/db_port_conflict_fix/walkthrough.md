# 修正内容の確認 - データベースポートの変更

## 実施内容
- ホストマシンの PostgreSQL とのポート競合を避けるため、Docker コンテナの PostgreSQL 公開ポートを **5433** に変更しました。
- 関連ドキュメント（セットアップガイド、本番接続ガイド）のポート情報を更新しました。

## 変更されたファイル
- [docker-compose.yml](file:///Users/koderahayato/small-voice-project/docker-compose.yml)
- [docker-compose.dev.yml](file:///Users/koderahayato/small-voice-project/docker-compose.dev.yml)
- [local_development_setup.md](file:///Users/koderahayato/small-voice-project/docs/local_development_setup.md)
- [db_connection_guide.md](file:///Users/koderahayato/small-voice-project/docs/db_connection_guide.md)

## 検証結果

### 1. ポート待機状態の確認
ホストマシンでポート 5433 が Docker によって使用されていることを確認しました。
```bash
$ lsof -i :5433
COMMAND    PID         USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
com.docke 4655 koderahayato  157u  IPv6 0xf1185ccaa9bf996d      0t0  TCP *:5433 (LISTEN)
```

### 2. コンテナの稼働状況
全てのコンテナが正常に起動し、DBポートが正しくマッピングされていることを確認しました。
```bash
$ docker ps
NAMES                            STATUS              PORTS
small-voice-project_frontend_1   Up About a minute   0.0.0.0:3000->3000/tcp
small-voice-project_backend_1    Up About a minute   0.0.0.0:8000->8000/tcp
small-voice-project_db_1         Up About a minute   0.0.0.0:5433->5432/tcp
```

## クライアントツールからの新しい接続情報

| 項目 | 値 |
|------|-----|
| **Host** | `localhost` |
| **Port** | **5433** (変更されました) |
| **User** | `postgres` |
| **Password** | `postgres` |
| **Database** | `voice_insight_db` |

> [!IMPORTANT]
> **本番DBへの接続について**: 
> ローカルDBが5433を使用するようになったため、本番DBへのSSHトンネル（gcloudコマンド）で使用するポートを **5434** に変更しました。詳細は [db_connection_guide.md](file:///Users/koderahayato/small-voice-project/docs/db_connection_guide.md) を参照してください。
