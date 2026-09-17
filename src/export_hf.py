import sqlite3
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "tfl.db"
OUT_DIR = REPO_ROOT / "hf_export"

LINE_STATUS_SQL = """
SELECT
    r.observed_at,
    o.line_id,
    o.line_name,
    o.status_index,
    o.severity_level,
    s.description AS severity_description,
    o.reason,
    o.valid_from,
    o.valid_to,
    o.is_now,
    o.disruption_hash,
    o.affected_route_count,
    r.source_file
FROM line_status_observation AS o
JOIN collection_run AS r USING (run_id)
JOIN severity_dim  AS s USING (severity_level)
ORDER BY r.observed_at, o.line_id, o.status_index
"""

CROWDING_SQL = """
SELECT
    r.observed_at,
    c.naptan_id,
    d.station_name,
    c.data_available,
    c.pct_of_baseline,
    c.reading_time_utc,
    c.fetch_error,
    r.source_file
FROM station_crowding_observation AS c
JOIN collection_run AS r USING (run_id)
JOIN station_dim   AS d USING (naptan_id)
ORDER BY r.observed_at, c.naptan_id
"""


def main():
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    for name, sql in [("line_status", LINE_STATUS_SQL), ("station_crowding", CROWDING_SQL)]:
        df = pd.read_sql_query(sql, conn)
        df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)
        df = df.convert_dtypes()
        out = OUT_DIR / f"{name}.parquet"
        df.to_parquet(out, index=False)
        print(f"{name}: {len(df)} rows, {df['observed_at'].min()} to {df['observed_at'].max()} -> {out.name}")


if __name__ == "__main__":
    main()

