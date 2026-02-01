
import json
import logging
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import google.generativeai as genai
from backend.utils import MODEL_NAME, MODEL_NAME_THINKING, MODEL_NAME_LIGHT, EMBEDDING_MODEL_NAME, GEMINI_API_KEY, logger
import pandas as pd
import umap
import hdbscan

# No global model cache needed for API-based embeddings

def get_batch_sentiments(texts):
    """
    発言リストに対して個別に感情分析を行い、スコアのリストを返します。
    -1.0 (極めてネガティブ) 〜 1.0 (極めてポジティブ)
    """
    if not texts:
        return []
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME_LIGHT)
    
    batch_size = 50
    all_scores = [0.0] * len(texts)
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        prompt = f"""
あなたは心理言語学者、および組織診断の専門家です。
以下の社員の声（日本語）のリストを読み、各発言の感情スコアを **-1.0 から 1.0 の範囲** で付けてください。

### 評価のルール:
1. **中立バイアスの打破**: 日本人の「〜かもしれない」「特にはないが〜」といった表現は、背後に強い不満や不安、あるいは期待が隠れていることが多いです。**安易に 0.0 を使わず、心理的な揺らぎを ±0.1〜0.4 などの範囲で積極的にスコアリングしてください。**
2. **文脈の重視**: 
   - 「改善してほしい」＝ 現状への不満（ネガティブ）
   - 「素晴らしい」＝ 満足（ポジティブ）
   - 「特にありません」＝ 諦めや関心の低さ（ややネガティブ寄り -0.1 〜 -0.2 と判定することも検討）
3. **極端なスコア**: 離職、ハラスメント、不正、絶望などを感じさせるものは -0.8 以下。強い感謝や意欲は 0.8 以上。

### スコアの目安:
- **-1.0 〜 -0.7**: 強い憤り、メンタル不調、離職の意志、不正への警鐘、絶望。
- **-0.6 〜 -0.4**: 明確な不満、非効率への苛立ち、環境への失望。
- **-0.3 〜 -0.1**: 違和感、改善を求めている、慎重な懸念、諦め。
- **0.0**: 客観的な事実の報告のみ（例：「昨日10時に会議があった」）。
- **0.1 〜 0.3**: 前向きな提案、改善への意欲、控えめな称賛。
- **0.4 〜 0.6**: 感謝、手応え、環境への満足。
- **0.7 〜 1.0**: 高いモチベーション、組織への強い信頼、卓越した成果への喜び。

### 出力形式:
JSON配列のみを出力してください。例: [-0.45, 0.12, -0.2, 0.0, 0.85]
余計な解説やマークダウンは一切含めないでください。

対象リスト:
{json.dumps(batch, ensure_ascii=False)}
"""
        try:
            resp = model.generate_content(prompt)
            text = resp.text.strip()
            
            # Remove markdown logic
            text = text.replace("```json", "").replace("```", "").strip()
            
            # Robust extraction of anything that looks like a list
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                text = match.group(0)
            
            scores = json.loads(text)
            if isinstance(scores, list):
                for idx, score in enumerate(scores):
                    if i + idx < len(all_scores):
                        all_scores[i + idx] = float(score)
        except Exception as e:
            logger.error(f"Batch sentiment analysis failed (batch {i}): {e}")
            
    return all_scores

