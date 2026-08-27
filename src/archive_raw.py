# Minimal raw archiver. Throwaway scaffolding: fetches tube line status and writes the response bytes to a gzipped file 

import requests
import gzip
from datetime import datetime, timezone
from pathlib import Path

STATUS_URL = "https://api.tfl.gov.uk/Line/Mode/tube/Status?detail=true"
TIMEOUT = 10

now = datetime.now(timezone.utc)
repo_root = Path(__file__).resolve().parent.parent
day_dir = repo_root / "data" / "raw" / now.strftime("%Y-%m-%d")
day_dir.mkdir(parents=True, exist_ok=True)

response = requests.get(STATUS_URL, timeout=TIMEOUT)
response.raise_for_status()

out_path = day_dir / f"{now.strftime('%H%M')}_status.json.gz"
with gzip.open(out_path, "wb") as f:
    f.write(response.content)

print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")
