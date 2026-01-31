
import sys
import os
import logging
import pandas as pd
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_analysis_with_csv():
    print("\nTesting analysis logic with generated CSV...")
    try:
        # Add backend to path
        sys.path.append(os.getcwd())
        
        from backend.services.analysis import analyze_clusters_logic
        
        csv_path = "outputs/test_data/project.csv"
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return

        df = pd.read_csv(csv_path)
        print(f"Loaded CSV with {len(df)} rows.")
        
        # Sample 200 rows to ensure we get clusters
        sample_df = df.head(200)
        texts = sample_df["プロセスへのコメント"].tolist() # Using one of the columns
        
        print(f"Running analyze_clusters_logic with {len(texts)} texts...")
        results = analyze_clusters_logic(texts, "Project Management Test")
        
        print(f"Analysis complete. Result count: {len(results)}")
        
        # Check cluster names
        unique_clusters = set()
        cluster_names = {}
        
        for r in results:
            cid = r['cluster_id']
            name = r['sub_topic']
            unique_clusters.add(cid)
            cluster_names[cid] = name
            
        print(f"Found {len(unique_clusters)} unique clusters.")
        print("Cluster Names:")
        for cid in sorted(unique_clusters):
            print(f"ID {cid}: {cluster_names[cid]}")
            
        # Verify no "Category X"
        failed_names = [name for name in cluster_names.values() if "Category" in name or "Group" in name]
        if failed_names:
            print(f"❌ Failed: Found generic names: {failed_names}")
        else:
            print("✅ Success: No generic names found.")

    except Exception as e:
        print(f"Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis_with_csv()
