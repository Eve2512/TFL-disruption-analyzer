import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
DB_PATH = REPO_ROOT / "data" / "tfl.db"
CAUSES_FILE = SRC_DIR / "causes.json"

UNCLASSIFIED = "unclassified"

def normalise(text):
  """ todo """
  
def classify(reason, rules):
  """Return (cause_code, matched_phrase) for one reason string. First rule whose "match" appears in the reason wins """
  # this is why is why causes.json is ordered specific-to-general
  text = normalise(reason)
  for rule in rules:
    if normalise(rule["match"]) in text:
      return rule["cause"], rule["match"]
  return UNCLASSIFIED, None

#todo write main function