def get_vectors_semantic(texts):
    """Generate semantic embeddings using Gemini Embeddings API."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Gemini embedding-004 supports batching (usually up to 100 or 2048 depending on version)
        # We'll batch to be safe and efficient if user has many texts
        batch_size = 100
        vectors = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            result = genai.embed_content(
                model=EMBEDDING_MODEL_NAME,
                content=batch_texts,
                task_type="clustering"
            )
            # result['embedding'] is a list of lists if input is a list
            vectors.extend(result['embedding'])
            
        return np.array(vectors)
    except Exception as e:
        logger.exception(f"Semantic vectorization with Gemini failed: {e}")
        # Fallback to TF-IDF
        return get_vectors_tfidf(texts)

def get_vectors_tfidf(texts):
    """Generate TF-IDF vectors (Character N-grams for Japanese) - Fallback method."""
    try:
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), min_df=1)
        vectors = vectorizer.fit_transform(texts).toarray()
        logger.info(f"Generated TF-IDF vectors shape: {vectors.shape}")
        return vectors
    except Exception as e:
        logger.exception(f"Vectorization failed: {e}")
        return np.array([])

def detect_outliers(vectors):
    """
    Detect outliers using Isolation Forest and Local Outlier Factor.
    Returns a 'small_voice_score' for each data point (higher = more likely to be an outlier/small voice).
    """
    n_samples = len(vectors)
    if n_samples < 3:
        # Not enough samples for outlier detection
        return np.zeros(n_samples)
    
    try:
        # Isolation Forest: -1 for outliers, 1 for inliers
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        iso_scores = iso_forest.fit_predict(vectors)
        
        # Local Outlier Factor
        lof = LocalOutlierFactor(n_neighbors=min(20, n_samples - 1), contamination=0.1)
        lof_scores = lof.fit_predict(vectors)
        
        # Combine scores: convert -1/1 to 0/1, then average
        # Outliers get higher scores
        iso_normalized = (1 - iso_scores) / 2  # -1 -> 1, 1 -> 0
        lof_normalized = (1 - lof_scores) / 2
        
        small_voice_score = (iso_normalized + lof_normalized) / 2
        
        return small_voice_score
    except Exception as e:
        logger.error(f"Outlier detection failed: {e}")
        return np.zeros(n_samples)

def analyze_clusters_logic(texts, theme_name, timestamps=None):
    """
    Enhanced clustering analysis for stable categorization and discussion-ready themes.
    """
    if not texts: return []
    
    # 1. Semantic Vectors
    logger.info("Generating semantic embeddings...")
    vectors = get_vectors_semantic(texts)
    if len(vectors) == 0: return []

    # 2. Clustering
    n_samples = len(texts)
    
    logger.info("Clustering with HDBSCAN...")
    try:
        # min_cluster_sizeを小さめに設定して、細かい差異も拾えるようにする
        min_cluster_size = 2 if n_samples < 20 else max(3, int(n_samples * 0.03))
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=1, 
            metric='euclidean', 
            cluster_selection_method='leaf', 
            allow_single_cluster=False # 強制的に分ける
        )
        cluster_ids = clusterer.fit_predict(vectors)
        
        # もしHDBSCANが全ノイズ（-1）または1クラスタしか返さない場合、KMeansで強制分割
        n_unique_clusters = len(set(cluster_ids[cluster_ids != -1]))
        if n_unique_clusters <= 1:
            logger.info("HDBSCAN produced too few clusters, falling back to KMeans for variety")
            n_clusters = min(max(3, int(n_samples / 4)), 8)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_ids = kmeans.fit_predict(vectors)
        
        logger.info(f"Clustering found {len(set(cluster_ids))} themes (including noise)")
        
    except Exception as e:
        logger.warning(f"Clustering algorithm failed: {e}")
        n_clusters = min(max(3, int(n_samples / 5)), 8) 
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_ids = kmeans.fit_predict(vectors)
    
    # 3. UMAP for 2D coords
    logger.info("Reducing dimensions with UMAP...")
    if n_samples >= 2:
        try:
            # パラメータを調整して、意味の近いものが集まりやすくする
            reducer = umap.UMAP(
                n_components=2, 
                n_neighbors=min(10, n_samples - 1), # 小さめに設定してローカルな構造を保持
                min_dist=0.05,
                metric='cosine',
                random_state=42
            )
            coords = reducer.fit_transform(vectors)
            # Subtle jitter
            coords += np.random.uniform(-0.01, 0.01, coords.shape)
        except Exception as e:
            logger.warning(f"UMAP failed, using PCA: {e}")
            pca = PCA(n_components=min(n_samples, 2))
            coords = pca.fit_transform(vectors)
            if coords.shape[1] < 2:
                coords = np.column_stack([coords, np.zeros(n_samples)])
    else:
        coords = np.zeros((n_samples, 2))

    # 4. Sentiment Analysis
    logger.info("Analyzing sentiments...")
    individual_sentiments = get_batch_sentiments(texts)

    # 5. Naming Themes
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
    
    cluster_info = {}
    unique_labels = sorted(list(set(cluster_ids)))
    
    prompt = f"""あなたは組織開発のシニア・コンサルタントです。
社員から寄せられた「{theme_name}」に関する声を分析し、対話や議論の土台となるようなカテゴリ名を付けてください。

### 指示:
1. **議論を引き出す命名**: 単なる「不満」といった言葉を避け、「[対象]の現状と今後のあり方」「[課題]を解決するための障壁」のように、問いかけや議論を想起させる名前にしてください。
2. **少数意見の尊重**: 人数が少ないグループ（IDが-1や、サンプルが1-2件のもの）は、たとえ一人であっても「独自の着眼点：〜〜」のように、その鋭さを尊重して命名してください。
3. **文字数**: **15文字以内**（多少前後しても、伝わりやすさを優先）。

### 対象データ（IDと発言サンプル）:
"""
    input_data = []
    for cid in unique_labels:
        indices = [i for i, x in enumerate(cluster_ids) if x == cid]
        samples = [texts[i] for i in indices[:min(10, len(indices))]]
        input_data.append({"id": int(cid), "samples": samples, "count": len(indices)})
    
    prompt += json.dumps(input_data, ensure_ascii=False)
    prompt += """
