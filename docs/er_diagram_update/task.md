# ER図の改善タスク

## 概要
現在のPythonスクリプトで生成されているER図を、GitHubでの視認性向上とメンテナンス性のためにMermaid記法の`erDiagram`に書き換える。
また、グルーピングごとの色分けを行い、主要なリレーションのみを表示して見やすくする。
最終成果物としてPNG画像を提供する。

## 要求事項
1. **フォーマット変更**: Python (`svgwrite`) -> Mermaid (`erDiagram`)
2. **色分け**: 機能/モジュールごとにエンティティを色分けする
   - User & Org: Blue
   - Survey: Green
   - Analysis: Orange
   - Casual: Purple
   - Notification: Red
3. **リレーション**: 主要なものに限定する
4. **レイアウト**: 縦長（Top-Down）の配置を目指す
5. **簡素化**: 各テーブルのカラムは主要なもの（PK, FK, 代表的な属性）のみ表示し、タイムスタンプ等を省略する
6. **出力**: PNG形式の画像ファイルを作成する

## 現在のエンティティ構成 (from `generate_diagram.py`)
- **User/Org**: `users`, `organizations`, `organization_members`, `sessions`
- **Survey**: `surveys`, `questions`, `answers`, `survey_comments`
- **Analysis**: `analysis_sessions`, `analysis_results`, `issue_definitions`, `comments`, `comment_likes`
- **Casual**: `casual_posts`, `casual_post_likes`, `casual_analyses`
- **Notification**: `notifications`
