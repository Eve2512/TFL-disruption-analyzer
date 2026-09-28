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
  # lowercase and collapse runs of whitespace, so small formattingd diffs in TfL's templated txt don't break a match
  return " ".join(text.lower().split())
  
def classify(reason, rules):
  """Return (cause_code, matched_phrase) for one reason string. First rule whose "match" appears in the reason wins """
  # this is why is why causes.json is ordered specific-to-general
  text = normalise(reason)
  for rule in rules:
    if normalise(rule["match"]) in text:
      return rule["cause"], rule["match"]
  return UNCLASSIFIED, None

def main():
  doc = json.loads(CAUSES_FILE.read_text())
  
  conn = sqlite3.connect(DB_PATH)
  conn.execute("PRAGMA foreign_keys = ON")
  
  with conn:
    conn.executemany(
      "INSERT INTO cause_dim VALUES (?, ?)"
      "ON CONFLICT (cause_code) DO UPDATE SET description = excluded.description",
      doc["causes"].items(),
    )
    
    reasons = [row[0] for row in conn.execute(
      "SELECT DISTINCT reason FROM line_status_observation WHERE reason IS NOT NULL"
    )]
    
    classified_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [(reason, *classify(reason, doc["rules"]), classified_at) for reason in reasons]
    
    with conn:
      conn.executemany(
      "INSERT INTO reason_cause VALUES (?, ?, ?, ?) "
      "ON CONFLICT (reason_text) DO UPDATE SET "
      "    cause_code     = excluded.cause_code, "
      "    matched_phrase = excluded.matched_phrase, "
      "    classified_at  = excluded.classified_at "
      "WHERE cause_code IS NOT excluded.cause_code "
      "   OR matched_phrase IS NOT excluded.matched_phrase",
      rows,
    )

  unmatched = conn.execute(
    "SELECT COUNT(*) FROM reason_cause WHERE cause_code = ?", (UNCLASSIFIED,)
  ).fetchone()[0]
  conn.close()

  print(f"{len(reasons)} distinct reasons, {unmatched} unclassified "
        f"({100 * unmatched / len(reasons):.1f}%)")

if __name__ == "__main__":
  main()
