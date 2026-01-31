
import json
import logging
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import google.generativeai as genai
from backend.utils import MODEL_NAME, MODEL_NAME_THINKING, MODEL_NAME_LIGHT, GEMINI_API_KEY, logger
import pandas as pd
from sentence_transformers import SentenceTransformer
import umap

import hdbscan

# Global model cache for performance
_semantic_model = None

def get_semantic_model():
    """Get or load Sentence Transformer model (cached)."""
    global _semantic_model
    if _semantic_model is None:
        logger.info("Loading Sentence Transformer model...")
        # Use multilingual model optimized for semantic similarity
        # 'intfloat/multilingual-e5-large' is SOTA for multilingual embeddings
        _semantic_model = SentenceTransformer('intfloat/multilingual-e5-large')
        logger.info("Model loaded successfully.")
    return _semantic_model

def get_vectors_semantic(texts):
    """Generate semantic embeddings using Sentence Transformers."""
    try:
        model = get_semantic_model()
        # e5-large requires "query: " prefix for asymmetric tasks, but for clustering we can use "passage: " or just raw text depending on usage.
        # For clustering similar items, raw text or "passage: " is often used.
        # However, e5 models are trained with "query: " / "passage: " prefixes.
        # We will use "passage: " as these are the items being analyzed.
        formatted_texts = [f"passage: {t}" for t in texts]
        vectors = model.encode(formatted_texts, show_progress_bar=False, normalize_embeddings=True)
        return vectors
    except Exception as e:
        logger.error(f"Semantic vectorization failed: {e}")
        # Fallback to TF-IDF if Sentence Transformers fails
        return get_vectors_tfidf(texts)

def get_vectors_tfidf(texts):
    """Generate TF-IDF vectors (Character N-grams for Japanese) - Fallback method."""
    try:
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), min_df=1)
        vectors = vectorizer.fit_transform(texts).toarray()
        return vectors
    except Exception as e:
        logger.error(f"Vectorization failed: {e}")
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
    4. Outlier detection (Isolation Forest + LOF)
    5. Enhanced LLM-based cluster naming with CoT + Few-Shot
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
            min_cluster_size=min(5, max(2, int(n_samples * 0.05))), # Minimum size to be a cluster
            min_samples=min(3, max(1, int(n_samples * 0.03))),      # Measure of how conservative the clustering is
            metric='euclidean', 
            cluster_selection_method='eom' # Excess of Mass
        )
        cluster_ids = clusterer.fit_predict(vectors)
        
        # HDBSCAN labels noise as -1. We can treat them as a separate cluster or "Outliers"
        n_clusters = len(set(cluster_ids)) - (1 if -1 in cluster_ids else 0)
        logger.info(f"HDBSCAN found {n_clusters} clusters")
        
    except Exception as e:
        logger.warning(f"HDBSCAN failed, falling back to KMeans: {e}")
        n_clusters = min(max(3, int(n_samples / 5)), 8)
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

    # 4. Outlier Detection (NEW: Small Voice Score)
    logger.info("Detecting outliers (Small Voice)...")
    small_voice_scores = detect_outliers(vectors)

    # 5. Naming Clusters with Enhanced Prompts (NEW: CoT + Few-Shot)
    genai.configure(api_key=GEMINI_API_KEY)
    # Use LIGHT model for quick cluster naming
    model = genai.GenerativeModel(MODEL_NAME_LIGHT, generation_config={"response_mime_type": "application/json"})
    
    cluster_info = {}
    
    unique_labels = set(cluster_ids)
    
    for cid in unique_labels:
        indices = [i for i, x in enumerate(cluster_ids) if x == cid]
        if not indices: continue

        if cid == -1:
            cluster_info[cid] = {"name": "特異点・外れ値", "sentiment": 0.0}
            continue

        sample_texts = [texts[i] for i in indices[:min(5, len(indices))]]
        
        # Enhanced Prompt with Chain of Thought + Few-Shot
        prompt = f"""あなたはデータアナリストです。以下の社員の声を段階的に分析してください。

### ステップ1: 表層的な意味の理解
各コメントが何について述べているか、明示的な内容を把握してください。

### ステップ2: 隠れた感情・意図の推定
日本的な間接表現（「〜だと嬉しいです」「〜は少し…」など）に注意し、本音の感情を推測してください。

### ステップ3: カテゴリ分類
技術的問題、業務改善、人間関係、職場環境などのカテゴリに分類してください。

テーマ: {theme_name}

声の例:
{json.dumps(sample_texts, ensure_ascii=False)}

### 参考例（Few-Shot）:
入力例1: "画面の読み込みが遅いときがあります"
→ カテゴリ: "システムパフォーマンス", 感情スコア: -0.4

入力例2: "もっと柔軟な働き方ができると嬉しいです"
→ カテゴリ: "働き方改革への要望", 感情スコア: -0.3 (丁寧だが現状への不満)

入力例3: "チームの雰囲気が良くて働きやすいです"
→ カテゴリ: "職場環境の評価", 感情スコア: 0.8

### 出力フォーマット(JSON):
{{
    "name": "カテゴリ名（簡潔に）",
    "sentiment": -0.5
}}

重要: 
- 技術的キーワード（バグ、エラー、重い、遅い等）は必ず技術カテゴリに
- 日本語の丁寧な不満表現は適切にネガティブ判定すること
"""
        try:
            resp = model.generate_content(prompt)
            data = json.loads(resp.text)
            cluster_info[cid] = {
                "name": data.get("name", f"Group {cid+1}"),
                "sentiment": float(data.get("sentiment", 0.0))
            }
        except Exception as e:
            logger.error(f"Generate cluster info failed: {e}")
            cluster_info[cid] = {"name": f"Group {cid+1}", "sentiment": 0.0}
    
    # Construct Result with Small Voice Score
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
            "small_voice_score": float(small_voice_scores[i]),  # Outlier score
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
        
        # Small Voice detection: identify high-score outliers
        small_voice_info = ""
        if 'small_voice_score' in df.columns:
            high_score_threshold = 0.7
            small_voices = df[df['small_voice_score'] >= high_score_threshold]
            if len(small_voices) > 0:
                small_voice_examples = small_voices['original_text'].head(3).tolist()
                small_voice_info = f"""
【Small Voice検出】
統計的に外れ値として検出された「少数だが重要な可能性のある意見」:
{json.dumps(small_voice_examples, ensure_ascii=False)}
→ これらは件数が少なくても、組織にとって重要なリスクや機会の可能性があります。
"""
        
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
トピック分布、トレンド、外れ値情報を総合的に把握する

#### ステップ2: 深刻度の評価
- 技術的リスク（システム障害の予兆）
- 組織的リスク（離職、モチベーション低下）
- 機会（改善提案、イノベーションの種）

#### ステップ3: 優先順位付け
件数だけでなく、影響度、緊急性、実現可能性を考慮

#### ステップ4: 課題の抽出
3〜5個の重要課題を選定

---

分析テーマ: {theme_name}

【クラスタリング結果】
{counts_str}

{trend_info}

{small_voice_info}

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
1. Small Voice（外れ値）は件数が少なくても重視すること
2. 技術的問題は組織全体への影響が大きいため優先度を上げること
3. 「〜してほしい」という要望は「現場のニーズ未充足」として課題化すること
"""
        resp = model.generate_content(prompt)
        return resp.text
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
        return resp.text
    except Exception as e:
        logger.error(f"Comment analysis failed: {e}")
        return json.dumps({
            "overall_summary": "分析中にエラーが発生しました。",
            "key_trends": [],
            "notable_ideas": []
        }, ensure_ascii=False)
