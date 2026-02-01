
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
以下の社員の声（日本語）のリストを読み、各発言の感情スコアを付けてください。

### 評価の指針:
1. **日本的表現の読解**: 「〜かもしれない」「個人的には〜」といった控えめな表現の裏にある、強い不満や期待を読み取ってください。
2. **組織への影響**: 単なる個人の好みではなく、業務効率、心理的安全、企業の誠実さに関わる不満は、より強くスコアリングしてください。
3. **中立バイアスの回避**: 多くの意見が「まあまあ」であっても、僅かな言葉の端々に表れる「諦め」や「喜び」を逃さず、0.0に逃げずに±0.1〜0.3の範囲で評価してください。

### スコア指標:
- **-1.0 〜 -0.7**: 強い憤り、メンタル不調の兆候、離職の意志、不正への警鐘。
- **-0.6 〜 -0.4**: 明確な不満、非効率への苛立ち、環境への失望。
- **-0.3 〜 -0.1**: 違和感、改善の余地を求めている、慎重な懸念。
- **0.0**: 事実の羅列のみ、または感情が全く読み取れない場合。
- **0.1 〜 0.3**: 前向きな提案、改善への意欲、控えめな称賛。
- **0.4 〜 0.6**: 感謝、手応え、環境への満足。
- **0.7 〜 1.0**: 高いモチベーション、組織への強い信頼、卓越した成果への喜び。

### 出力形式:
入力と同じ順番の数値のみが入ったJSON配列としてください。
例: [-0.85, 0.4, -0.15, 0.0, 0.72]
余計な解説やマークダウンは一切含めないでください。

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
            
            # Parse only if looks like a valid list
            if not text.startswith('['):
                text = '[' + text + ']'
            
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
        # 安定性を高めるため、データの量に応じて最小クラスタサイズを調整
        # 小・中規模データでも「主要な話題」が適切に固まるように
        min_cluster_size = max(2, int(n_samples * 0.05)) if n_samples > 20 else 2
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=1, # 境界の発言も極力どこかに入れる
            metric='euclidean', 
            cluster_selection_method='leaf', # より具体的な（小さな）塊を拾う
            allow_single_cluster=True,
            prediction_data=True
        )
        cluster_ids = clusterer.fit_predict(vectors)
        
        # ノイズ（-1）が多すぎる場合の救済措置：最も近いクラスタに割り当てるか、
        # あるいは「独自の視点」としてそのまま扱う
        # ※ ユーザーは「特異点としての点数付け」は不要としているが、
        # 「議論の土台として表示する」ことは希望しているため、
        # 少人数のグループも一つのカテゴリとして適切に命名する。
        
        n_clusters = len(set(cluster_ids)) - (1 if -1 in cluster_ids else 0)
        logger.info(f"HDBSCAN found {n_clusters} themes")
        
    except Exception as e:
        logger.warning(f"HDBSCAN failed, falling back to KMeans: {e}")
        n_clusters = min(max(3, int(n_samples / 5)), 10) 
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_ids = kmeans.fit_predict(vectors)
    
    # 3. UMAP for 2D coords
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
            # Subtle jitter
            coords += np.random.uniform(-0.02, 0.02, coords.shape)
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
    Generate discussion agendas from clustered data with enhanced LLM analysis.
    Uses THINKING model for deeper reasoning.
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME_THINKING, generation_config={"response_mime_type": "application/json"})
        
        unique_topics = df['sub_topic'].unique()
        if len(unique_topics) == 0:
             return "[]"

        topic_summaries = []
        for topic in unique_topics:
            topic_df = df[df['sub_topic'] == topic]
            count = len(topic_df)
            all_texts = topic_df['original_text'].tolist()
            # 議論の材料として、代表的な声をいくつかピックアップ
            texts_str = "\n".join([f"    - {t}" for t in all_texts[:min(10, len(all_texts))]])
            
            # 少数意見かどうかのフラグ
            marker = "【少数・独自意見】" if count <= 2 else f"({count}件)"
            topic_summaries.append(f"### カテゴリ: {topic} {marker}\n{texts_str}")

        all_comments_str = "\n\n".join(topic_summaries)
        total_comments = len(df)
        
        prompt = f"""あなたは組織開発のシニア・コンサルタントです。
分析テーマ「{theme_name}」について、社員から寄せられた計{total_comments}件の声を元に、
**次の議論や対話の土台（アジェンダ）となる項目**を抽出してください。

### 分析・抽出のルール:
1. **多様性の保持**: 多数派の意見に偏らず、少数であっても本質を突いた指摘、あるいは組織に新しい気づきを与える声は必ず一つの項目として取り上げてください。
2. **対話への接続**: 単に「◯◯が悪い」と定義するのではなく、「◯◯の現状をどう捉え、今後どうあるべきか」といった、建設的な議論を促す構成にしてください。
3. **客観性**: 主観的な断定を避け、社員の言葉の背後にある「願い」や「期待」にも焦点を当ててください。

### 分析対象データ:
{all_comments_str}

### 出力指示:
- **必ず3〜5個の項目を抽出してください。**
- 各項目には具体的で中立的なタイトル（15文字以内）を付けてください。
- 説明文には、なぜその項目が議論に必要なのか、どのような視点が寄せられているかを記述してください。

### 出力形式(JSON):
[
    {{
        "title": "項目タイトル",
        "description": "議論のポイント。どのような声があり、何について対話すべきか。",
        "urgency": "high" | "medium" | "low",
        "category": "organizational" | "technical" | "culture" | "future_opportunity"
    }}
]
"""
        resp = model.generate_content(prompt)
        text = resp.text
        
        import re
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
