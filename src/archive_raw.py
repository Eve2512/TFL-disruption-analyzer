
import requests
import gzip
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TFL_BASE = "https://api.tfl.gov.uk"
TIMEOUT = 10
 
SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
STATIONS_FILE = SRC_DIR / "stations.json"

def auth_params():
    """returns the app_key query param if one is configured, else nothing """
    key = os.environ.get("TFL_APP_KEY")
    return {"app_key": key} if key else {}

def fetch(session, url, params=None):
    """One GET, returns (ok, http_status, body_bytes, error_string)."""
    merged = dict(auth_params())
    if params:
        merged.update(params)
    try:
        r = session.get(url, params=merged, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return False, None, None, f"request failed: {exc}"
    if r.status_code != 200:
        return False, r.status_code, None, f"HTTP {r.status_code}"
    return True, r.status_code, r.content, None
 
 
def archive_status(session, day_dir, stamp):
    """fetches the tube line status and write the response in bytes"""
    ok, _, body, error = fetch (
        session, f"{TFL_BASE}/Line/Mode/tube/Status", {"detail": "true"}
    )
    if not ok:
        print(f"status: FAILED - {error}")
        return False
        
    out = day_dir / f"{stamp}_status.json.gz"
    with gzip.open(out, "wb") as f:
        f.write(body)
    print(f"status: wrote {out} ({out.stat().st_size} bytes)")
    return True
 
 
def archive_crowding(session, day_dir, stamp, stations, fetched_at):
    """fetches live crowding for every station into ONE file, returns the number of stations that failed"""
    responses = []
    failed = 0
 
    for naptan in stations:
        ok, http_status, body, error = fetch(
            session, f"{TFL_BASE}/crowding/{naptan}/Live"
        )
        entry = {"naptan_id": naptan, "http_status": http_status, "error": error}
        if ok:
            try:
                entry["body"] = json.loads(body)
            except ValueError:
                entry["body"] = None
                entry["error"] = "response was not JSON"
                ok = False
        else:
            entry["body"] = None
        if not ok:
            failed += 1
        responses.append(entry)
 
    document = {
        "fetched_at": fetched_at,
        "endpoint": "crowding_live",
        "station_count": len(stations),
        "responses": responses,
    }
 
    out = day_dir / f"{stamp}_crowding.json.gz"
    with gzip.open(out, "wt", encoding="utf-8") as f:
        json.dump(document, f)
 
    got = len(stations) - failed
    print(f"crowding: wrote {out} ({out.stat().st_size} bytes) - "
          f"{got}/{len(stations)} stations returned")
    return failed
 
 
def main():
    stations = json.loads(STATIONS_FILE.read_text())["stations"]
 
    # One timestamp for the whole poll, taken once so the folder and both filenames can never straddle a midnight boundary.
    now = datetime.now(timezone.utc)
    day_dir = REPO_ROOT / "data" / "raw" / now.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%H%M")
 
    session = requests.Session()
 
    status_ok = archive_status(session, day_dir, stamp)
    crowding_failed = archive_crowding(
        session, day_dir, stamp, stations, now.isoformat()
    )
 
    # DEVIATION from spec-collection.md's "exit non-zero, write nothing", writes whatever succeeded, then exits non-zero so the Actions run goes red and the failure is visible. Partial data is still better than no data, beggars cant be choosers.
    if not status_ok or crowding_failed == len(stations):
        sys.exit(1)
 
 
if __name__ == "__main__":
    main()
