# 共通ユーティリティ (Constants & Config)
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Initialize
# Load .env from project root (parent of backend)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
MODEL_NAME_THINKING = os.getenv("GEMINI_MODEL_NAME_THINKING", "gemini-1.5-pro")
MODEL_NAME_LIGHT = os.getenv("GEMINI_MODEL_NAME_LIGHT", "gemini-1.5-flash")
EMBEDDING_MODEL_NAME = os.getenv("GEMINI_EMBEDDING_MODEL_NAME", "models/text-embedding-004")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 20))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
