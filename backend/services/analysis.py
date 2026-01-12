
import json
import logging
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
import google.generativeai as genai
from backend.utils import MODEL_NAME, GEMINI_API_KEY, logger
import pandas as pd # Added for trend analysis

def get_vectors_tfidf(texts):
    """Generate TF-IDF vectors (Character N-grams for Japanese)."""
    try:
        # Use character n-grams (1-3 chars) to capture meaning without tokenizer
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3), min_df=1)
        vectors = vectorizer.fit_transform(texts).toarray()
        return vectors
    except Exception as e:
        logger.error(f"Vectorization failed: {e}")
        return np.array([])

def analyze_clusters_logic(texts, theme_name, timestamps=None):
    """
    1. Vectors (TF-IDF)
    2. KMeans Clustering
    3. PCA for 2D coords
    4. Naming clusters via LLM
    """
    if not texts: return []
    
    # 1. Vectors
    vectors = get_vectors_tfidf(texts)
    if len(vectors) == 0: return []

    # 2. Clustering
    # Determine K: simple heuristic, e.g., sqrt(N/2) or fixed range usually 5-10
    n_samples = len(texts)
    n_clusters = min(max(3, int(n_samples / 5)), 8) # At least 3, max 8
    
    # If samples are too few, adjust
    if n_samples < n_clusters: n_clusters = max(1, n_samples)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(vectors)
    
    # 3. PCA
    # PCA needs at least n_components + 1 samples to be meaningful, but scikit-learn handles it.
    # However, if n_samples < 2, PCA(2) will fail.
    if n_samples >= 2:
        pca = PCA(n_components=min(n_samples, 2))
        coords = pca.fit_transform(vectors) # shape (N, 2)
        # If only 1D, pad with zeros for Y
        if coords.shape[1] < 2:
            coords = np.column_stack([coords, np.zeros(n_samples)])
            
        # Add Jitter to separate identical points
        # Even with unique texts, semantic vectors might be very close. Jitter helps visibility.
        noise = np.random.uniform(-0.08, 0.08, coords.shape)
        coords += noise
    else:
        coords = np.zeros((n_samples, 2))

    # 4. Naming Clusters
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
    
    cluster_info = {}
    
    # Process each cluster to get a name
    for cid in range(n_clusters):
        # Pick indices for this cluster
        indices = [i for i, x in enumerate(cluster_ids) if x == cid]
        if not indices:
            cluster_info[cid] = {"name": "その他", "sentiment": 0.0}
            continue
            
        # Example texts
        sample_texts = [texts[i] for i in indices[:5]]
        
        if timestamps:
             # Calculate trend for this cluster
             cluster_dates = [timestamps[i] for i in indices]
             # Simple trend: compare first half vs second half counts? Or just range.
             # Let's just pass the date range to the prompt for context if needed, 
             # but for now, we'll focus on the content analysis as requested.
             pass

        prompt = f"""
        あなたは熟練したデータアナリストです。
        以下の「社員の声」のグループについて、分析を行ってください。

        ### 分析のポイント
        1. **カテゴリ名**: このグループを的確に表す「短いカテゴリ名」を付けてください。（例：給与への不満、業務フローの改善、システム不具合など）
           - **重要**: 「バグ」「重い」「エラー」「接続不可」などのキーワードが含まれる場合は、必ず「技術的課題」「システム品質」といった技術的なカテゴリに分類してください。
        
        2. **感情スコア**: このグループ全体の「感情スコア」を -1.0 〜 1.0 で判定してください。
           - -1.0: 非常にネガティブ（怒り、強い不満、危機感）
           - 0.0: 中立（事実の報告、質問）
           - 1.0: 非常にポジティブ（感謝、称賛、期待）
           - **重要**: 日本語の「〜してほしい」「〜だと良いのですが」「〜は少し使いにくい」といった **"丁寧だが不満を含んでいる表現"** は、**ネガティブ（-0.3 〜 -0.7）** として扱ってください。ポジティブに分類しないでください。

        テーマ: {theme_name}
        
        声の例:
        {json.dumps(sample_texts, ensure_ascii=False)}
        
        出力フォーマット(JSON):
        {{
            "name": "カテゴリ名",
            "sentiment": 0.0
        }}
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
    
    # Construct Result
    results = []
    for i, text in enumerate(texts):
        cid = cluster_ids[i]
        info = cluster_info.get(cid, {"name": "Uncategorized", "sentiment": 0.0})
        results.append({
            "original_text": text,
            "created_at": timestamps[i].isoformat() if timestamps and i < len(timestamps) and timestamps[i] else None,
            "sub_topic": info["name"],
            "sentiment": info["sentiment"],
            "summary": text[:50] + "..." if len(text)>50 else text, # Extended summary length
            "x_coordinate": float(coords[i, 0]),
            "y_coordinate": float(coords[i, 1]),
            "cluster_id": int(cid)
        })
        
    return results

def generate_issue_logic_from_clusters(df, theme_name):
    # Cluster based summary
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
        
        # Aggregate counts by sub_topic
        topic_counts = df['sub_topic'].value_counts().to_dict()
        counts_str = ", ".join([f"{k}: {v}件" for k, v in topic_counts.items()])
        
        # Prepare timeline info if available
        trend_info = ""
        if 'created_at' in df.columns and not df['created_at'].isnull().all():
            try:
                # Convert to datetime
                df['dt'] = pd.to_datetime(df['created_at'])
                # Sort by date
                df = df.sort_values('dt')
                
                # Simple monthly/weekly aggregation could be done here, 
                # but let's provide a summary of "Recent" vs "Past" issues to the LLM.
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

        prompt = f"""
        あなたは、組織開発とデータ分析の専門家である「シニア・コンサルタント」です。
        収集された社員の声（アンケート結果）とトレンドデータを分析し、現在組織内で発生している「解決すべき重要課題」を抽出してください。
        
        分析テーマ: {theme_name}
        
        クラスタリング分析の結果、以下のトピック分布が確認されました:
        {counts_str}
        
        {trend_info}
        
        **分析の指示:**
        1. 単に件数が多いだけでなく、内容の深刻度や（もしあれば）トレンド情報を加味して課題を選定してください。
        2. 技術的な問題（バグ、重い、エラー等）が報告されている場合は、件数が少なくても「システム品質リスク」として取り上げてください。
        3. 「〜してほしい」という要望が多い場合は、「現場のニーズ未充足」として課題化してください。
        
        以下のJSONフォーマットで、重要課題を3〜5個出力してください。
        
        出力フォーマット(JSON):
        [
            {{
                "title": "課題のタイトル（簡潔に）",
                "description": "課題の内容（背景や現状など）"
            }}
        ]
        """
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return "[]"

def analyze_comments_logic(texts):
    """
    Summarize comments/proposals using Gemini.
    """
    if not texts: return "分析対象のコメントがありません。"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME, generation_config={"response_mime_type": "application/json"})
        
        prompt = f"""
        あなたは組織開発コンサルタントです。
        以下の「社員からの改善提案リスト」を分析し、組織改善のためのインサイトを抽出してください。

        提案リスト:
        {json.dumps(texts, ensure_ascii=False)} 
        
        以下のJSONフォーマットで出力してください：

        {{
            "overall_summary": "全体としてどのような提案が多いか、100文字程度の要約",
            "key_trends": [
                {{
                    "title": "トレンドのタイトル（例：コミュニケーション改善）",
                    "description": "内容の詳細と具体的な提案の傾向",
                    "count_inference": "High"  // High, Medium, Low のいずれか（提案の多さから推測）
                }}
            ],
            "notable_ideas": [
                {{
                    "title": "アイデアのタイトル",
                    "description": "具体的でユニークな提案内容",
                    "expected_impact": "実施した場合の組織へのポジティブな効果"
                }}
            ]
        }}
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
