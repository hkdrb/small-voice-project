# 共通ユーティリティ (Constants & Config)
import os
import logging
from dotenv import load_dotenv

# Initialize
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp")
MODEL_NAME_THINKING = os.getenv("GEMINI_MODEL_NAME_THINKING", "gemini-2.0-flash-thinking-exp")
MODEL_NAME_LIGHT = os.getenv("GEMINI_MODEL_NAME_LIGHT", "gemini-2.0-flash-exp")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 20))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
