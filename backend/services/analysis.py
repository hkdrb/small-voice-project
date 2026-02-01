
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

from sklearn.metrics import silhouette_score

def get_optimal_k(vectors, max_k=12):
    """
    Determine optimal number of clusters using Silhouette Score.
    """
    n_samples = len(vectors)
    if n_samples < 3:
        return 1
        
    best_k = 2
    best_score = -1
    
    # Try range of k
    # Upper limit is bounded by n_samples - 1 or max_k
    limit = min(n_samples, max_k + 1)
    
    for k in range(2, limit):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(vectors)
            score = silhouette_score(vectors, labels)
            
            logger.info(f"K={k}, Silhouette Score={score:.4f}")
            
            if score > best_score:
                best_score = score
                best_k = k
        except Exception:
            continue
            
    # Heuristic: If best score is very low (< 0.1), data might not be clusterable -> use fewer clusters
    if best_score < 0.1 and n_samples > 10:
         logger.info(f"Low silhouette score ({best_score:.4f}). Fallback to conservative K.")
         return max(2, int(n_samples / 10))

    return best_k

def analyze_clusters_logic(texts, theme_name, timestamps=None):
    """
    Enhanced clustering analysis using high-dimensional embeddings for accuracy.
    Points are clustered semantically first, then projected for visualization.
    Sentiment analysis is completely removed.
    
    IMPROVEMENTS:
    - Outlier Detection (Small Voices)
    - Silhouette Analysis for Optimal K
    """
    if not texts: return []
    
    # 1. Semantic Vectors
    logger.info("Generating semantic embeddings...")
    vectors = get_vectors_semantic(texts)
    if len(vectors) == 0: return []

    n_samples = len(texts)
    
    # 2. Outlier Detection (Small Voices)
    logger.info("Detecting outliers...")
    small_voice_scores = detect_outliers(vectors)
    
    # Threshold: e.g., top 10% are outliers, or score > 0.6
    # For now, let's use a dynamic threshold based on distribution
    # If standard deviation is low, maybe no outliers.
    
    # Simple logic: Score > 0.7 is a definitive outlier (Isolation forest + LOF normalized)
    # We create a mask for Inliers vs Outliers
    outlier_mask = small_voice_scores > 0.65
    
    # Force at least some inliers if too many outliers
    if np.sum(outlier_mask) > n_samples * 0.3:
        # Too many outliers, raise threshold significantly
        outlier_mask = small_voice_scores > 0.9
        
    # Failsafe: if STILL too many outliers (or all), force top 50% to be inliers based on score
    if np.sum(outlier_mask) == n_samples or np.sum(~outlier_mask) < 2:
        logger.info("Outlier detection marked almost all points as outliers. Forcing top 50% as inliers.")
        # Sort by score ascending (lower is more inlier)
        sorted_indices = np.argsort(small_voice_scores)
        # Keep half as inliers
        n_keep = max(2, int(n_samples * 0.5))
        threshold_idx = sorted_indices[n_keep]
        threshold_val = small_voice_scores[threshold_idx]
        outlier_mask = small_voice_scores > threshold_val

    inlier_indices = np.where(~outlier_mask)[0]
    outlier_indices = np.where(outlier_mask)[0]
    
    n_inliers = len(inlier_indices)
    logger.info(f"Inliers: {n_inliers}, Outliers (Small Voices): {len(outlier_indices)}")

    # 3. Clustering (Inliers Only)
    inlier_cluster_ids = np.zeros(n_inliers, dtype=int)
    
    if n_inliers >= 3:
        logger.info("Calculating optimal K for inliers...")
        best_k = get_optimal_k(vectors[inlier_indices])
        logger.info(f"Optimal K determined: {best_k}")
        
        try:
            kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            inlier_cluster_ids = kmeans.fit_predict(vectors[inlier_indices])
        except Exception as e:
            logger.warning(f"KMeans failed: {e}")
    else:
        # Too few inliers, just one cluster
        inlier_cluster_ids = np.zeros(n_inliers, dtype=int)

    # 4. Integrate Results
    # Initialize all as -1 (Outlier)
    final_cluster_ids = np.full(n_samples, -1, dtype=int)
    
    # Map inlier results back
    for rank, idx in enumerate(inlier_indices):
        final_cluster_ids[idx] = inlier_cluster_ids[rank]

    # 5. UMAP for 2D coords (Visualization)
    logger.info("Reducing dimensions with UMAP for visualization...")
    if n_samples >= 2:
        try:
            reducer = umap.UMAP(
                n_components=2, 
                n_neighbors=min(15, n_samples - 1),
                min_dist=0.1,
                metric='cosine',
                random_state=42
            )
            coords = reducer.fit_transform(vectors)
            coords += np.random.uniform(-0.01, 0.01, coords.shape)
        except Exception as e:
            logger.warning(f"UMAP failed, using PCA: {e}")
            pca = PCA(n_components=2)
            coords = pca.fit_transform(vectors)
    else:
        coords = np.zeros((n_samples, 2))

    # 6. Naming Themes
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
    
    cluster_info = {}
    # Unique labels excluding -1
    unique_labels = sorted(list(set(final_cluster_ids)))
    if -1 in unique_labels:
        unique_labels.remove(-1)
        cluster_info[-1] = {"name": "Small Voices (特異点)"} # Default name for outliers
    
    prompt = f"""あなたは組織開発のシニア・コンサルタントです。
社員から寄せられた「{theme_name}」に関する声を分析し、グループごとのカテゴリ名を付けてください。

### 指示:
1. **正確な要約**: そのグループに属する発言の共通点を見抜き、最も適切なラベル（15文字以内）を付けてください。
2. **体言止め**: 「〜について」「〜の問題」のような曖昧な表現ではなく、「現場の疲弊」「情報共有の不足」のように核心を突く名詞形にしてください。

### 対象データ（IDとサンプル）:
"""
    input_data = []
    for cid in unique_labels:
        indices = [i for i, x in enumerate(final_cluster_ids) if x == cid]
        samples = [texts[i] for i in indices[:min(10, len(indices))]]
        input_data.append({"id": int(cid), "samples": samples})
    
    if unique_labels:
        prompt += json.dumps(input_data, ensure_ascii=False)
        prompt += """
### 出力形式(JSON):
{
    "results": [
        { "id": ID数値, "name": "カテゴリ名" }
    ]
}
"""
        try:
            resp = model.generate_content(prompt)
            clean_text = resp.text.strip()
            # JSON clean logic
            if "```" in clean_text:
                clean_text = clean_text.split("```")[-2] if "json" in clean_text else clean_text.split("```")[1]
                if clean_text.startswith("json"): clean_text = clean_text[4:]
            clean_text = clean_text.strip()
            
            data = json.loads(clean_text)
            for res in data.get("results", []):
                cluster_info[res["id"]] = {"name": res["name"]}
        except Exception as e:
            logger.error(f"Generate thematic names failed: {e}")
            for cid in unique_labels: 
                cluster_info[cid] = {"name": f"カテゴリ {cid}"}

    # Construct Final Result
    results = []
    for i, text in enumerate(texts):
        cid = int(final_cluster_ids[i])
        info = cluster_info.get(cid, {"name": "未分類"})
        results.append({
            "original_text": text,
            "created_at": timestamps[i].isoformat() if timestamps and i < len(timestamps) and timestamps[i] else None,
            "sub_topic": info["name"],
            # "sentiment": 0.0, # Removed
            "summary": text[:60] + "..." if len(text)>60 else text,
            "x_coordinate": float(coords[i, 0]),
            "y_coordinate": float(coords[i, 1]),
            "cluster_id": cid,
            "small_voice_score": float(small_voice_scores[i]), # Save score
            "is_noise": cid == -1
        })
        
    return results

