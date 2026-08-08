import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    BREETH_API_KEY: str = os.getenv("BREETH_API_KEY", "")
    
    CURRICULUM_PATH: Path = BASE_DIR / "curriculum.json"
    CANDIDATES_PATH: Path = BASE_DIR / "candidates.json"
    
    # Provider fallback logging
    LOG_PROVIDERS: bool = True

settings = Settings()
