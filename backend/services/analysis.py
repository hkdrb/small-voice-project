
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
以下の社員の声（日本語）のリストを読み、各発言の「感情の絶対温度」と「組織への影響度」を考慮して感情スコアを付けてください。

### 評価基準:
- **-1.0 〜 -0.7**: 強い怒り、絶望、不正の告発、離職の兆候、メンタル不調の訴えなど、極めて深刻な不満。
- **-0.6 〜 -0.4**: 業務への支障、無駄なプロセスへの苛立ち、環境への明確な不満。
- **-0.3 〜 -0.1**: 軽い疑問、違和感、改善の余地があると感じている状態。
- **0.0**: 完全に中立、または単なる事実。**安易に0.0を付けず、文脈から感情を読み取ってください。**
- **0.1 〜 0.3**: 肯定的な受け止め、改善への意欲。
- **0.4 〜 0.7**: 感謝、やりがい、前向きな提案、充実感。
- **0.8 〜 1.0**: 極めて高いモチベーション、会社への強い愛着、卓越した成果への喜び。

### 出力フォーマット:
入力と同じ順番の数値のみが入ったJSON配列としてください。
例: [-0.85, 0.4, -0.1, 0.0, 0.9]
余計な解説やマークダウン、JSON以外の文字は一切含めないでください。

対象リスト:
{json.dumps(batch, ensure_ascii=False)}
"""
        try:
            resp = model.generate_content(prompt)
            text = resp.text.strip()
            # Code block removal
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.split("```")[0].strip()
            
            # Remove any trailing commas or potential non-numeric junk
            import re
            text = re.sub(r'[^0-9\.\-\,\[\]\ ]', '', text)
            
            scores = json.loads(text)
            if isinstance(scores, list):
                for idx, score in enumerate(scores):
                    if i + idx < len(all_scores):
                        all_scores[i + idx] = float(score)
        except Exception as e:
            logger.error(f"Batch sentiment analysis failed (batch {i}): {e}")
            # エラー時は0.0のまま
            
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
    
    # Use HDBSCAN with stable settings for "Thematic Grouping"
    logger.info("Clustering with HDBSCAN...")
    try:
        clusterer = hdbscan.HDBSCAN(
            # 議論の土台として適切な粒度（少なくともデータ数の3〜5%は集まるように）
            min_cluster_size=max(3, int(n_samples * 0.04)),
            min_samples=2,
            metric='euclidean', 
            cluster_selection_method='eom', # Use 'eom' for more stable, broad clusters
            allow_single_cluster=True
        )
        cluster_ids = clusterer.fit_predict(vectors)
        
        # Noise points (-1) are grouped as "Special Insights" rather than individual IDs
        # This keeps the map clean but identifies them as unique
        n_clusters = len(set(cluster_ids)) - (1 if -1 in cluster_ids else 0)
        logger.info(f"HDBSCAN found {n_clusters} main themes")
        
    except Exception as e:
        logger.warning(f"HDBSCAN failed, falling back to KMeans: {e}")
        n_clusters = min(max(3, int(n_samples / 10)), 8) 
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_ids = kmeans.fit_predict(vectors)
    
    # 3. UMAP for 2D coords
    logger.info("Reducing dimensions with UMAP...")
    if n_samples >= 2:
        try:
            reducer = umap.UMAP(
                n_components=2, 
                n_neighbors=min(20, n_samples - 1),
                min_dist=0.15,
                metric='cosine',
                random_state=42
            )
            coords = reducer.fit_transform(vectors)
            # Subtle jitter
            coords += np.random.uniform(-0.03, 0.03, coords.shape)
        except Exception as e:
            logger.warning(f"UMAP failed, using PCA: {e}")
            pca = PCA(n_components=min(n_samples, 2))
            coords = pca.fit_transform(vectors)
            if coords.shape[1] < 2:
                coords = np.column_stack([coords, np.zeros(n_samples)])
    else:
        coords = np.zeros((n_samples, 2))

    # 4. Naming Themes with "Discussion" in mind
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 5. Batch Sentiment Analysis
    logger.info("Analyzing sentiments...")
    individual_sentiments = get_batch_sentiments(texts)

    model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
    
    cluster_info = {}
    unique_labels = sorted(list(set(cluster_ids)))
    
    # Thematic Analysis Prompt
    prompt = f"""あなたは組織開発のシニア・コンサルタントです。
社員から寄せられた「{theme_name}」に関する声を分析し、経営会議やチームビルディングで**議論の土台（アジェンダ）となるようなテーマ名**を付けてください。

