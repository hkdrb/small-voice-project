
import json
import logging
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
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

from sentence_transformers import SentenceTransformer

# Global model cache
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading local embedding model: paraphrase-multilingual-MiniLM-L12-v2")
        # 多言語対応の軽量モデル
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model

def get_vectors_semantic(texts):
    """Generate semantic embeddings using local SentenceTransformer."""
    try:
        model = get_embedding_model()
        # encode returns numpy array by default
        vectors = model.encode(texts, batch_size=32, show_progress_bar=False)
        return vectors
    except Exception as e:
        logger.exception(f"Semantic vectorization with SentenceTransformer failed: {e}")
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
    
    # Parallel execution for K search
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Define single K run
    def run_k(k):
        try:
            # Re-instantiate KMeans for thread safety (though fit is usually safe, better to be sure)
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(vectors)
            score = silhouette_score(vectors, labels)
            return k, score
        except Exception:
            return k, -1

    with ThreadPoolExecutor(max_workers=min(limit-2, 8)) as executor:
        future_to_k = {executor.submit(run_k, k): k for k in range(2, limit)}
        for future in as_completed(future_to_k):
            k, score = future.result()
            if score > -1:
                logger.debug(f"K={k}, Silhouette Score={score:.4f}")
                if score > best_score:
                    best_score = score
                    best_k = k
            
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
        # Dynamic max_k: sqrt(N) is a common heuristic. Allow more clusters for larger datasets.
        max_k_dynamic = max(12, int(np.sqrt(n_inliers)))
        # Cap at 20 to prevent too many clusters (latency trade-off)
        max_k_dynamic = min(max_k_dynamic, 20)
        
        best_k = get_optimal_k(vectors[inlier_indices], max_k=max_k_dynamic)
        logger.info(f"Optimal K determined: {best_k} (Max K: {max_k_dynamic})")
        
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

    # 5. PCA for 2D coords (Visualization) - Faster than UMAP
    logger.info("Reducing dimensions with PCA for visualization...")
    if n_samples >= 2:
        try:
            pca = PCA(n_components=2)
            coords = pca.fit_transform(vectors)
            # Add slight jitter to avoid perfect overlap
            coords += np.random.uniform(-0.01, 0.01, coords.shape)
        except Exception as e:
            logger.warning(f"PCA failed: {e}")
            coords = np.zeros((n_samples, 2))
    else:
        coords = np.zeros((n_samples, 2))

    # 6. Naming Themes
    logger.info("Generating cluster names with Gemini (Parallel Batches)...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    # helper for one batch
    def process_naming_batch(batch_labels, batch_idx):
        logger.info(f"  > Batch {batch_idx} started: {batch_labels}")
        try:
            model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
            prompt_data = []
            for cid in batch_labels:
                indices = [i for i, x in enumerate(final_cluster_ids) if x == cid]
                if not indices: continue
                
                cluster_vectors = vectors[indices]
                centroid = np.mean(cluster_vectors, axis=0)
                distances = np.linalg.norm(cluster_vectors - centroid, axis=1)
                # Sort indices by distance (closest first)
                sorted_local_indices = np.argsort(distances)
                
                # Select top 5 closest samples (Balanced for accuracy)
                top_n = min(5, len(indices))
                selected_indices = [indices[i] for i in sorted_local_indices[:top_n]]
                samples = [texts[i] for i in selected_indices]
                prompt_data.append({"id": int(cid), "samples": samples})
            
            if not prompt_data: 
                logger.info(f"  > Batch {batch_idx} empty.")
                return {}

            prompt = f"""あなたは組織開発のシニア・コンサルタントです。
社員から寄せられた「{theme_name}」に関する声を分析し、グループごとのカテゴリ名を付けてください。

### 指示:
1. **簡潔なラベル**: ダッシュボードの表示用に、**10文字以内の「体言止め」**（名詞）で出力してください。
2. **本質の抽出**: 多くを語らず、ズバリ何についての意見かを単語で表現してください。
3. **禁止事項**: 
   - 「〜について」「〜に関する意見」という表現は禁止。
   - 文章（「〜が遅い」）ではなく、名詞句（「処理速度の遅延」）にする。

### 出力例:
- OK: 「会議の効率化」「評価制度への不満」「情報共有ミス」
- NG: 「会議時間が長いことについて」「評価制度が納得できない」「情報が共有されていない件」

### 対象データ（IDとサンプル）:
{json.dumps(prompt_data, ensure_ascii=False, indent=2)}

### 出力フォーマット (JSON):
{{
  "clusters": [
    {{ "id": 0, "name": "カテゴリ名" }},
    ...
  ]
}}
"""
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            batch_result = {}
            for item in result.get("clusters", []):
                batch_result[item["id"]] = {"name": item["name"]}
            logger.info(f"  > Batch {batch_idx} success. Got {len(batch_result)} names.")
            return batch_result
        except Exception as e:
            logger.error(f"  > Batch {batch_idx} failed: {e}")
            return {}

    cluster_info = {}
    # Unique labels excluding -1
    unique_labels = sorted(list(set(final_cluster_ids)))
    if -1 in unique_labels:
        unique_labels.remove(-1)
        cluster_info[-1] = {"name": "Small Voice (特異点)"} # Default name for outliers

    # Batch size of 5 for parallel efficiency
    BATCH_SIZE = 5
    batches = [unique_labels[i:i + BATCH_SIZE] for i in range(0, len(unique_labels), BATCH_SIZE)]
    
    # Process batches in parallel
    logger.info(f"Processing {len(unique_labels)} clusters in {len(batches)} batches...")
    
    # Use 3 workers: Best balance of speed (parallel) vs stability (CPU load)
    # With the custom 5-min timeout proxy, we don't need to rush aggressively.
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit with index for logging
        futures = [executor.submit(process_naming_batch, batch, i) for i, batch in enumerate(batches)]
        for future in as_completed(futures):
            try:
                batch_res = future.result()
                cluster_info.update(batch_res)
            except Exception as e:
                logger.error(f"Parallel naming error: {e}")

    # Fallback for missing names
    for cid in unique_labels:
        if cid not in cluster_info:
            cluster_info[cid] = {"name": f"Group {cid}"}

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
            # "small_voice_score": float(small_voice_scores[i]), # Removed per user request
            "is_noise": cid == -1
        })
        
    return results

