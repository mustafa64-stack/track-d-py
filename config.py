import os
from dotenv import load_dotenv

load_dotenv()

# Database credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Google AI Studio API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Flash model for fast multimodal inference
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.5-flash")
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 1000

# Similarity search tuning
DEFAULT_MATCH_COUNT = 6
DEFAULT_SIMILARITY_THRESHOLD = 0.40
REFUSAL_SIMILARITY_THRESHOLD = 0.42

# Asset directories for UI viewers
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
PAGES_DIR = os.path.join(ASSETS_DIR, "pages")
SLIDES_DIR = os.path.join(ASSETS_DIR, "slides")
DIAGRAMS_DIR = os.path.join(ASSETS_DIR, "diagrams")

for folder in (PAGES_DIR, SLIDES_DIR, DIAGRAMS_DIR):
    os.makedirs(folder, exist_ok=True)
