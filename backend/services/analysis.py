
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
以下の社員の声（日本語）のリストを読み、各発言の感情傾向（Sentiment）を分析してください。
-1.0（強い不満、怒り、深刻な課題）から 1.0（強い満足、感謝、ポジティブな提案）の範囲の数値で評価してください。
0.0 は中立、または感情が含まれない客観的な事実のみの発言です。

出力は、入力と同じ順番の数値のみが入ったJSON配列としてください。
例: [-0.6, 0.1, 0.0, 0.8, -0.2]
余計な解説、マークダウンの装飾、JSON以外の文字は一切含めないでください。

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
    
    # Use HDBSCAN for density-based clustering (automatically determines number of clusters)
    logger.info("Clustering with HDBSCAN...")
    try:
        clusterer = hdbscan.HDBSCAN(
            # データ数の約5%を最小サイズとする（下限3、上限10）- より細かいクラスタを検出 -> Modified to be more inclusive
            min_cluster_size=max(3, min(5, int(n_samples * 0.02))),
            # クラスタの「核」となるデータの最小数（下限2、上限5）-> Reduced to minimize noise
            min_samples=2,
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
    
    # 5. NEW: Batch Sentiment Analysis for all texts
    logger.info("Analyzing sentiments for each text...")
    individual_sentiments = get_batch_sentiments(texts)

    # Use LIGHT model for quick cluster naming
    model = genai.GenerativeModel(MODEL_NAME_LIGHT, generation_config={"response_mime_type": "application/json"})
    
    cluster_info = {}
    
    unique_labels = set(cluster_ids)
    
    for cid in unique_labels:
        indices = [i for i, x in enumerate(cluster_ids) if x == cid]
        if not indices: continue

        # cid == -1 (Noise) continues to be named by LLM just like others


        sample_texts = [texts[i] for i in indices[:min(8, len(indices))]]
        
        # Enhanced Prompt with Chain of Thought + Few-Shot
        prompt = f"""あなたはデータアナリストです。以下の社員の声を分析し、内容を端的に表す日本語のカテゴリ名（グループ名）を付けてください。

### 分析対象のテーマ
{theme_name}

### 声の例
{json.dumps(sample_texts, ensure_ascii=False)}

### 指示
1. 声の内容を要約し、共通するトピックを特定してください。
2. **重要**: 「Category 1」「Group A」のような機械的な名前は**絶対に使用しないでください**。
3. **重要**: 「あえて個人的な意見ですが」「正直に言うと」などの導入句や、「〜と感じます」「〜と願っています」などの末尾表現は完全に無視してください。
4. 内容を**10文字以内の簡潔な単語（体言止め）**で表現してください。
   - 文章形式（「〜が課題です」など）は厳禁です。
   - 「〜についての意見」「〜に関する要望」「〜の課題」などの冗長な付帯語は禁止です。
   - 具体的かつ短い単語を選んでください。
   
   改善の例:
   - "JIRAのチケット管理が複雑なことへの不満" → "JIRA運用"
   - "PCのスペックが低くて困っている" → "PCスペック"
   - "会議が多すぎて作業ができない" → "会議過多"
   - "給与制度を見直してほしい" → "給与制度"
   
   良い例（単語形式・10文字以内）: 
   - "PC性能", "給与制度", "リモートワーク", "会議過多", "福利厚生", "残業時間", "評価制度", "通勤環境", "情報共有"
   
5. このトピックから読み取れる、組織としての全体的な解決意向や緊急度について考慮してください（名前には含めない）。

### 出力フォーマット(JSON):
{{
    "name": "カテゴリ名(10文字以内)"
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

            name = data.get("name", "").strip()
            
            # Post-processing: If LLM still returns generic name or too long name, clean up
            if not name or name.lower().startswith("category") or name.lower().startswith("group") or "カテゴリー" in name or len(name) > 20:
                if sample_texts:
                    # Try to generate a very short summary as fallback
                    name = "トピック分析中" 
                else:
                    name = "その他"

            cluster_info[cid] = {
                "name": name
            }
        except Exception as e:
            logger.error(f"Generate cluster info failed: {e}")
            # Fallback for errors
            fallback_name = sample_texts[0][:15] + "..." if sample_texts else "未分類"
            cluster_info[cid] = {"name": fallback_name}
    
    # Construct Result without Small Voice Score
    results = []
    for i, text in enumerate(texts):
        cid = cluster_ids[i]
        info = cluster_info.get(cid, {"name": "Uncategorized"})
        results.append({
            "original_text": text,
            "created_at": timestamps[i].isoformat() if timestamps and i < len(timestamps) and timestamps[i] else None,
            "sub_topic": info["name"],
            "sentiment": individual_sentiments[i], # Use individual sentiment
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
        
        # Aggregate ALL comments by sub_topic
        unique_topics = df['sub_topic'].unique()
        if len(unique_topics) == 0:
             return "[]"

        topic_summaries = []
        for topic in unique_topics:
            topic_df = df[df['sub_topic'] == topic]
            count = len(topic_df)
            
            # Use all comments for each topic to ensure no info is lost
            all_texts = topic_df['original_text'].tolist()
            texts_str = "\n".join([f"    - {t}" for t in all_texts])
            
            # Mark if this is likely a "Small Voice" (outliers often fall into a specific cluster or 'is_noise' is true)
            # In analyze_clusters_logic, noise is bool(cid == -1).
            # We can check if any items in this topic are noise.
            is_noise_cluster = topic_df['is_noise'].any() if 'is_noise' in topic_df.columns else False
            cluster_type = " (少数意見・特異点)" if is_noise_cluster else ""
            
            topic_summaries.append(f"### トピック: 【{topic}】 ({count}件){cluster_type}\n{texts_str}")

        all_comments_str = "\n\n".join(topic_summaries)
        
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

        # Calculate appropriate number of issues based on data volume
        total_comments = len(df)
        num_topics = len(unique_topics)
        
        # Determine target number of issues (3-8 based on data volume)
        if total_comments < 10:
            target_issues = "2〜3個"
        elif total_comments < 30:
            target_issues = "3〜5個"
        elif total_comments < 100:
            target_issues = "5〜7個"
        else:
            target_issues = "6〜8個"
        
        # Enhanced Prompt with Chain of Thought
        prompt = f"""あなたは組織開発とデータ分析の専門家である「シニア・コンサルタント」です。
以下のデータを段階的に分析し、組織の重要課題を抽出してください。

### 分析ステップ

#### ステップ1: データの理解
トピック分布、実際の発言内容、およびトレンドを総合的に把握する。
- 総コメント数: {total_comments}件
- 検出されたトピック数: {num_topics}個

#### ステップ2: 深刻度の評価
各トピックについて実際の発言内容を確認し、以下の観点で評価する：
- 技術的リスク（システム障害の予兆、業務効率の低下）
- 組織的リスク（離職、モチベーション低下、コミュニケーション不全）
- 機会（改善提案、イノベーションの種、ポジティブな変化の兆し）

#### ステップ3: 優先順位付け
件数だけでなく、発言の具体性や深刻度を考慮し、以下を総合的に判断する：
- 影響度（どれだけの人や業務に影響するか）
- 緊急性（すぐに対処すべきか）
- 実現可能性（改善の余地があるか）

#### ステップ4: 課題の抽出
**必ず{target_issues}の課題を抽出してください。**
データが少ない場合でも、観察された傾向や潜在的な課題を含めてください。

---

分析テーマ: {theme_name}

【全データ：トピック別コメント一覧】
{all_comments_str}

{trend_info}

---

### 出力フォーマット(JSON):
[
    {{
        "title": "課題のタイトル（簡潔に、15文字以内）",
        "description": "課題の内容（背景、現状、予想される影響を含む。提示された全てのコメントを考慮し、網羅的かつ具体的に記述すること）",
        "urgency": "high" | "medium" | "low",
        "category": "technical" | "organizational" | "opportunity"
    }}
]

### 重要な分析ポイント:
1. **全データの網羅**: 提示された全てのコメントに目を通し、それらを統合した課題を抽出してください。
2. **少数意見（Small Voice）の重視**: 件数が少なくても（1件でも）、深刻な内容や組織のリスクを示唆するものは必ず課題として抽出、または他の課題に深刻な背景として含めてください。
3. **必ず指定された数の課題を抽出すること**: データが少ない場合でも、観察された傾向から考えられる潜在的リスクを「兆候」として記述してください。
4. 具体的なエピソードや単語を反映させ、説得力のある説明にしてください。

### 出力例:
- 多数派の意見: 「〜が多数寄せられており、生産性に大きな支障が出ている」
- 少数派の重要意見: 「少数ながら〜という深刻な指摘があり、潜在的なリスクが懸念される」
"""
        resp = model.generate_content(prompt)
        
        try:
            text = resp.text
        except ValueError:
            logger.warning(f"Gemini report generation error (likely blocked): {resp.prompt_feedback}")
            return "[]"

        # Robust JSON Extraction
        import re
        json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        else:
            # Fallback to markdown blocks if regex fails
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].strip()
            
        # Verify JSON
        try:
            json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"Generated JSON is invalid: {text}")
            # If still invalid, try to wrap it if it's almost there
            return "[]" 
            
        return text
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
