"""RAG configuration."""
from pathlib import Path

# Base directory (where .rag/ lives)
BASE_DIR = Path(__file__).parent.parent

# Repositories to index
REPOS = {
    "scenarios": {
        "path": BASE_DIR / "scenarios",
        "extensions": [".py"],
    },
    "specter-diy": {
        "path": BASE_DIR / "specter-diy-src",
        "extensions": [".py"],
    },
}

# Embedding model
MODEL = "sentence-transformers/all-mpnet-base-v2"

# ChromaDB storage
DB_PATH = Path(__file__).parent / "chroma_db"

# Search defaults
DEFAULT_TOP_K = 5
