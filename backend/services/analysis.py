
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

def analyze_clusters_logic(texts, theme_name, timestamps=None):
    """
    Enhanced clustering analysis with:
    1. Semantic Vectors (Sentence Transformers)
    2. KMeans Clustering
    3. UMAP for 2D coords
    4. Enhanced LLM-based cluster naming with CoT + Few-Shot
    """
    if not texts: return []
    
    # 1. Semantic Vectors (NEW: Sentence Transformers)
    logger.info("Generating semantic embeddings...")
    vectors = get_vectors_semantic(texts)
    if len(vectors) == 0: return []

    # 2. Clustering
    n_samples = len(texts)
    
    # Use HDBSCAN for density-based clustering (automatically determines number of clusters)
    logger.info("Clustering with HDBSCAN...")
    try:
        clusterer = hdbscan.HDBSCAN(
            # データ数の約5%を最小サイズとする（下限3、上限10）- より細かいクラスタを検出
            min_cluster_size=max(3, min(10, int(n_samples * 0.05))),
            # クラスタの「核」となるデータの最小数（下限2、上限5）
            min_samples=max(2, min(5, int(n_samples * 0.03))),
            metric='euclidean', 
            cluster_selection_method='eom' # Excess of Mass
        )
        cluster_ids = clusterer.fit_predict(vectors)
        
        # HDBSCAN labels noise as -1. We can treat them as a separate cluster or "Outliers"
        n_clusters = len(set(cluster_ids)) - (1 if -1 in cluster_ids else 0)
        logger.info(f"HDBSCAN found {n_clusters} clusters")
        
    except Exception as e:
        logger.warning(f"HDBSCAN failed, falling back to KMeans: {e}")
        # クラスタ数を少し減らし、大きく分類するように変更 (データ数 / 7, 最大8)
        n_clusters = min(max(3, int(n_samples / 7)), 8)
        if n_samples < n_clusters: n_clusters = max(1, n_samples)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_ids = kmeans.fit_predict(vectors)
    
    # 3. UMAP for 2D coords (NEW: UMAP instead of PCA)
    logger.info("Reducing dimensions with UMAP...")
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
            
            # Add jitter for visual separation
            noise = np.random.uniform(-0.05, 0.05, coords.shape)
            coords += noise
        except Exception as e:
            logger.warning(f"UMAP failed, falling back to PCA: {e}")
            # Fallback to PCA
            pca = PCA(n_components=min(n_samples, 2))
            coords = pca.fit_transform(vectors)
            if coords.shape[1] < 2:
                coords = np.column_stack([coords, np.zeros(n_samples)])
            noise = np.random.uniform(-0.08, 0.08, coords.shape)
            coords += noise
    else:
        coords = np.zeros((n_samples, 2))

    # 4. Naming Clusters with Enhanced Prompts (NEW: CoT + Few-Shot)
    genai.configure(api_key=GEMINI_API_KEY)
    # Use LIGHT model for quick cluster naming
    model = genai.GenerativeModel(MODEL_NAME_LIGHT, generation_config={"response_mime_type": "application/json"})
    
    cluster_info = {}
    
    unique_labels = set(cluster_ids)
    
    for cid in unique_labels:
        indices = [i for i, x in enumerate(cluster_ids) if x == cid]
        if not indices: continue

        if cid == -1:
            cluster_info[cid] = {"name": "Small Voice (特異点)", "sentiment": 0.0}
            continue

        sample_texts = [texts[i] for i in indices[:min(8, len(indices))]]
        
        # Enhanced Prompt with Chain of Thought + Few-Shot
        prompt = f"""あなたはデータアナリストです。以下の社員の声を分析し、内容を端的に表す日本語のカテゴリ名を付けてください。

### 分析対象のテーマ
{theme_name}

### 声の例
{json.dumps(sample_texts, ensure_ascii=False)}

### 指示
1. 声の内容を要約し、共通するトピックを特定してください。
2. **重要**: 「Category 1」「Group A」のような機械的な名前は**絶対に使用しないでください**。
3. 内容を**6文字以内の体言止め（名詞）**で要約してください。一言で表現することを強く推奨します。
   - 「〜についての意見」「〜に関する要望」などの冗長な表現は禁止です。
   - 可能な限り短い単語を選んでください。
   悪い例: "PCスペックが低いことへの不満", "給与制度を見直してほしい", "リモートワークの課題"
   良い例: "PC性能", "給与制度", "会議過多", "リモート", "福利厚生", "勤怠管理"
4. 全体の感情傾向を -1.0(ネガティブ) 〜 1.0(ポジティブ) で数値化してください。

### 出力フォーマット(JSON):
{{
    "name": "カテゴリ名",
    "sentiment": 0.0
}}
"""
        try:
            resp = model.generate_content(prompt)
            
            # Helper to safely get text
            try:
                text_content = resp.text
            except ValueError:
                logger.warning(f"Gemini response error (likely blocked): {resp.prompt_feedback}")
                text_content = "{}"

            data = json.loads(text_content)
            
            # Handle potential list output
            if isinstance(data, list):
                if len(data) > 0:
                    data = data[0]
                else:
                    data = {}

            name = data.get("name", "")
            
            # Post-processing: If LLM still returns generic name, force fallback or clean up
            if not name or name.lower().startswith("category") or name.lower().startswith("group") or "カテゴリー" in name:
                # Fallback to a summary of the first item if name is bad
                if sample_texts:
                    # Summarize first item simply by taking first 15 chars
                    name = sample_texts[0][:15] + "..."
                else:
                    name = "その他のトピック"

            cluster_info[cid] = {
                "name": name,
                "sentiment": float(data.get("sentiment", 0.0))
            }
        except Exception as e:
            logger.error(f"Generate cluster info failed: {e}")
            # Fallback for errors
            fallback_name = sample_texts[0][:15] + "..." if sample_texts else "未分類"
            cluster_info[cid] = {"name": fallback_name, "sentiment": 0.0}
    
    # Construct Result without Small Voice Score
    results = []
    for i, text in enumerate(texts):
        cid = cluster_ids[i]
        info = cluster_info.get(cid, {"name": "Uncategorized", "sentiment": 0.0})
        results.append({
            "original_text": text,
            "created_at": timestamps[i].isoformat() if timestamps and i < len(timestamps) and timestamps[i] else None,
            "sub_topic": info["name"],
            "sentiment": info["sentiment"],
            "summary": text[:50] + "..." if len(text)>50 else text,
            "x_coordinate": float(coords[i, 0]),
            "y_coordinate": float(coords[i, 1]),
            "cluster_id": int(cid),
            "is_noise": bool(cid == -1) # Flag for HDBSCAN noise
        })
        
    return results