def generate_issue_logic_from_clusters(df, theme_name):
    """
    Generate discussion agendas from clustered data.
    Explicitly handles 'Small Voices' (Cluster ID -1) to ensure they are represented.
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
        
        # Split DataFrame into Normal and Small Voices
        # Assuming cluster_id -1 is for outliers/small voices as defined in analyze_clusters_logic
        if 'cluster_id' in df.columns:
            small_voices_df = df[df['cluster_id'] == -1]
            normal_df = df[df['cluster_id'] != -1]
        else:
            small_voices_df = pd.DataFrame()
            normal_df = df

        # Prepare Inputs
        prompt_content = []
        
        # 1. Main Topics
        unique_topics = normal_df['sub_topic'].unique()
        for topic in unique_topics:
            topic_df = normal_df[normal_df['sub_topic'] == topic]
            count = len(topic_df)
            texts = topic_df['original_text'].tolist()
            # Sample up to 10
            samples = "\\n".join([f"  - {t}" for t in texts[:min(10, len(texts))]])
            prompt_content.append(f"### メインカテゴリ: {topic} ({count}件)\\n{samples}")
            
        # 2. Small Voices (CRITICAL)
        if not small_voices_df.empty:
            sv_texts = small_voices_df['original_text'].tolist()
            # Sample up to 20 for small voices (show more because they are diverse)
            sv_samples = "\\n".join([f"  - {t}" for t in sv_texts[:min(20, len(sv_texts))]])
            prompt_content.append(f"### 【重要】Small Voices (少数だが特異な意見)\\n{sv_samples}")
            
        all_content_str = "\\n\\n".join(prompt_content)
        total_comments = len(df)
        
        prompt = f"""あなたは組織開発のシニア・コンサルタントとして、社員の声を元に「議論のアジェンダ（議題）」を作成します。
