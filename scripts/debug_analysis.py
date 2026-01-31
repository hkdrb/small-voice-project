
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    print("Testing imports...")
    try:
        import hdbscan
        print(f"hdbscan imported successfully. Version: {getattr(hdbscan, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"Failed to import hdbscan: {e}")
    except Exception as e:
        print(f"Error importing hdbscan: {e}")

    try:
        import umap
        print(f"umap imported successfully. Version: {getattr(umap, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"Failed to import umap: {e}")
    except Exception as e:
        print(f"Error importing umap: {e}")
        
    try:
        import google.generativeai as genai
        print(f"google.generativeai imported successfully. Version: {getattr(genai, '__version__', 'unknown')}")
    except ImportError as e:
        print(f"Failed to import google.generativeai: {e}")

def test_analysis():
    print("\nTesting analysis logic...")
    try:
        # Add backend to path if needed (assuming running from project root)
        sys.path.append(os.getcwd())
        
        from backend.services.analysis import analyze_clusters_logic
        from backend.utils import GEMINI_API_KEY
        
        print(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}")
        
        texts = [
            "システムが遅いです",
            "画面が重い",
            "もっと早くしてほしい",
            "人間関係が悩みです",
            "上司と合わない",
            "福利厚生を良くして"
        ]
        
        print(f"Running analyze_clusters_logic with {len(texts)} texts...")
        results = analyze_clusters_logic(texts, "Test Theme")
        
        print(f"Analysis complete. Result count: {len(results)}")
        if results:
            print("First result sample:", results[0])
        else:
            print("Results are empty!")
            
    except Exception as e:
        print(f"Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imports()
    test_analysis()
