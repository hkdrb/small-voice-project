# 実装計画: ER図のMermaid化とPNG生成

## 1. Mermaidファイルの作成
`docs/images/er_diagram.mmd` を新規作成し、以下の内容を記述する。
- エンティティ定義 (各テーブルと主要なカラム)
- リレーション定義 (主要なFKのみ)
- スタイル定義 (`classDef` と `class` 割り当て)

### カラーパレット計画
- **User/Org**: fill:#E1F5FE, stroke:#01579B
- **Survey**: fill:#E8F5E9, stroke:#2E7D32
- **Analysis**: fill:#FFF3E0, stroke:#EF6C00
- **Casual**: fill:#F3E5F5, stroke:#7B1FA2
- **Notification**: fill:#FFEBEE, stroke:#C62828

## 2. PNG画像の生成
Mermaid CLI (`mmdc`) が環境にない可能性があるため、以下の手順でPNGを生成する。
1. `temp_er_diagram.html` を作成し、Mermaid.js (CDN) を読み込み、作成した `.mmd` の内容を描画するスクリプトを埋め込む。
2. `browser_subagent` を使用してこのHTMLを開く。
3. ブラウザ上でレンダリングされたSVG部分のスクリーンショット、またはページ全体のスクリーンショットを撮影する。
4. 撮影した画像を `docs/images/er_diagram.png` として保存する。

## 3. ファイルの整理
- `temp_er_diagram.html` は削除する。
- 既存の `generate_diagram.py` と古い `er_diagram.svg` は、ユーザーの指示がない限り残すが、今回はリプレイスの意図があるため、`er_diagram.png` は上書きする。

## 検証
- GitHub等でMarkdownとして見た場合も意図通り表示されるか (GitHubは `classDef` をサポートしているか確認が必要だが、今回はPNG納品が主目的)。
- 画像が見やすいか (線が多すぎないか)。