def generate_issue_logic_from_clusters(df, theme_name):
    """
    Generate discussion agendas from clustered data.
    Dynamically adjusts prompt based on presence of Small Voice (Cluster ID -1).
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
        
        # Split DataFrame into Normal and Small Voice
        if 'cluster_id' in df.columns:
            small_voices_df = df[df['cluster_id'] == -1]
            normal_df = df[df['cluster_id'] != -1]
        else:
            small_voices_df = pd.DataFrame()
            normal_df = df

        has_small_voice = not small_voices_df.empty

        # Prepare Inputs
        prompt_content = []
        
        # 1. Main Topics
        unique_topics = normal_df['sub_topic'].unique()
        for topic in unique_topics:
            topic_df = normal_df[normal_df['sub_topic'] == topic]
            count = len(topic_df)
            texts = topic_df['original_text'].tolist()
            # Sample 30% of items, minimum 10, max 100
            sample_size = max(10, int(count * 0.3))
            sample_size = min(sample_size, 100)
            
            samples = "\\n".join([f"  - {t}" for t in texts[:min(sample_size, len(texts))]])
            prompt_content.append(f"### メインカテゴリ: {topic} ({count}件 - 抽出{min(sample_size, len(texts))}件)\\n{samples}")
            
        # 2. Small Voice
        if has_small_voice:
            sv_texts = small_voices_df['original_text'].tolist()
            sv_samples = "\\n".join([f"  - {t}" for t in sv_texts])
            prompt_content.append(f"### 【重要】Small Voice (少数だが特異な意見 - 全件)\\n{sv_samples}")
            
        all_content_str = "\\n\\n".join(prompt_content)
        total_comments = len(df)
        
        # Unify instructions to always have 4 Majority + 1 Small Voice
        if has_small_voice:
            # Case A: Normal + Small Voice
            instructions = """
1. **マジョリティの課題（4つ）**:
   - 「メインカテゴリ」データから、多くの社員が感じている組織的な課題（ボトルネック、制度疲労など）を4つ抽出してください。
   - `related_topics` には、そのデータの「カテゴリ名」を正確に入れてください。

2. **Small Voiceの課題（1つ）**:
   - **「Small Voice」データに含まれる意見を、分析や解釈を加えずに、具体的に紹介してください。**
   - **タイトルは必ず「Small Voice」としてください。**
   - `related_topics` は必ず `["Small Voice (特異点)"]` としてください。
   - `insight`（詳細説明）には、「以下のような意見がありました」という形式で、具体的な意見の内容を**列挙**してください。
   - **【禁止事項】**: 背景の推測、過度な一般化、元の発言にない解釈を加えることは禁止です。事実のみを伝えてください。
"""
        else:
            # Case B: All Majority (No Small Voice)
            instructions = """
1. **マジョリティの課題（4つ）**:
   - 「メインカテゴリ」データから、多くの社員が感じている組織的な課題（ボトルネック、制度疲労など）を4つ抽出してください。
   - `related_topics` には、そのデータの「カテゴリ名」を正確に入れてください。

2. **Small Voiceの課題（1つ）**:
   - **今回の分析では、特異な少数意見（Small Voice）は検出されませんでした。**
   - **タイトルは必ず「Small Voice」としてください。**
   - `related_topics` は必ず `["Small Voice (特異点)"]` としてください。
   - `insight`（詳細説明）には、「今回の分析では、特異な少数意見（Small Voice）は検出されませんでした。」と記述してください。
   - `source_type` は必ず `small_voice` としてください。
"""

        prompt = f"""あなたは組織開発のシニア・コンサルタントとして、社員の声を元に「議論のアジェンダ（議題）」を作成します。
分析テーマ: {theme_name}
データ数: {total_comments}件

### 指示:
以下の指示に従い、合計で**5つのアジェンダ**を作成してください。

{instructions.strip()}