def generate_issue_logic_from_clusters(df, theme_name):
    """
    Generate issues from clustered data with enhanced LLM analysis.
    Uses THINKING model for deeper reasoning.
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use THINKING model for complex analysis
        model = genai.GenerativeModel(MODEL_NAME_THINKING, generation_config={"response_mime_type": "application/json"})
        
        # Aggregate counts by sub_topic
        topic_counts = df['sub_topic'].value_counts().to_dict()
        counts_str = ", ".join([f"{k}: {v}件" for k, v in topic_counts.items()])
        
        # Trend info
        trend_info = ""
        if 'created_at' in df.columns and not df['created_at'].isnull().all():
            try:
                df['dt'] = pd.to_datetime(df['created_at'])
                df = df.sort_values('dt')
                
                recent_cutoff = df['dt'].max() - pd.Timedelta(days=30)
                recent_df = df[df['dt'] >= recent_cutoff]
                
                recent_topics = recent_df['sub_topic'].value_counts().head(3).to_dict()
                recent_str = ", ".join([f"{k}: {v}件" for k, v in recent_topics.items()])
                
                trend_info = f"""
【トレンド情報】
直近30日間で特に多かったトピック: {recent_str}
（これらが急増している場合は、緊急性の高い課題として扱ってください）
"""
            except Exception as e:
                logger.warning(f"Trend analysis failed: {e}")

        # Enhanced Prompt with Chain of Thought
        prompt = f"""あなたは組織開発とデータ分析の専門家である「シニア・コンサルタント」です。