### 出力形式(JSON):
{
    "results": [
        { "id": ID数値, "name": "議論の土台となるカテゴリ名" }
    ]
}
"""
    try:
        resp = model.generate_content(prompt)
        clean_text = resp.text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        
        data = json.loads(clean_text)
        for res in data.get("results", []):
            cluster_info[res["id"]] = {"name": res["name"]}
    except Exception as e:
        logger.error(f"Generate thematic names failed: {e}")
        for cid in unique_labels: 
            tag = "【独自の視点】" if cid == -1 else f"テーマ {cid}"
            cluster_info[cid] = {"name": tag}

    # Construct Final Result
    results = []
    for i, text in enumerate(texts):
        cid = int(cluster_ids[i])
        info = cluster_info.get(cid, {"name": "未分類"})
        results.append({
            "original_text": text,
            "created_at": timestamps[i].isoformat() if timestamps and i < len(timestamps) and timestamps[i] else None,
            "sub_topic": info["name"],
            "sentiment": individual_sentiments[i],
            "summary": text[:60] + "..." if len(text)>60 else text,
            "x_coordinate": float(coords[i, 0]),
            "y_coordinate": float(coords[i, 1]),
            "cluster_id": cid,
            "is_noise": bool(cid == -1)
        })
        
    return results

def generate_issue_logic_from_clusters(df, theme_name):
    """
    Generate discussion agendas from clustered data.
    Ensures that at least a few points are always extracted for debate.
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use a reliable model for this task
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
        
        unique_topics = df['sub_topic'].unique()
        if len(unique_topics) == 0:
             return "[]"

        topic_summaries = []
        for topic in unique_topics:
            topic_df = df[df['sub_topic'] == topic]
            count = len(topic_df)
            all_texts = topic_df['original_text'].tolist()
            # ピックアップするサンプルを増加
            samples = "\n".join([f"  - {t}" for t in all_texts[:min(15, len(all_texts))]])
            
            marker = "【少数意見】" if count <= 2 else f"({count}件)"
            topic_summaries.append(f"### カテゴリ: {topic} {marker}\n{samples}")

        all_comments_str = "\n\n".join(topic_summaries)
        total_comments = len(df)
        
        prompt = f"""あなたは組織開発のシニア・コンサルタントとして、社員の声を元に「議論のアジェンダ（議題）」を作成します。
分析テーマ: {theme_name}
データ数: {total_comments}件

### 指示:
1. **必ず3〜5個の議論項目を抽出してください。** 「顕著な課題がない」という結論は禁止です。
2. **対立ではなく対話を促す**: 「◯◯が悪い」と決めつけるのではなく、「◯◯について、現場はこう感じているようです。今後どう向き合うべきでしょうか？」という問いかけに変換してください。
3. **少数派の救い出し**: たった一人の意見であっても、視点が鋭いもの、あるいはリスクを示唆するものは必ず1つのアジェンダとして独立させてください。
4. **全カテゴリの網羅**: 提示された複数のカテゴリを満遍なく検討材料に含めてください。

### 分析対象データ:
{all_comments_str}

### 出力フォーマット (JSON):
[
    {{
        "title": "議題タイトル（15文字以内）",
        "description": "議題の詳細。何が起きているか、なぜ話し合う必要があるか。社員の声の引用を含めても良い。",
        "urgency": "high" | "medium" | "low",
        "category": "organizational" | "technical" | "culture" | "future_opportunity"
    }}
]
"""
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        
        # JSON extraction logic
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.split("```")[0].strip()
        
        # Validate if it's a list
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return match.group(0)
            
        return text
    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
        return "[]"



def analyze_comments_logic(texts):
    """
    Summarize comments/proposals using Gemini with a focus on discussion and unique insights.
    Uses THINKING model for deeper analysis.
    """
    if not texts: return "分析対象のコメントがありません。"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME_THINKING, generation_config={"response_mime_type": "application/json"})
        
        prompt = f"""あなたは組織開発コンサルタントです。
以下の社員からの改善提案を分析し、組織をより良くするための対話のヒントを抽出してください。

### 指示:
1. **全体像の提示**: どのような傾向の提案が多いか、簡潔にまとめてください。
2. **「小さな声」の救い出し**: 少数意見や独自のアイデアであっても、組織の将来にプラスになる可能性や、見落とされがちなリスクを含んでいるものは積極的に取り上げてください。
3. **建設的な示唆**: 単なる不満の集計ではなく、「次にどのようなアクションや話し合いが必要か」という示唆を含めてください。

対象の提案リスト:
{json.dumps(texts, ensure_ascii=False)}

### 出力形式(JSON):
{{
    "overall_summary": "全体の要約（100〜150文字程度。議論の方向性を含む）",
    "key_trends": [
        {{
            "title": "トレンドのタイトル",
            "description": "内容の詳細と、なぜこれが現在注目されているかの考察",
            "count_inference": "High" | "Medium" | "Low"
        }}
    ],
    "notable_ideas": [
        {{
            "title": "独自の視点・アイデア",
            "description": "具体的でユニークな提案、または鋭いリスク指摘",
            "expected_impact": "これが対話のきっかけとなった場合の組織への好影響",
            "feasibility": "実現可能性（高/中/低）"
        }}
    ]
}}
"""
        resp = model.generate_content(prompt)
        try:
            return resp.text
        except ValueError:
             logger.warning(f"Gemini comment analysis error: {resp.prompt_feedback}")
             return json.dumps({
                "overall_summary": "AIによる分析が生成できませんでした。",
                "key_trends": [],
                "notable_ideas": []
            }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Comment analysis failed: {e}")
        return json.dumps({
            "overall_summary": "分析中にエラーが発生しました。",
            "key_trends": [],
            "notable_ideas": []
        }, ensure_ascii=False)
