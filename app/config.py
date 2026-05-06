import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

load_dotenv(BASE_DIR / ".env")


def _parse_supported_languages() -> Dict[str, str]:
    return {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
        "ta": "Tamil",
    }


SUPPORTED_LANGUAGES = _parse_supported_languages()
DEFAULT_LANGUAGE_CODE = "en"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "AI Multilingual Banking Support Bot").strip()
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:8501").strip()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2").strip()
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "4"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "8"))
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "banking_knowledge")

PDF_GLOB_PATTERNS: List[str] = ["*.pdf"]

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is required in .env or environment variables.")