以下のデータを段階的に分析し、組織の重要課題を抽出してください。

### 分析ステップ

#### ステップ1: データの理解
トピック分布とトレンドを総合的に把握する。

#### ステップ2: 深刻度の評価
- 技術的リスク（システム障害の予兆）
- 組織的リスク（離職、モチベーション低下）
- 機会（改善提案、イノベーションの種）

#### ステップ3: 優先順位付け
件数だけでなく、影響度、緊急性、実現可能性を考慮。

#### ステップ4: 課題の抽出
3〜5個の重要課題を選定。

---

分析テーマ: {theme_name}

【クラスタリング結果】
{counts_str}

{trend_info}

---

### 出力フォーマット(JSON):
[
    {{
        "title": "課題のタイトル（簡潔に）",
        "description": "課題の内容（背景、現状、予想される影響を含む）",
        "urgency": "high" | "medium" | "low",
        "category": "technical" | "organizational" | "opportunity"
    }}
]

重要な分析ポイント:
1. 技術的問題は組織全体への影響が大きいため優先度を上げること
2. 「〜してほしい」という要望は「現場のニーズ未充足」として課題化すること
"""
        resp = model.generate_content(prompt)
        
        try:
            text = resp.text
        except ValueError:
            logger.warning(f"Gemini report generation error: {resp.prompt_feedback}")
            return "[]"
        # Ensure pure JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
            
        return text
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return "[]"



def analyze_comments_logic(texts):
    """
    Summarize comments/proposals using Gemini with enhanced prompts.
    Uses THINKING model for deeper analysis.
    """
    if not texts: return "分析対象のコメントがありません。"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use THINKING model for comment analysis
        model = genai.GenerativeModel(MODEL_NAME_THINKING, generation_config={"response_mime_type": "application/json"})
        
        # Enhanced Prompt with CoT
        prompt = f"""あなたは組織開発コンサルタントです。
以下の社員からの改善提案を段階的に分析してください。

### 分析ステップ

#### ステップ1: 全体傾向の把握
提案の主なテーマやカテゴリを特定

#### ステップ2: 重要トレンドの抽出
複数の提案に共通する課題やニーズを発見

#### ステップ3: ユニークアイデアの発掘
少数だが価値のある独創的な提案を特定

#### ステップ4: インサイトの統合
組織改善のための具体的な示唆をまとめる

---

提案リスト:
{json.dumps(texts, ensure_ascii=False)}

---

### 出力フォーマット(JSON):
{{
    "overall_summary": "全体の要約（100文字程度）",
    "key_trends": [
        {{
            "title": "トレンドのタイトル",
            "description": "内容の詳細と具体的な提案の傾向",
            "count_inference": "High" | "Medium" | "Low"
        }}
    ],
    "notable_ideas": [
        {{
            "title": "アイデアのタイトル",
            "description": "具体的でユニークな提案内容",
            "expected_impact": "実施した場合の組織へのポジティブな効果",
            "feasibility": "実現可能性（高/中/低）"
        }}
    ]
}}

重要: Notable Ideasには、件数は少なくても質的に優れた提案を含めること
"""
        resp = model.generate_content(prompt)
        try:
            return resp.text
        except ValueError:
             logger.warning(f"Gemini comment analysis error: {resp.prompt_feedback}")
             return json.dumps({
                "overall_summary": "AIによる分析が生成できませんでした（コンテンツフィルタ等の理由）",
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
