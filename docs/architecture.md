# システムアーキテクチャ

## 📖 ドキュメント概要

本ドキュメントは、Small Voice（ブロードリスニングシステム）の技術アーキテクチャを包括的に説明します。システムの設計思想、機能詳細、技術スタック、実装の詳細まで網羅しています。

**対象読者**: 開発者

**読み方ガイド**:
- **全体像を把握したい**: 「主な機能」「技術スタック」セクションを参照
- **AI分析の仕組みを理解したい**: 「AI分析・アルゴリズム詳細」セクションを参照
- **実装を詳しく知りたい**: 「ディレクトリ構造」「コンポーネント詳細」セクションを参照

---

## 📋 目次

1. [主な機能](#主な機能)
   - [1. フォーム管理](#1-フォーム管理)
     - [1.1 雑談掲示板からのフォーム作成](#11-雑談掲示板からのフォーム作成)
     - [1.2 メンバーからのフォーム申請](#12-メンバーからのフォーム申請)
     - [1.3 外部フォームのCSVインポート](#13-外部フォームのcsvインポート)
     - [1.4 管理者によるフォーム作成](#14-管理者によるフォーム作成)
     - [1.5 フォーム回答のCSVエクスポート](#15-フォーム回答のcsvエクスポート)
     - [1.6 申請フォームへのチャット](#16-申請フォームへのチャット)
   - [2. 雑談掲示板](#2-雑談掲示板)
     - [2.1 基本機能](#21-基本機能)
     - [2.2 AI分析結果の管理](#22-ai分析結果の管理)
   - [3. クラスタリング](#3-クラスタリング)
     - [3.1 分析セッション管理](#31-分析セッション管理)
     - [3.2 意味ベクトル化](#32-意味ベクトル化)
     - [3.3 外れ値検出](#33-外れ値検出)
     - [3.4 クラスタリング実行](#34-クラスタリング実行)
     - [3.5 2次元可視化](#35-2次元可視化)
   - [4. 課題リスト](#4-課題リスト)
     - [4.1 実装](#41-実装)
     - [4.2 プロンプトエンジニアリング](#42-プロンプトエンジニアリング)
     - [4.3 データモデル](#43-データモデル)
   - [5. 課題ごとの議論チャット](#5-課題ごとの議論チャット)
   - [6. AIファシリテーター](#6-aiファシリテーター)
     - [6.1 実装](#61-実装)
     - [6.2 プロンプト設計](#62-プロンプト設計)
   - [7. マルチテナント構成](#7-マルチテナント構成)
     - [7.1 権限モデル](#71-権限モデル)
     - [7.2 多重所属](#72-多重所属)
     - [7.3 組織切り替え](#73-組織切り替え)
     - [7.4 組織管理機能](#74-組織管理機能)
   - [8. ユーザー管理](#8-ユーザー管理)
     - [8.1 ユーザーCRUD](#81-ユーザーcrud)
     - [8.2 プロフィール設定](#82-プロフィール設定)
   - [9. 認証とセキュリティ](#9-認証とセキュリティ)
     - [9.1 認証機能](#91-認証機能)
     - [9.2 招待リンク機能](#92-招待リンク機能)
     - [9.3 パスワードリセット](#93-パスワードリセット)
   - [10. 通知システム](#10-通知システム)

2. [技術スタック](#技術スタック)
   - [Frontend](#frontend)
   - [Backend](#backend)
   - [インフラ](#インフラ)

3. [AI分析とアルゴリズム詳細](#ai分析とアルゴリズム詳細)
   - [1. 掲示板分析](#1-掲示板分析)
   - [2. クラスタリング分析](#2-クラスタリング分析)
   - [3. 課題リスト生成](#3-課題リスト生成)
   - [4. AIファシリテーター](#4-aiファシリテーター)

4. [ディレクトリ構造](#ディレクトリ構造)

5. [コンポーネント詳細](#コンポーネント詳細)
   - [Backend](#backend-1)
     - [API層](#api層)
     - [Service層](#service層)
     - [データベース](#データベース)
     - [セキュリティ](#セキュリティ)
   - [Frontend](#frontend-1)
     - [App Router](#app-router)
     - [Components](#components)
   - [Database](#database-1)
   - [Scripts](#scripts)

---

## 主な機能

### 1. フォーム管理
本システムの中核となるフォーム機能です。雑談掲示板からのAI生成、メンバーからのボトムアップ申請、管理者による直接作成、外部CSVインポートなど、多様な経路でフォームを作成・管理できます。

#### 1.1 雑談掲示板からのフォーム作成
- **実装**: `backend/api/casual_chat.py` でCRUD操作を提供
- **データモデル**: `CasualPost` (投稿), `CasualReply` (返信)
- **AI分析機能**: 
  - `backend/services/analysis.py::analyze_casual_posts_logic()` により、投稿内容を分析
  - Gemini APIを使用して、組織的な課題として取り上げるべきトピックを自動抽出
  - 抽出されたトピックから、フォームのタイトル・説明・質問案を自動生成
- **アーキテクチャ特性**: 日常的な会話データを構造化されたアンケートへ昇華させることで、潜在的な課題の早期発見を実現

#### 1.2 メンバーからのフォーム申請
※ ボトムアップ申請機能です。
- **実装**: `backend/api/survey.py` の承認フローシステム
- **ワークフロー**:
  
  | 物理状態 (`approval_status` / `is_active`) | 管理者表示 | 申請者表示 | 詳細説明 |
  | :--- | :--- | :--- | :--- |
  | `pending` / `False` | **申請中** | **申請中** | 申請直後の初期状態。管理者が内容を審査します。 |
  | `approved` / `False` | **停止中** | **承認済み** | 承認されたが非公開。管理者が公開操作を行うまでこの状態です。 |
  | `approved` / `True` | **公開中** | (非表示*) | 全ユーザーへ公開中。*申請者は「回答」タブで確認可能になります。 |
  | `rejected` / `False` | **却下** | **却下** | 差し戻し状態。申請者が内容を修正して「再申請」することが可能です。 |

- **承認フローAPI**:
  - `PUT /api/surveys/{survey_id}/approve` - 承認
  - `PUT /api/surveys/{survey_id}/reject` - 却下
  - `PATCH /api/surveys/{survey_id}/toggle` - 公開/停止切り替え
- **データモデル**: `Survey` テーブルに `approval_status`, `is_active` カラムでステート管理
- **通知システム**: 承認・却下時に `backend/services/notification_service.py` を通じてユーザーに通知

#### 1.3 外部フォームのCSVインポート
- **実装**: `backend/api/dashboard.py::import_csv()` エンドポイント（システム管理者のみ）
- **処理フロー**:
  1. CSVファイルをアップロード
  2. 既存セッション選択、または新規セッション作成
  3. CSVの各行を `SurveyComment` として組織スコープ内に格納
  4. 既存の分析パイプラインで処理可能
- **セキュリティ**: `is_system_admin` デコレータによるアクセス制御

#### 1.4 管理者によるフォーム作成
- **実装**: `backend/api/survey.py::create_survey()` 
- **AIアシスト機能**: フォーム作成時に、質問案を自動生成する機能を提供（雑談掲示板分析結果を活用）

#### 1.5 フォーム回答のCSVエクスポート
- **実装**: `GET /api/surveys/{survey_id}/responses/csv`
- **機能**: フォームに対する全回答をCSV形式でダウンロード
- **用途**: 外部ツールでの分析、バックアップ、レポート作成
- **権限**: 組織管理者のみ

#### 1.6 申請フォームへのチャット
※ 議論機能を含みます。
- **実装**: `backend/api/survey.py`
  - `POST /api/surveys/{survey_id}/comments` - コメント投稿
  - `GET /api/surveys/{survey_id}/comments` - コメント一覧取得
- **データモデル**: `SurveyComment`
- **用途**: **一般ユーザーからのフォーム申請**に対する質問、内容の確認、議論（フォーム回答とは別の機能）
- **重要**: 
  - **管理者が直接作成したフォーム**（`approval_status="approved"`で作成）では、チャット機能は使用できません
  - チャット機能は**申請フロー**（一般ユーザー→管理者）専用の機能です
- **アクセス制御**: 
  - **バックエンドAPI**: 管理者または申請者（作成者本人）のみアクセス可能
  - **フロントエンド一覧表示**: 
    - 管理者: 全フォームが一覧に表示される
    - 一般ユーザー: 自分が作成した非公開フォームのみ一覧に表示（`!is_active`）
- **チャット表示条件（編集画面）**:
  - **申請中** (`pending`) または **却下** (`rejected`) のフォームを編集中の場合のみ、チャット欄が表示される
  - 承認済み・公開中のフォームでは、管理者・申請者ともにチャット欄は非表示

  | 作成者 | フォーム状態 | 管理者 | 申請者（作成者） | 備考 |
  | :--- | :--- | :---: | :---: | :--- |
  | 一般ユーザー | `pending`（申請中） | ✅ | ✅ | 申請内容の補足説明や質問が可能 |
  | 一般ユーザー | `rejected`（却下） | ✅ | ✅ | 却下理由の確認や修正相談が可能 |
  | 一般ユーザー | `approved` + `is_active=False`（承認済み・停止中） | ❌ | ❌ | チャット欄非表示、申請は完了済み |
  | 一般ユーザー | `approved` + `is_active=True`（公開中） | ❌ | ❌ | チャット欄非表示、申請は完了済み |
  | **管理者** | **`approved`（作成時から承認済み）** | **❌** | **-** | **チャット機能自体が不要（申請フローではない）** |

- **通知連携**: 
  - 管理者がコメント → 申請者に通知（`/dashboard?tab=requests`）
  - 申請者がコメント → 組織管理者全員に通知（`/dashboard?tab=surveys`）

### 2. 雑談掲示板
組織メンバーが自由に意見を投稿し、議論できる場を提供します。この掲示板の投稿は、AI分析によってフォーム作成の素材として活用されます（1.1参照）。

#### 2.1 基本機能
- **実装**: `backend/api/casual_chat.py`
- **API**:
  - `POST /api/casual/posts` - 投稿作成
  - `GET /api/casual/posts` - 投稿一覧取得（組織スコープ）
  - `POST /api/casual/posts/{post_id}/replies` - 返信投稿（ネストしたスレッド）
  - `POST /api/casual/posts/{post_id}/like` - いいね
- **データモデル**: 
  - `CasualPost` (投稿・返信を統合。parent_idで自己参照し、階層構造を実現)
  - `CasualPostLike` (いいね)
- **用途**: 
  - 日常的な業務の悩みや気づきの共有
  - 組織内の雰囲気醸成
  - フォーム化する前の「声」の収集

#### 2.2 AI分析結果の管理
- **実装**: `backend/api/casual_chat.py`
- **API**:
  - `POST /api/casual/analyze` - AI分析実行（フォーム推奨リスト生成）
  - `GET /api/casual/analyses` - 過去の分析結果一覧
  - `PATCH /api/casual/analyses/{analysis_id}/visibility` - 分析結果の表示/非表示切り替え
  - `DELETE /api/casual/analyses/{analysis_id}` - 分析結果削除
- **データモデル**: `CasualAnalysis` (分析結果、推奨フォーム案を保存)
- **機能**: 
  - 分析結果を保存し、後から参照可能
  - 管理者が分析結果の公開状態を制御
  - 不要な分析結果を削除

### 3. クラスタリング
管理画面の「分析」機能に対応します。収集されたフォーム回答やCSVデータを、AIがクラスタリングして視覚化・構造化します。

#### 3.1 分析セッション管理
- **実装**: `backend/api/dashboard.py`
- **API**:
  - `POST /api/dashboard/sessions/analyze` - 新規分析セッション作成＋AI分析実行
  - `GET /api/dashboard/sessions` - セッション一覧取得
  - `GET /api/dashboard/sessions/{session_id}` - セッション詳細取得
  - `DELETE /api/dashboard/sessions/{session_id}` - セッション削除
  - `PUT /api/dashboard/sessions/{session_id}/publish` - セッション公開/非公開切り替え
  - `POST /api/dashboard/sessions/{session_id}/comments/import` - CSVデータインポート
- **データモデル**: `AnalysisSession` (テーマ、タイトル、作成日時、組織ID、公開フラグ)
- **機能**:
  - 1つのセッションに、フォームの回答データまたはCSVデータを紐付け
  - クラスタリング結果、課題リスト、議論を一元管理
  - 公開設定により、一般メンバーへの表示/非表示を制御

#### 3.2 意味ベクトル化
- **実装**: `backend/services/analysis.py::get_vectors_semantic()`
- **手法**: 
  - **Sentence Transformers** (`paraphrase-multilingual-MiniLM-L12-v2`) をローカルで使用
  - 多言語対応の軽量モデルで、日本語テキストを高次元ベクトル空間に埋め込み
  - フォールバック: 失敗時はTF-IDF (文字n-gram) に自動切り替え

#### 3.3 外れ値検出
※ Small Voice (少数意見) の検出機能です。
- **実装**: `backend/services/analysis.py::detect_outliers()`
- **手法**:
  - **Isolation Forest** と **Local Outlier Factor (LOF)** を併用
  - 両者のスコアを正規化・平均化して `small_voice_score` を算出
  - 動的閾値調整: データ分布に応じて外れ値判定を適応的に変更
- **目的**: 少数意見を統計的に「ノイズ」として除外せず、重要な兆候として保持

#### 3.4 クラスタリング実行
- **実装**: `backend/services/analysis.py::analyze_clusters_logic()`
- **手法**:
  - **K-Means** によるクラスタリング（外れ値を除いた主要意見のみ対象）
  - **シルエットスコア** による最適クラスタ数の自動決定 (`get_optimal_k()`)
  - 並列処理: ThreadPoolExecutorによる高速化
- **クラスタ命名**: 
  - Gemini 2.0 Flash API を使用して、各クラスタの代表的なテキストから簡潔なラベルを生成
  - バッチ処理（5クラスタごと）で並列実行し、レイテンシを削減

#### 3.5 2次元可視化
- **実装**: `backend/services/analysis.py::analyze_clusters_logic()` 内でPCA実行
- **手法**: 
  - **PCA (主成分分析)** による2次元座標の算出（高速処理のためUMAPから変更）
  - フロントエンドで `react-plotly.js` を使用してインタラクティブな散布図を表示
  - 各点をクリックすると元のテキストを表示可能

### 4. 課題リスト
管理画面の「イシューリスト」機能に対応します。クラスタリング結果から、議論すべきアジェンダを自動生成します。

#### 4.1 実装
- **関数**: `backend/services/analysis.py::generate_issue_logic_from_clusters()`
- **API**: `GET /api/dashboard/sessions/{session_id}/issues` - 課題一覧取得
- **処理フロー**:
  1. 通常クラスタとSmall Voiceクラスタを分離
  2. Gemini 2.0 Flash Thinking API に以下を依頼:
     - マジョリティの課題 4つ（多数派の意見から）
     - Small Voiceの課題 1つ（少数意見の具体的な紹介）
  3. Small Voiceが存在しない場合は、「検出されませんでした」として空の項目を生成

#### 4.2 プロンプトエンジニアリング
- **マジョリティ課題**: 「〜の問題」ではなく「〜をどう乗り越えるか」といった建設的なタイトルを生成
- **Small Voice課題**: 
  - 分析や解釈を加えず、具体的な意見を列挙する形式
  - 背景の推測や過度な一般化を禁止（プロンプトで明示）

#### 4.3 データモデル
- **IssueDefinition**: 課題タイトル、関連トピック、洞察、ソースタイプ (`majority` | `small_voice`) をJSON形式で保持

### 5. 課題ごとの議論チャット
各課題に対して、メンバーが意見を投稿し、議論を深める空間を提供します。

- **API**: `backend/api/dashboard.py`
  - `POST /api/dashboard/sessions/{session_id}/comments` - コメント投稿
  - `GET /api/dashboard/sessions/{session_id}/comments` - コメント一覧取得（課題IDでフィルタ可能）
  - `PUT /api/dashboard/comments/{comment_id}` - コメント編集
  - `POST /api/dashboard/comments/{comment_id}/like` - いいね
- **データモデル**: 
  - `Comment` (親コメント) ↔ `CommentReply` (子コメント) の階層構造
  - `CommentLike` による「いいね」機能
- **機能**:
  - スレッド形式のリプライ
  - リアルタイム更新（ポーリング方式）
  - いいね数の表示
  - コメント編集（投稿者のみ）

### 6. AIファシリテーター
議論の内容を分析し、次のアクションを提案します。

#### 6.1 実装
- **関数**: `backend/services/analysis.py::analyze_thread_logic()`
- **API**: `POST /api/dashboard/sessions/{session_id}/analyze-thread`
- **入力**: `parent_comment_id` （スレッドのルートコメントID）
- **処理フロー**:
  1. `parent_comment_id` を起点に、すべての子コメント（リプライ）を再帰的に取得
  2. 時系列順に整理してプロンプトを構築
  3. Gemini 2.0 Flash Thinking API に議論内容を送信し、次のアクションを提案
  4. 結果を返却（フロントエンドでアコーディオン形式で表示）

#### 6.2 プロンプト設計
- **役割**: 中立的かつ理性的なプロのファシリテーター（診断や分析ではなく、合意形成のためのサポートを提供）
- **出力形式**: JSON形式で「論点」と「次のアクション」を構造化

### 7. マルチテナント構成
※ 組織管理機能の実装詳細です。
複数の組織が同一システムを利用し、データが論理的に分離される設計です。

#### 7.1 権限モデル
| 役割 | 権限範囲 | データモデル |
| :--- | :--- | :--- |
| **システム管理者** | 全組織の管理、ユーザー作成、組織作成 | `User.role = "system_admin"` |
| **組織管理者** | 所属組織内のフォーム管理、分析実行 | `OrganizationMember.role = "admin"` |
| **一般ユーザー** | フォーム回答、申請、議論参加 | `OrganizationMember.role = "general"` |

#### 7.2 多重所属
- **仕組**: `OrganizationMember` テーブルで `user_id` と `organization_id` の多対多関係を実現
- **ユースケース**: 
  - 1人のユーザーが、複数の部署・プロジェクトに参加
  - 各組織内で異なる役割を持つことが可能（例: A組織は一般、B組織は管理者）

#### 7.3 組織切り替え
- **実装**: `POST /api/auth/switch-org` 
- **機能**: 所属する組織間での切り替え。Cookieに現在の組織コンテキストを保存し、全APIがこれを参照

#### 7.4 組織管理機能
※ システム管理者専用です。
- **API**: `backend/api/organization.py`
  - `POST /api/organizations` - 組織作成
  - `GET /api/organizations` - 組織一覧
  - `PUT /api/organizations/{id}` - 組織情報更新
  - `DELETE /api/organizations/{id}` - 組織削除
  - `POST /api/organizations/{id}/members` - メンバー追加
  - `GET /api/organizations/{id}/members` - メンバー一覧
- **権限**: システム管理者のみ

### 8. ユーザー管理
システム管理者が全ユーザーを管理できます。

#### 8.1 ユーザーCRUD
- **API**: `backend/api/users.py`
  - `POST /api/users` - 新規ユーザー作成（システム管理者のみ）
  - `GET /api/users` - ユーザー一覧取得
  - `PUT /api/users/{id}` - ユーザー情報更新（システム管理者のみ）
  - `DELETE /api/users/{id}` - ユーザー削除（システム管理者のみ）
- **機能**:
  - 初期パスワード自動生成
  - メールによる招待通知
  - 組織への自動紐付け
  - ロール設定 (`system_admin` /` system_user`)

#### 8.2 プロフィール設定
- **API**: `PUT /api/auth/me`
- **機能**: ユーザー自身が自分の情報（氏名、パスワード）を更新可能

### 9. 認証とセキュリティ
ユーザー認証とセッション管理を提供します。

#### 9.1 認証機能
- **実装**: `backend/api/auth.py`, `backend/security_utils.py`
- **API**:
  - `POST /api/auth/login` - ログイン（メール・パスワード）
  - `POST /api/auth/logout` - ログアウト
  - `GET /api/auth/me` - 現在のユーザー情報取得
  - `GET /api/auth/my-orgs` - 自分が所属する組織一覧
  - パスワードリセット、招待リンク生成/検証

#### 9.2 招待リンク機能
- **実装**: `backend/api/auth.py`
- **処理フロー**:
  1. システム管理者が招待トークンを発行
  2. ユーザーが招待リンクをクリックし、初回パスワードを設定
  3. 組織に自動的に所属

#### 9.3 パスワードリセット
- **実装**: `backend/api/auth.py`, `backend/services/email_service.py`
- **処理フロー**:
  1. ユーザーがメールアドレスを入力
  2. リセットトークンを生成し、メール送信
  3. リンク経由で新しいパスワードを設定
- **メール送信**: `backend/services/email_service.py` を使用

### 10. 通知システム
システム全体のイベントをユーザーに通知します。権限と公開状態に応じて、適切な対象者に配信されます。

- **実装**: `backend/services/notification_service.py`, `backend/api/notifications.py`
- **データモデル**: `Notification` テーブル（`type`, `title`, `content`, `link`, `organization_id`, `is_read`, `created_at`）
- **API**: 
  - `GET /api/notifications` - 通知一覧取得（最新99件）
  - `POST /api/notifications/{id}/read` - 個別既読マーク
  - `POST /api/notifications/read-all` - 一括既読マーク

#### 通知の種類と対象者

| 通知タイプ | トリガー | 対象者 | 権限条件 | リンク先 | 実装箇所 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`form_applied`** | フォーム新規申請、再申請 | 組織管理者、システム管理者 | 申請者を除く全管理者 | `/dashboard?tab=surveys` | survey.py:112, 408 |
| **`form_approved`** | フォーム申請承認 | 申請者本人 | 申請者のみ | `/dashboard?tab=requests` | survey.py:503 |
| **`form_rejected`** | フォーム申請却下 | 申請者本人 | 申請者のみ | `/dashboard?tab=requests` | survey.py:538 |
| **`chat_new`** (申請チャット) | 申請フォームへのコメント投稿 | 管理者 or 申請者 | 投稿者以外の関係者 | `/dashboard?tab=surveys` (管理者) <br> `/dashboard?tab=requests` (申請者) | survey.py:608, 619 |
| **`survey_released`** | フォーム公開 | 組織全メンバー | 公開者を除く全員 | `/dashboard?tab=answers` | survey.py:469 |
| **`report_published`** | 分析レポート公開 | 組織全メンバー | 公開者を除く全員 | `/dashboard?tab=reports` | dashboard.py:209 |
| **`report_published`** (AI分析更新) | AIスレッド分析実行・更新 | **公開中**: 組織全メンバー<br>**未公開**: 組織管理者のみ | 公開状態による | `/dashboard/sessions/{id}?title={議題}` | dashboard.py:565, 576 |
| **`chat_new`** (レポート議論) | レポート課題チャットへのコメント投稿 | **公開中**: 組織全メンバー<br>**未公開**: 組織管理者のみ | 公開状態&投稿者除く | `/dashboard/sessions/{id}?title={議題}` | dashboard.py:416, 427 |
| **`chat_new`** (雑談掲示板) | 雑談掲示板への投稿・返信 | 組織全メンバー | 投稿者を除く全員 | `/dashboard?tab=casual` | casual_chat.py:70 |
| **`casual_suggestion`** | 雑談AI提案公開 | 組織全メンバー | 公開者を除く全員 | `/dashboard?tab=casual` | casual_chat.py:305 |

#### 通知の基本ルール
- **自己除外**: 自身の操作による通知は自分には届かない（`exclude_user_id`パラメータで制御）
- **組織スコープ**: 通知は組織単位で管理され、所属組織のイベントのみ通知
- **権限による制限**: 
  - **管理者**: 未公開レポートの通知、申請フローの通知を受信
  - **一般ユーザー**: 公開済みコンテンツの通知のみ受信
- **最大表示件数**: 最新99件まで表示
- **日本時間**: 通知時刻はJST（日本時間）で表示
- **自動遷移**: 通知クリック時に該当ページへ遷移し、レポート関連の通知では該当する議論スレッドが自動的に開く

#### 通知サービスの関数
- **`create_notification(db, user_id, type, title, content, link, organization_id)`**: 特定のユーザーに通知を作成
- **`notify_organization_members(db, organization_id, type, title, content, link, exclude_user_id)`**: 組織の全メンバーに通知（`exclude_user_id` を除く）
- **`notify_organization_admins(db, organization_id, type, title, content, link, exclude_user_id)`**: 組織管理者とシステム管理者全員に通知（`exclude_user_id` を除く)


## 技術スタック

本システムは、モダンなWebアプリケーションフレームワークと最新のAI技術を組み合わせた構成となっています。フロントエンドはNext.js（App Router）、バックエンドはFastAPI、データベースはPostgreSQLを採用し、AI分析にはGoogle Gemini APIとSentence Transformersを活用しています。

### Frontend
- **フレームワーク**: Next.js 16.1.1 (App Router)
- **言語**: TypeScript 5
- **UIライブラリ**: React 19.2.3
- **スタイリング**: Tailwind CSS 4, Lucide React 0.562.0
- **データ可視化**: 
  - Plotly.js 3.3.1
  - react-plotly.js 2.6.0
- **リッチテキストエディタ**: 
  - TipTap 3.14.0 (React, Starter Kit, Extensions)
  - tiptap-markdown 0.9.0
- **マークダウン表示**: 
  - react-markdown 10.1.0
  - remark-gfm 4.0.1 (GitHub Flavored Markdown)
  - remark-breaks 4.0.0
- **HTTP通信**: axios 1.13.2
- **日付処理**: date-fns 4.1.0
- **ビルドツール**: @tailwindcss/postcss 4
- **Lint**: ESLint 9, eslint-config-next 16.1.1

### Backend
- **フレームワーク**: FastAPI (Python 3.10+)
- **Webサーバー**: Uvicorn
- **ORM**: SQLAlchemy
- **データベース**: PostgreSQL (psycopg2-binary)
- **マイグレーション**: Alembic
- **認証**: 
  - Bcrypt (パスワードハッシュ化)
  - データベースバックエンドのセッション管理
- **AI/LLM**: 
  - **Google Gemini 2.0 Flash Thinking Exp**: 課題抽出、深層分析、ファシリテーション
  - **Google Gemini 2.0 Flash Exp**: クラスタ命名、要約生成
  - ※ APIキーは環境変数 `GEMINI_API_KEY` で管理
- **機械学習**: 
  - **Sentence Transformers** (`paraphrase-multilingual-MiniLM-L12-v2`): 意味ベクトル化
  - **scikit-learn**: K-Means, PCA, Isolation Forest, LOF, Silhouette Score
  - **HDBSCAN** 0.8.33+: 密度ベースクラスタリング（コード内で定義済みだがPCAに切り替え）
  - **UMAP** 0.5.0+: 非線形次元削減（コード内で定義済みだがPCAに切り替え）
- **データ処理**: Pandas, NumPy
- **その他**: 
  - python-multipart (ファイルアップロード)
  - python-dotenv (環境変数管理)
  - Plotly (グラフ生成補助)

### インフラ
- **コンテナ**: Docker, Docker Compose
- **開発環境**: `docker-compose.dev.yml`
- **本番環境**: `docker-compose.prod.yml`
- **Webサーバー（本番）**: Nginx (リバースプロキシ)

## AI分析とアルゴリズム詳細

本セクションでは、Small Voiceの核心機能である4つのAI分析の具体的なアルゴリズムと実装詳細を説明します。各分析の入力・出力・処理ステップ・プロンプト戦略を詳しく記載しています。

### 1. 掲示板分析
※ 雑談掲示板からフォームを推奨する機能です。
- **関数**: `backend/services/analysis.py::analyze_casual_posts_logic()`
- **入力**: `CasualPost` オブジェクトのリスト
- **出力**: 
  ```json
  {
    "recommendations": [
      {
        "title": "アンケートのタイトル案",
        "reason": "なぜいまアンケートをとるべきかの理由（管理者向け）",
        "survey_description": "回答者に表示する説明文",
        "suggested_questions": ["質問案1", "質問案2"]
      }
    ]
  }
  ```
- **プロンプト戦略**:
  - 個人の愚痴ではなく、組織全体の課題として扱うべきテーマを抽出
  - 潜在的な不満や新しいアイデアの芽を見つけ出す
  - 全ての質問は自由記述形式（回答形式の指定を禁止）
- **API実装**: `POST /api/casual/analyze` (`backend/api/casual_chat.py`)

### 2. クラスタリング分析
※ アンケート回答データの意味分類です。
- **関数**: `backend/services/analysis.py::analyze_clusters_logic()`
- **処理ステップ**:
  1. **意味ベクトル化**: 
     - Sentence Transformers でテキストを384次元ベクトルに変換
     - フォールバック: TF-IDF (文字1-3gram)
  2. **外れ値検出**: 
     - Isolation Forest (汚染度10%)
     - Local Outlier Factor (k=20, 汚染度10%)
     - スコア平均化 → 閾値0.65以上を外れ値とマーク
     - 動的調整: 外れ値が30%超の場合は閾値を0.9に引き上げ
  3. **クラスタリング**: 
     - 外れ値を除いたデータに対してK-Meansを実行
     - 最適K: シルエットスコアで自動決定（範囲: 2～min(√N, 20)）
     - 並列処理: ThreadPoolExecutor (最大8ワーカー)
  4. **2次元投影**: 
     - PCA (n_components=2) で2次元座標を算出
     - 微小なジッター追加で重複点を視覚的に分離
  5. **クラスタ命名**: 
     - 各クラスタの重心から最も近い5サンプルを抽出
     - Gemini 2.0 Flash に渡し、10文字以内の体言止めラベルを生成
     - バッチサイズ5、並列ワーカー3で効率化
- **出力**: 各テキストに対して以下を付与
  - `sub_topic`: クラスタ名
  - `x_coordinate`, `y_coordinate`: 2D座標
  - `cluster_id`: クラスタID (-1は外れ値)
  - `is_noise`: 外れ値フラグ
  - `summary`: テキスト要約（60文字）

### 3. 課題リスト生成
※ クラスタから議論アジェンダを生成します。
- **関数**: `backend/services/analysis.py::generate_issue_logic_from_clusters()`
- **入力**: クラスタリング結果のDataFrame
- **処理ステップ**:
  1. 通常クラスタ (`cluster_id != -1`) と Small Voice (`cluster_id == -1`) を分離
  2. 各クラスタの代表サンプルを抽出（30%、最小10件、最大100件）
  3. Gemini 2.0 Flash Thinking に以下を依頼:
     - **マジョリティ課題**: 4つ（多数派の意見から組織的課題を抽出）
     - **Small Voice課題**: 1つ（具体的な意見を列挙、解釈を加えない）
  4. Small Voiceが存在しない場合は、「検出されませんでした」として空項目を生成
- **プロンプト戦略**:
  - マジョリティ課題: 「〜の問題」ではなく「〜をどう乗り越えるか」形式
  - Small Voice課題: 
    - タイトル固定: 「Small Voice」
    - `related_topics`: `["Small Voice (特異点)"]`
    - `insight`: 「以下のような意見がありました」+ 具体的意見の列挙
    - 禁止事項: 背景推測、過度な一般化、元発言にない解釈
- **出力**: 
  ```json
  {
    "issues": [
      {
        "title": "議題タイトル",
        "related_topics": ["カテゴリ名"],
        "insight": "なぜこれを議論すべきか...",
        "source_type": "majority" | "small_voice"
      }
    ]
  }
  ```

### 4. AIファシリテーター
※ 議論スレッドから次のアクションを提案します。
- **関数**: `backend/services/analysis.py::analyze_thread_logic()`
- **入力**: コメントリスト（親+子、各要素に `content`, `user_name`, `created_at`）
- **処理ステップ**:
  1. コメントをフォーマット化: `[ユーザー名] コメント内容\n`
  2. Gemini 2.0 Flash に議論の流れを渡す
  3. AIが以下を生成:
     - `next_steps`: 次にとるべき具体的なアクション（最大3つ）
       - `title`: アクションの見出し（20文字以内）
       - `detail`: 具体的な内容、担当者、期限の目安、背景説明
- **プロンプト設計**:
  - 役割: 中立的かつ理性的なプロのファシリテーター
  - 目的: 議論を停滞させず、具体的かつ実行可能な解決策を提示
  - 出力要件: なぜそのアクションが必要なのかという背景（論点）を含める
- **出力**: 
  ```json
  {
    "next_steps": [
      {"title": "見出し...", "detail": "詳細..."}
    ]
  }
  ```

## ディレクトリ構造

プロジェクト全体のファイル・フォルダ構成を示します。Backend（FastAPI）、Frontend（Next.js）、データベースマイグレーション（Alembic）、運用スクリプト、ドキュメントなど、主要なディレクトリとファイルを記載しています。

```
small-voice-project/
├── backend/                    # Backend Application (FastAPI)
│   ├── api/                    # API Endpoints (Routers)
│   │   ├── auth.py             # 認証・セッション管理
│   │   ├── survey.py           # アンケート管理・承認フロー
│   │   ├── dashboard.py        # ダッシュボード、分析セッション、課題、コメント、CSVインポート
│   │   ├── casual_chat.py      # 雑談掲示板（投稿・返信・いいね・AI分析）
│   │   ├── organization.py     # 組織管理
│   │   ├── users.py            # ユーザー管理
│   │   └── notifications.py    # 通知API
│   ├── services/               # ビジネスロジック層
│   │   ├── analysis.py         # AI分析のコアロジック（クラスタリング、課題抽出、ファシリテーター）
│   │   ├── email_service.py    # メール送信サービス
│   │   ├── notification_service.py  # 通知作成ロジック
│   │   └── mock_generator.py   # テストデータ生成（モック）
│   ├── database.py             # SQLAlchemyモデル定義とDBセッション管理
│   ├── security_utils.py       # パスワードハッシュ化、セッション検証
│   ├── utils.py                # 共通ユーティリティ（モデル名、APIキー読み込み）
│   ├── main.py                 # FastAPIアプリのエントリーポイント
│   └── Dockerfile              # Backendコンテナイメージ
├── frontend/                   # Frontend Application (Next.js)
│   ├── src/
│   │   ├── app/                # App Router Pages
│   │   │   ├── login/          # ログインページ
│   │   │   ├── dashboard/      # メインダッシュボード
│   │   │   │   ├── surveys/    # アンケート管理ページ
│   │   │   │   ├── sessions/   # 分析セッション一覧・詳細
│   │   │   │   └── page.tsx    # ダッシュボードホーム
│   │   │   ├── admin/          # システム管理者ページ（組織管理、CSVインポート）
│   │   │   ├── survey/         # フォーム回答ページ（公開フォーム）
│   │   │   ├── invite/         # 招待リンク受付
│   │   │   └── forgot-password/ # パスワードリセット
│   │   ├── components/         # 再利用可能なUIコンポーネント
│   │   │   ├── dashboard/      # ダッシュボード専用コンポーネント
│   │   │   │   ├── PlotChart.tsx        # Plotlyグラフ（クラスタ可視化）
│   │   │   │   ├── IssueList.tsx        # 課題リスト表示
│   │   │   │   ├── CommentSection.tsx   # コメント・リプライUI
│   │   │   │   ├── AIFacilitatorPanel.tsx # AIファシリテーター結果表示
│   │   │   │   ├── SurveyFormModal.tsx  # フォーム作成・編集モーダル
│   │   │   │   └── ...
│   │   │   ├── admin/          # 管理者用コンポーネント
│   │   │   │   ├── OrganizationManagement.tsx
│   │   │   │   └── CSVImport.tsx
│   │   │   ├── ui/             # 汎用UIコンポーネント（ボタン、モーダル等）
│   │   │   └── Sidebar.tsx     # グローバルサイドバー
│   │   └── types/              # TypeScript型定義
│   ├── middleware.ts           # Next.js認証ミドルウェア
│   ├── package.json
│   └── Dockerfile              # Frontendコンテナイメージ
├── alembic/                    # DBマイグレーション管理
│   ├── versions/               # マイグレーションスクリプト
│   ├── env.py
│   └── alembic.ini
├── scripts/                    # 運用スクリプト
│   ├── seed_db.py              # 初期データ投入（組織、ユーザー、テストデータ）
│   ├── generate_test_data.py   # テストデータ生成（CSV出力）
│   ├── generate_new_forms_test_data.py  # 新フォーム形式のテストデータ生成
│   ├── reset_db_clean.py       # DB初期化
│   └── deploy_prod.sh          # 本番デプロイスクリプト
├── nginx/                      # 本番環境のNginx設定
├── docs/                       # プロジェクトドキュメント
│   ├── architecture.md         # 本ドキュメント
│   ├── database.md             # データベース設計
│   ├── local_development_setup.md  # ローカル開発環境構築
│   ├── production_deployment_guide.md  # 本番デプロイ手順
│   ├── db_connection_guide.md  # 本番DB接続手順
│   └── user_manual.md          # ユーザー利用マニュアル
├── outputs/                    # 分析結果出力（CSV、レポート等）
├── docker-compose.yml          # 基本構成
├── docker-compose.dev.yml      # 開発環境
├── docker-compose.prod.yml     # 本番環境
├── alembic.ini                 # Alembic設定
├── requirements.txt            # Python依存パッケージ
├── .env                        # 環境変数（Gitignore対象）
└── README.md                   # プロジェクト概要
```

## コンポーネント詳細

本セクションでは、BackendとFrontendの各コンポーネントの役割と実装詳細を説明します。APIエンドポイント、Service層の関数、データベースモデル、Reactコンポーネントなど、実装に直結する情報を提供します。

### Backend

#### API層
`backend/api/`
各ルーターは、認証・権限チェックを行った上で、Service層やDatabase層を呼び出します。

- **`auth.py`**: 
  - `POST /api/auth/login` - ログイン、セッション作成
  - `POST /api/auth/logout` - ログアウト、セッション削除
  - `GET /api/auth/me` - 現在のユーザー情報取得
  - `POST /api/auth/switch-org` - 組織切り替え
  - `GET /api/auth/my-orgs` - 自分が所属する組織一覧
  - パスワードリセット、招待リンク生成/検証
- **`survey.py`**: 
  - `POST /api/surveys` - フォーム作成（一般ユーザー: 申請、管理者: 直接作成）
  - `GET /api/surveys` - フォーム一覧（状態フィルタ: 申請中/承認済み/却下/公開中）
  - `PUT /api/surveys/{id}/approve` - 承認（組織管理者のみ）
  - `PUT /api/surveys/{id}/reject` - 却下（組織管理者のみ）
  - `PATCH /api/surveys/{id}/toggle` - 公開/停止切り替え（組織管理者のみ）
  - `POST /api/surveys/{id}/response` - フォーム回答送信
  - `GET /api/surveys/{id}/responses/csv` - フォーム回答CSVエクスポート（組織管理者のみ）
  - `GET /api/surveys/{uuid}` - 公開フォームの取得（UUID指定、認証不要）
- **`dashboard.py`**: 
  - **分析セッション管理**:
    - `POST /api/dashboard/sessions/analyze` - 新規分析セッション作成＋AI分析実行
    - `GET /api/dashboard/sessions` - セッション一覧取得
    - `GET /api/dashboard/sessions/{session_id}` - セッション詳細取得
    - `DELETE /api/dashboard/sessions/{session_id}` - セッション削除
    - `PUT /api/dashboard/sessions/{session_id}/publish` - セッション公開/非公開切り替え
  - **課題生成・取得**:
    - `GET /api/dashboard/sessions/{session_id}/issues` - 課題一覧取得
  - **コメント・議論**:
    - `POST /api/dashboard/sessions/{session_id}/comments` - コメント投稿
    - `PUT /api/dashboard/comments/{comment_id}` - コメント編集
    - `POST /api/dashboard/comments/{comment_id}/like` - いいね
  - **AIファシリテーター**:
    - `POST /api/dashboard/sessions/{session_id}/analyze-thread` - 議論スレッド分析、次のアクション提案
  - **CSVインポート**:
    - `POST /api/dashboard/sessions/{session_id}/comments/import` - 既存セッションへCSVデータ取り込み
- **`casual_chat.py`**: 
  - `POST /api/casual/posts` - 投稿作成
  - `GET /api/casual/posts` - 投稿一覧取得
  - `POST /api/casual/posts/{id}/replies` - 返信投稿
  - `POST /api/casual/posts/{id}/like` - いいね
  - `POST /api/casual/analyze` - AI分析、フォーム推奨リスト生成
  - `GET /api/casual/analyses` - 過去の分析結果一覧
  - `PATCH /api/casual/analyses/{analysis_id}/visibility` - 分析結果表示/非表示切り替え
  - `DELETE /api/casual/analyses/{analysis_id}` - 分析結果削除
- **`organization.py`**: 
  - `POST /api/organizations` - 組織作成（システム管理者のみ）
  - `GET /api/organizations` - 組織一覧
  - `POST /api/organizations/{id}/members` - メンバー追加
  - `GET /api/organizations/{id}/members` - メンバー一覧
- **`users.py`**: 
  - `POST /api/users` - ユーザー作成（システム管理者のみ）
  - `GET /api/users` - ユーザー一覧
  - `PUT /api/users/{id}` - ユーザー情報更新
- **`notifications.py`**: 
  - `GET /api/notifications` - 通知一覧取得
  - `PUT /api/notifications/{id}/read` - 既読マーク

#### Service層
`backend/services/`
ビジネスロジックとAI処理を担当します。

- **`analysis.py`**: 
  - `analyze_clusters_logic()` - クラスタリング分析の中核
  - `generate_issue_logic_from_clusters()` - 課題リスト生成
  - `analyze_thread_logic()` - 議論スレッドのAI分析
  - `analyze_casual_posts_logic()` - 雑談掲示板のAI分析
  - `get_vectors_semantic()` - Sentence Transformersによるベクトル化
  - `detect_outliers()` - Isolation Forest + LOFによる外れ値検出
  - `get_optimal_k()` - シルエットスコアによる最適クラスタ数決定
- **`email_service.py`**: 
  - `send_email()` - SMTP経由でメール送信
  - パスワードリセット、招待リンクの送信に使用
- **`notification_service.py`**: 
  - `create_notification()` - 通知レコード作成
  - コメント、リプライ時に自動実行
- **`mock_generator.py`**: 
  - テストデータ生成用のモックテキスト生成

#### データベース
`database.py`
SQLAlchemyモデル定義とDB接続管理。

**主要モデル**:
- **User**: ユーザー情報、パスワードハッシュ、ロール (`system_admin`, `admin`, `general`)
- **UserSession**: セッショントークン、有効期限
- **Organization**: 組織情報
- **OrganizationMember**: ユーザー↔組織の多対多関係、組織内ロール
- **Survey**: アンケートフォーム（タイトル、説明、質問、承認ステータス、公開フラグ）
- **Question**: フォームの質問
- **Answer**: ユーザーの回答
- **AnalysisSession**: 分析セッション（テーマ、作成日時、組織ID）
- **AnalysisResult**: クラスタリング結果（元テキスト、クラスタID、座標、サブトピック）
- **IssueDefinition**: 分析セッションの課題定義レポート（JSON形式で課題リストを保存）
- **Comment**: 課題へのコメント（親コメント、階層構造でリプライをサポート）
- **CommentLike**: コメントへのいいね
- **SurveyComment**: アンケート回答に紐づくコメント（CSVインポート時にも使用）
- **CasualPost**: 雑談掲示板の投稿（parent_idで自己参照、返信も同じモデルで扱う）
- **CasualPostLike**: 投稿へのいいね
- **CasualAnalysis**: 雑談掲示板のAI分析結果（推奨フォーム案を保存）
- **Notification**: 通知（タイプ、リンク、既読フラグ）

#### セキュリティ
`security_utils.py`
- `verify_password()` - Bcryptによるパスワード検証
- `hash_password()` - パスワードハッシュ化
- `get_current_user()` - セッショントークンからユーザー取得
- `is_org_admin()` - 組織管理者権限チェック
- `is_system_admin()` - システム管理者権限チェック

### Frontend

#### App Router
`src/app/`
Next.js 13+ のApp Routerを使用したページ構成。

- **`/login`**: ログインページ
- **`/dashboard`**: メインダッシュボード（ホーム）
  - **`/dashboard/surveys`**: アンケート管理（作成・編集・承認・公開）
  - **`/dashboard/sessions`**: 分析セッション一覧
    - **`/dashboard/sessions/[id]`**: 分析詳細（クラスタ可視化・課題リスト・議論）
  - **`/dashboard/casual-chat`**: 雑談掲示板
  - **`/dashboard/notifications`**: 通知一覧
- **`/admin`**: システム管理者専用
  - 組織管理、ユーザー管理、CSVインポート
- **`/survey/[uuid]`**: 公開フォーム回答ページ（認証不要）
- **`/invite/[token]`**: 招待リンク受付
- **`/forgot-password`**: パスワードリセット

#### Components
`src/components/`
再利用可能なReactコンポーネント。

**ダッシュボード関連** (`dashboard/`):
- **`PlotChart.tsx`**: Plotly.jsを使用したインタラクティブな散布図
- **`IssueList.tsx`**: 課題リスト表示、Small Voiceの特別表示
- **`CommentSection.tsx`**: コメント・リプライのスレッド表示、いいね機能
- **`AIFacilitatorPanel.tsx`**: AIファシリテーターの分析結果表示（アコーディオン形式）
- **`SurveyFormModal.tsx`**: フォーム作成・編集モーダル、AI質問案生成
- **`AnalysisSessionList.tsx`**: 分析セッション一覧カード表示
- **`CasualChatBoard.tsx`**: 雑談掲示板UI、投稿・返信・いいね
- **`NotificationBell.tsx`**: 通知ベルアイコン、未読数表示

**管理者関連** (`admin/`):
- **`OrganizationManagement.tsx`**: 組織CRUD、メンバー管理
- **`CSVImport.tsx`**: CSVアップロード、セッション選択UI

**汎用UI** (`ui/`):
- **`Button.tsx`**: 共通ボタンコンポーネント
- **`Modal.tsx`**: モーダルダイアログ
- **`LoadingSpinner.tsx`**: ローディング表示

**グローバル**:
- **`Sidebar.tsx`**: サイドバーナビゲーション、組織切り替え、ロール別メニュー表示

### Database
- **PostgreSQL**: 本番環境で使用
- **SQLite**: 開発環境でも使用可能（`database.py` でURI切り替え）
- **Alembic**: マイグレーション管理（`alembic/versions/` にバージョン履歴）

### Scripts
`scripts/`
- **`seed_db.py`**: 
  - 初期データ投入（組織、ユーザー、テストアンケート、雑談投稿）
  - 複雑な組織階層（部署・プロジェクト）とユーザーの多重所属シナリオ
- **`generate_test_data.py`**
- **`generate_new_forms_test_data.py`**
- **`reset_db_clean.py`**
- **`deploy_prod.sh`**
