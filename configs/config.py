import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote

# Setup colored, UTF-8 safe logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "app.log"
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8")  # ✅ log fix
    ]
)
logger = logging.getLogger(__name__)

# Load environment from .env
load_dotenv()

# Read raw values
AZURE_ORG_URL = os.getenv("AZURE_ORG_URL").rstrip("/")
AZURE_PROJECT_RAW = os.getenv("AZURE_PROJECT")
AZURE_TEAM_RAW = os.getenv("AZURE_TEAM")
AZURE_PAT = os.getenv("AZURE_PAT")

# Encode for URL-safety
AZURE_PROJECT = quote(AZURE_PROJECT_RAW)
AZURE_TEAM = quote(AZURE_TEAM_RAW)

def get_auth_header():
    import base64
    if not AZURE_PAT:
        logger.warning("AZURE_PAT is missing from your .env!")
    token = f":{AZURE_PAT}"
    b64 = base64.b64encode(token.encode("utf-8")).decode()
    return {
        "Content-Type": "application/json",
        "Authorization": f"Basic {b64}"
    }
