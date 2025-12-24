"""
H1B Job Finder settings - completely isolated
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


# API Keys for FREE job search APIs
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")  # Get from https://developer.adzuna.com/
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Get from https://rapidapi.com/

# OpenAI configuration
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
# Leave this empty in .env for normal OpenAI; set a URL only if using a compatible provider
OPENAI_API_BASE: str | None = os.getenv("OPENAI_API_BASE")
# Default model name; can be overridden in .env
DEFAULT_MODEL_NAME: str = os.getenv("DEFAULT_MODEL_NAME", "gpt-4.1-mini")

# Paths (won't conflict with existing code)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# H1B-specific data files
JOBS_H1B_LIVE_CSV = DATA_DIR / "jobs_h1b_live.csv"
H1B_REPORT_CSV = OUTPUT_DIR / "reports" / "h1b_daily_report.csv"

# Email settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
REPORT_RECIPIENT = os.getenv("REPORT_RECIPIENT", EMAIL_USER)

# Job search settings
JOB_KEYWORDS = "Data Engineer", "Software Engineer", "Cloud Architect" 
JOB_LOCATION = "United States"
NUM_PAGES = 5

# Create output directories
(OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)