3. **対話を促すタイトル（マジョリティ側）**:
   - マジョリティ側の議題タイトルは「〜の問題」ではなく「〜をどう乗り越えるか」といった、建設的な議論を誘発するものにしてください。

### 分析対象データ:
{all_content_str}

### 出力フォーマット(JSON):
{{
  "issues": [
    {{
      "title": "議題タイトル",
      "related_topics": ["カテゴリ名"], 
      "insight": "なぜこれを議論すべきか...",
      "source_type": "majority" | "small_voice"
    }},
    ...
  ]
}}
"""
        logger.info(f"Generating Issue Logic with Gemini (Has SV: {has_small_voice})...")
        try:
            response = model.generate_content(prompt)
            clean_text = response.text.strip()
             # JSON clean logic
            if "```" in clean_text:
                clean_text = clean_text.split("```")[-2] if "json" in clean_text else clean_text.split("```")[1]
                if clean_text.startswith("json"): clean_text = clean_text[4:]
            clean_text = clean_text.strip()
            
            data = json.loads(clean_text)
            return data.get("issues", [])
        except Exception as e:
            logger.error(f"Generate Issue Logic failed: {e}")
            return []
    except Exception as e:
        logger.error(f"Outer generation error: {e}")
        return []


def analyze_thread_logic(comments):
    """
    Analyze a discussion thread (parent + children) and generate a simple summary and actions.
    """
    if not comments:
        return {"summary": "議論がありません。", "key_points": [], "next_steps": []}

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})

        # Format comments for prompt
        formatted_thread = ""
        for c in comments:
            # c is a dict with content, user_name, created_at
            formatted_thread += f"[{c.get('user_name', '不明')}] {c.get('content', '')}\n"

        prompt = f"""あなたは中立的かつ理性的で、議論を建設的な解決へと導く専門家（プロのファシリテーター）です。
以下のチャットスレッド（議論の流れ）を深く分析し、参加者の意見を尊重しつつ、状況を整理して次の具体的なアクションを提案してください。

### 議論の内容:
{formatted_thread}

### 指示:
議論を停滞させず、具体的かつ実行可能な解決策や次にとるべきステップを最大3つ提示してください。
   - **title**: アクションを一言で表す見出し（20文字以内）。
   - **detail**: そのアクションの具体的な内容、担当者（もし特定できれば）、期限の目安などを説明した文章。なぜそのアクションが必要なのかという背景（論点）も簡潔に含めてください。

### 出力フォーマット(JSON):
{{
    "next_steps": [
        {{ "title": "見出し...", "detail": "詳細..." }},
        ...
    ]
}}
"""
        logger.info("Generating Thread Analysis with Gemini...")
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result

    except Exception as e:
        logger.error(f"Thread analysis logic failed: {e}")
        return {
            "next_steps": [{"title": "エラー", "detail": f"分析中にエラーが発生しました: {str(e)}"}]
        }

def analyze_casual_posts_logic(posts, org_name=""):
    """
    Analyze casual posts to identify topics that should be escalated to a formal survey.
    Returns a list of recommendations.
    """
    if not posts:
        return {"recommendations": []}

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})

        # Format posts
        formatted_posts = ""
        # Assuming posts is a list of strings or objects with 'content'
        for p in posts:
            content = p.content if hasattr(p, 'content') else str(p)
            formatted_posts += f"- {content}\n"

        prompt = f"""あなたは組織開発の専門家です。
「{org_name}」という組織の「雑談掲示板」に投稿された以下の内容を分析し、
全社的なアンケート（サーベイ）を実施して意見を問うべき重要なトピックを特定してください。
メンバーが直面している課題、潜在的な要望、組織として対応すべき兆候を拾い上げてください。

### 投稿内容:
{formatted_posts}

### 分析の視点:
1. 個人の単なる愚痴ではなく、組織全体の課題や改善につながる可能性のあるテーマを探す。
2. 潜在的な不満や、新しいアイデアの芽を見つけ出す。
3. メンバーの関心が高く、定量的に状況を把握すべき事項を選ぶ。

### 出力フォーマット (JSON):
{{
    "recommendations": [
        {{
            "title": "アンケートのタイトル案",
            "reason": "なぜいまアンケートをとるべきかの理由・背景（管理者向け）",
            "survey_description": "アンケート回答者に表示する説明文。回答を促す前向きで分かりやすい文章。",
            "suggested_questions": ["具体的な質問案1", "具体的な質問案2"]
        }},
        ...
    ]
}}
推論の結果、特筆すべきアンケート推奨事項がない場合は、空のリストを返しても構いません。
"""
        logger.info("Generating Casual Post Analysis with Gemini...")
        response = model.generate_content(prompt)
        # Parse JSON
        result_text = response.text.strip()
        if "```" in result_text:
             result_text = result_text.split("```")[-2] if "json" in result_text else result_text.split("```")[1]
             if result_text.startswith("json"): result_text = result_text[4:]
        
        result = json.loads(result_text)
        return result

    except Exception as e:
        logger.error(f"Casual post analysis failed: {e}")
        return {"recommendations": [], "error": str(e)}


            

