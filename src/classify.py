import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
DB_PATH = REPO_ROOT / "data" / "tfl.db"
CAUSES_FILE = SRC_DIR / "causes.json"

UNCLASSIFIED = "unclassified"


#todo define the functions

#todo write main function
