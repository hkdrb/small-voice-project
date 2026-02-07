# クラスタリング図への自動スクロール実装計画

「Small Voice」内の個別の意見をクリックした際、ページ上部のクラスタリング図（Meaning Map）が画面内に収まるように自動スクロールする機能を追加します。

## 変更内容

### Frontend

#### [MODIFY] [page.tsx](file:///Users/koderahayato/small-voice-project/frontend/src/app/dashboard/sessions/[id]/page.tsx)

1. **Refの追加**:
   - `mapSectionRef` ステート（`useRef<HTMLElement>(null)`）を追加します。
   - クラスタリング図を囲む `<section className="glass-card p-4 h-[500px] relative">` にこのRefをアタッチします。

2. **スクロールロジックの実装**:
   - Small Voiceの個別意見（ボタン）の `onClick` ハンドラ内で、`setHighlightedText(text)` を呼び出した後、`mapSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })` を実行します。

## 検証プラン

### 手動検証
1. 「Small Voice」課題を展開し、下にスクロールして個別の意見を表示する。
2. リンク化された意見をクリックする。
3. ページがスムーズに上部のクラスタリング図までスクロールし、該当する点がハイライトされていることを確認する。
