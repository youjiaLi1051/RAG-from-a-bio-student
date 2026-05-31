"""共享配置：路径常量 + API 设置"""

from pathlib import Path

# ── 路径 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

EMBED_MODEL_PATH = MODELS_DIR / "bge-m3"
RERANKER_MODEL_PATH = MODELS_DIR / "bge-reranker-v2-m3"

COLLECTION_NAME = "biograph"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
ALLOWED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}

# ── MiMo LLM ─────────────────────────────────────────
MIMO_API_BASE = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2.5"