分析テーマ: {theme_name}
データ数: {total_comments}件

### 指示:
1. **マジョリティとマイノリティの両立**:
   - 「メインカテゴリ」からは、多くの社員が感じている組織的な課題（ボトルネック、制度疲労など）を抽出してください。
   - **「Small Voices」からは、たった1件の意見であっても、ハラスメント、コンプライアンス違反、あるいは革新的なアイデアの種など、見過ごすと危険/勿体ないものを必ず1つ以上救い上げてください。**

2. **対話を促すタイトル**:
   - 議題タイトルは「〜の問題」ではなく「〜をどう乗り越えるか」「〜についてどう考えるか」といった、建設的な議論を誘発するものにしてください（15文字〜20文字程度）。

3. **出力数**: 3〜6個のアジェンダを作成してください。

### 分析対象データ:
{all_content_str}

### 出力フォーマット (JSON):
[
    {{
        "title": "議題タイトル",
        "description": "議題の詳細。なぜ今これを話し合うべきなのか、背景にある社員の声（引用）を含めて記述。",
        "urgency": "high" | "medium" | "low",
        "category": "organizational" | "risk_management" | "innovation" | "culture"
    }}
]
"""
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        
        # JSON extraction logic
        if "```" in text:
            text = text.split("```")[-2] if "json" in text else text.split("```")[1]
            if text.strip().startswith("json"):
                text = text.strip()[4:]
            text = text.strip()
        
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
        
        prompt = f"""あなたは組織変革を支援する戦略コンサルタントです。
以下の社員からの改善提案リストを読み込み、経営層やリーダーが「ハッとする」ような洞察を抽出してください。

### 指示:
1. **全体俯瞰 (Overall Summary)**: 
   - 単に「多かった意見」を並べるのではなく、その背後にある**「組織の深層心理」や「構造的な矛盾」**を言語化してください。

2. **トレンド分析 (Key Trends)**:
   - 「なぜ今、この意見が増えているのか？」という背景推察を含めて記述してください。

3. **【最重要】きらりと光るアイデア (Notable Ideas)**:
   - 多数決では埋もれてしまうが、**「実行すれば大きなインパクトを生む逆転の発想」や「誰も気づいていない本質的なリスク指摘」**を探し出してください。
   - 常識的な提案（「Macが欲しい」「給料上げて」）はここでは除外してください。

### 対象データ:
{json.dumps(texts, ensure_ascii=False)}

### 出力形式(JSON):
{{
    "overall_summary": "組織の深層心理に迫る要約（150文字程度）",
    "key_trends": [
        {{
            "title": "トレンド名",
            "description": "内容と背景の考察",
            "count_inference": "High" | "Medium" | "Low"
        }}
    ],
    "notable_ideas": [
        {{
            "title": "アイデア/指摘のタイトル",
            "description": "提案の具体的記述",
            "expected_impact": "これが組織にもたらす変革インパクト（具体的利益や回避できるリスク）",
            "feasibility": "High" | "Medium" | "Low"
        }}
    ]
}}
"""
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        
        # JSON Clean logic
        if "```" in text:
            text = text.split("```")[-2] if "json" in text else text.split("```")[1]
            if text.strip().startswith("json"):
                text = text.strip()[4:]
        text = text.strip()

        try:
            return text
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
