import os
from pathlib import Path

from dotenv import load_dotenv

# Path to project root (folder containing src/, data/, etc.)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env at the project root
load_dotenv(PROJECT_ROOT / ".env")

# OpenAI configuration
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
# Leave this empty in .env for normal OpenAI; set a URL only if using a compatible provider
OPENAI_API_BASE: str | None = os.getenv("OPENAI_API_BASE")

# Default model name; can be overridden in .env
DEFAULT_MODEL_NAME: str = os.getenv("DEFAULT_MODEL_NAME", "gpt-4.1-mini")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Add it to your .env file at the project root."
    )
