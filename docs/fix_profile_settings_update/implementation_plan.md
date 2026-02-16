# 実装計画：プロフィール設定更新機能の修正

## 1. バックエンドの修正 (`backend/api/auth.py`)
- `UserUpdate` Pydanticモデルの `username` を任意（`str | None`）に変更。
- `update_profile` 関数で、`username` が提供された場合のみ更新するように変更。

## 2. フロントエンドの修正 (`frontend/src/components/ProfileSettingsModal.tsx`)
- プロパティおよび状態管理を `name` から `username` に変更。
- `currentPassword` の状態を追加。
- パスワード入力フィールドに値がある場合のみ、「現在のパスワード」入力欄を表示するように UI を変更。
- 送信データに `username` と `current_password` を正しく含めるように修正。

## 3. 正整合性の確保 (`frontend/src/components/Sidebar.tsx`)
- ユーザー情報の表示において `name || username` となっていた箇所を `username` に統一。
- 型定義（`SidebarProps`）から `name` を削除。