### 指示:
1. **抽象度と具体性のバランス**: 単なる「PC不満」ではなく「開発環境の投資対効果」、単なる「会議」ではなく「意思決定の透明性と速度」のように、背景にある課題の本質を突いてください。
2. **文字数**: **15文字以内**を目安に（「〜の課題」「〜への懸念」など、文脈がわかる言葉も含めてOK）。
3. **ノイズ(-1)の扱い**: クラスタIDが -1 のものは、他のグループに属さない「独自の視点やリスク」です。これらを統合して『独自の指摘・潜在的リスク』といった興味を引く名前を付けてください。
4. **アウトプット**: 各IDの内容を統合し、議論を活性化させる言葉を選んでください。

### 対象データ（IDと発言サンプル）:
"""
    # Build data for prompt
    input_data = []
    for cid in unique_labels:
        indices = [i for i, x in enumerate(cluster_ids) if x == cid]
        samples = [texts[i] for i in indices[:min(8, len(indices))]]
        input_data.append({"id": int(cid), "samples": samples})
    
    prompt += json.dumps(input_data, ensure_ascii=False)
    
    prompt += """
### 出力フォーマット(JSON):
{
    "results": [
        { "id": ID数値, "name": "アジェンダとなるテーマ名" }
    ]
}
"""
    try:
        resp = model.generate_content(prompt)
        # Handle cases where Thinking models might add text before JSON
        clean_text = resp.text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        
        data = json.loads(clean_text)
        for res in data.get("results", []):
            cluster_info[res["id"]] = {"name": res["name"]}
    except Exception as e:
        logger.error(f"Generate thematic names failed: {e}")
        for cid in unique_labels: cluster_info[cid] = {"name": f"テーマ {cid}" if cid != -1 else "独自の指摘"}

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
            "summary": text[:50] + "..." if len(text)>50 else text,
            "x_coordinate": float(coords[i, 0]),
            "y_coordinate": float(coords[i, 1]),
            "cluster_id": cid,
            "is_noise": bool(cid == -1)
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
        
        # Aggregate ALL comments by sub_topic
        unique_topics = df['sub_topic'].unique()
        if len(unique_topics) == 0:
             return "[]"

        topic_summaries = []
        for topic in unique_topics:
            topic_df = df[df['sub_topic'] == topic]
            count = len(topic_df)
            
            # Use all comments for each topic
            all_texts = topic_df['original_text'].tolist()
            texts_str = "\n".join([f"    - {t}" for t in all_texts])
            
            # Identify if this is a "Small Voice" (cluster with only 1 person or flagged as noise)
            is_noise_point = (count == 1)
            cluster_type = " 【重要：特異点/少数意見】" if is_noise_point else f" ({count}件)"
            
            topic_summaries.append(f"### トピック: {topic}{cluster_type}\n{texts_str}")

        all_comments_str = "\n\n".join(topic_summaries)
        
        # Determine target number of issues
        total_comments = len(df)
        target_issues = "4〜6個" if total_comments > 50 else "3〜5個"
        
        # Enhanced Prompt with specialized analysis for Small Voices
        prompt = f"""あなたは組織開発のシニア・コンサルタントです。
提供された社員の声から、組織が直視すべき「重要課題」と「隠れた兆候（Small Voices）」を抽出してください。

### 分析の三原則
1. **多数派の課題**: 多くの社員が共通して感じている構造的な課題を特定する。
2. **鋭い少数意見(Small Voices)**: 1件しかなくても、組織の腐敗、コンプライアンスリスク、メンタルヘルス、あるいは革新的な提案を示唆するものは絶対に見逃さない。
3. **因果関係の洞察**: 表面的な現象（例：会議が多い）の裏にある本質的な原因（例：意思決定プロセスの不在）を推察する。

### 分析対象データ
分析テーマ: {theme_name}
データ数: {total_comments}件
トピック別内訳:
{all_comments_str}

### 出力指示
- **必ず{target_issues}の課題を抽出してください。**
- そのうち、少なくとも1つは「少数意見（特異点）」に基づいた、潜在的リスクや新しい機会に関する課題にしてください。
- 具体的で、アクションに繋がりやすいタイトル（15文字以内）にしてください。

### 出力フォーマット(JSON):
[
    {{
        "title": "課題タイトル",
        "description": "分析結果。なぜこれが重要なのか、どのようなリスク/機会があるのかを具体的に。少数意見を引用する場合はその旨を明記。",
        "urgency": "high" | "medium" | "low",
        "category": "technical" | "organizational" | "opportunity"
    }}
]
"""
        resp = model.generate_content(prompt)
        
        import re
        text = resp.text
        # Cleanup JSON formatting
        json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        return text.strip()
    except Exception as e:
        logger.exception(f"Report generation failed: {e}")
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
