"""MiMo Recruitment Engine configuration."""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
DATABASE_PATH = DATA_DIR / "recruitment.db"

# MiMo LLM
MIMO_API_URL = os.getenv("MIMO_API_URL", "http://43.153.206.68:20128/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "xmtp/mimo-v2.5-pro")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "sk-hermes-mimo")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
