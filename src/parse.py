import gzip
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
REPO_ROOT = SRC_DIR.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
DB_PATH = REPO_ROOT / "data" / "tfl.db"
SCHEMA_FILE = SRC_DIR / "schema.sql"
STATIONS_FILE = SRC_DIR / "stations.json"

ENDPOINTS = {"status": "line_status", "crowding": "crowding_live"}


def status_rows(run_id, lines):
    """one row per (line, status_index) - every entry in lineStatuses, never just [0]"""
    for line in lines:
        for index, status in enumerate(line["lineStatuses"]):
            periods = status["validityPeriods"]
            if len(periods) > 1:
                raise ValueError(f"{line['id']} has {len(periods)} validityPeriods - time to make it a table")
            period = periods[0] if periods else {}

            disruption = status.get("disruption")
            if disruption:
                body = json.dumps(disruption, sort_keys=True).encode()
                disruption_hash = hashlib.sha256(body).hexdigest()
                route_count = len(disruption["affectedRoutes"])
            else:
                disruption_hash = route_count = None

            yield (
                run_id,
                line["id"],
                index,
                line["name"],
                status["statusSeverity"],
                (status.get("reason") or "").strip() or None,
                period.get("fromDate"),
                period.get("toDate"),
                period.get("isNow"),
                disruption_hash,
                route_count,
            )


def crowding_rows(run_id, document):
    """one row per station, in one of the three states described in schema.sql"""
    for response in document["responses"]:
        naptan = response["naptan_id"]
        body = response["body"]
        if response["error"]:
            yield run_id, naptan, None, None, None, response["error"]
        elif body["dataAvailable"]:
            yield run_id, naptan, 1, body["percentageOfBaseline"], body["timeUtc"], None
        else:
            # TfL sends percentageOfBaseline 0 here; that zero is not a measurement
            yield run_id, naptan, 0, None, None, None


def parse_file(conn, path):
    """one raw file -> one collection_run row plus its observations, in one transaction"""
    source_file = path.relative_to(RAW_DIR).as_posix()  # '2026-09-12/1015_status.json.gz'
    day = path.parent.name
    hhmm, kind = path.name.split(".")[0].split("_")
    observed_at = f"{day}T{hhmm[:2]}:{hhmm[2:]}:00Z"
    parsed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with gzip.open(path) as f:
        document = json.load(f)

    with conn:  # commits if the block finishes, rolls back if anything raises
        run_id = conn.execute(
            "INSERT INTO collection_run (source_file, endpoint, observed_at, parsed_at) VALUES (?, ?, ?, ?)",
            (source_file, ENDPOINTS[kind], observed_at, parsed_at),
        ).lastrowid
        if kind == "status":
            conn.executemany(
                "INSERT INTO line_status_observation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                status_rows(run_id, document),
            )
        else:
            conn.executemany(
                "INSERT INTO station_crowding_observation VALUES (?, ?, ?, ?, ?, ?)",
                crowding_rows(run_id, document),
            )

