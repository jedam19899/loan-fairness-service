import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ─── Model & Feature Configuration ───
MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
FEATURE_ORDER = [
    "age",
    "score",
    "income",
    # … other feature keys in training order …
]

# ─── Raw SQL Query Constants ───
SQL_COUNT_APPLICATIONS_BY_GROUP = (
    "SELECT COUNT(*) FROM applications "
    "WHERE json_extract(features, '$.group') = :grp"
)
SQL_COUNT_APPROVED_BY_GROUP = (
    "SELECT COUNT(*) FROM applications "
    "WHERE json_extract(features, '$.group') = :grp AND decision='approved'"
)
SQL_SELECT_FEATURES_BY_ID = (
    "SELECT features FROM applications "
    "WHERE application_id = :id"
)

# ─── System Prompt Configuration ───
PROMPT_PATH = Path(__file__).parent / "prompts" / "fairness_agent.txt"
try:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are FairnessAgent. Use function-calling with defined FUNCTIONS."
