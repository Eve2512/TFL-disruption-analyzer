-- schema.sql - Toxic-TFL.  Apply: sqlite3 data/tfl.db < src/schema.sql
-- Five tables, still need toadd some notes at the bottom.

 
PRAGMA foreign_keys = ON;
 
 
-- ONE ROW = one TfL severity level and how this project interprets it.
CREATE TABLE severity_dim (
    severity_level       INTEGER NOT NULL PRIMARY KEY,
    description          TEXT    NOT NULL,
    is_disruption        INTEGER NOT NULL CHECK (is_disruption IN (0, 1)),
    is_planned           INTEGER NOT NULL CHECK (is_planned    IN (0, 1)),
    service_impact_rank  INTEGER NOT NULL CHECK (service_impact_rank BETWEEN 0 AND 5)
);
 
-- service_impact_rank: 0 none, 1 info/access only, 2 minor, 3 moderate,
-- 4 severe or partial closure, 5 total loss of service.
INSERT INTO severity_dim VALUES
    ( 0, 'Special Service',      1, 0, 2),
    ( 1, 'Closed',               1, 0, 5),
    ( 2, 'Suspended',            1, 0, 5),   -- seen
    ( 3, 'Part Suspended',       1, 0, 4),   -- seen
    ( 4, 'Planned Closure',      1, 1, 5),   -- seen
    ( 5, 'Part Closure',         1, 1, 4),   -- seen
    ( 6, 'Severe Delays',        1, 0, 4),   -- seen
    ( 7, 'Reduced Service',      1, 0, 3),
    ( 8, 'Bus Service',          1, 0, 4),
    ( 9, 'Minor Delays',         1, 0, 2),   -- seen
    (10, 'Good Service',         0, 0, 0),   -- seen
    (11, 'Part Closed',          1, 1, 4),
    (12, 'Exit Only',            1, 0, 1),
    (13, 'No Step Free Access',  1, 0, 1),
    (14, 'Change of frequency',  1, 1, 2),
    (15, 'Diverted',             1, 0, 3),
    (16, 'Not Running',          1, 0, 5),
    (17, 'Issues Reported',      1, 0, 2),
    (18, 'No Issues',            0, 0, 0),
    (19, 'Information',          0, 0, 0),
    (20, 'Service Closed',       0, 1, 0);   -- seen
 
 
-- ONE ROW = one station this project polls for crowding.
CREATE TABLE station_dim (
    naptan_id     TEXT NOT NULL PRIMARY KEY,
    station_name  TEXT NOT NULL
);
 
 
-- ONE ROW = one archived raw file, parsed once.
CREATE TABLE collection_run (
    run_id       INTEGER PRIMARY KEY,                -- rowid alias, autoincrements
    source_file  TEXT    NOT NULL UNIQUE,            -- '2026-09-12/1015_status.json.gz'
    endpoint     TEXT    NOT NULL CHECK (endpoint IN ('line_status', 'crowding_live')),
    observed_at  TEXT    NOT NULL,                   -- ISO 8601 UTC, from the path
    parsed_at    TEXT    NOT NULL                    -- ISO 8601 UTC
);
 
CREATE INDEX idx_run_observed_at ON collection_run (observed_at);
 
 
-- ONE ROW = one status condition reported for one line in one run.
CREATE TABLE line_status_observation (
    run_id                INTEGER NOT NULL REFERENCES collection_run (run_id),
    line_id               TEXT    NOT NULL,
    status_index          INTEGER NOT NULL CHECK (status_index >= 0),
    line_name             TEXT    NOT NULL,
    severity_level        INTEGER NOT NULL REFERENCES severity_dim (severity_level),
    reason                TEXT,
    valid_from            TEXT,
    valid_to              TEXT,
    is_now                INTEGER CHECK (is_now IN (0, 1)),
    disruption_hash       TEXT,
    affected_route_count  INTEGER,
    PRIMARY KEY (run_id, line_id, status_index)
);
 
CREATE INDEX idx_status_line     ON line_status_observation (line_id);
CREATE INDEX idx_status_severity ON line_status_observation (severity_level);
CREATE INDEX idx_status_hash     ON line_status_observation (disruption_hash);
 
 
-- ONE ROW = one live crowding reading for one station in one run.
CREATE TABLE station_crowding_observation (
    run_id            INTEGER NOT NULL REFERENCES collection_run (run_id),
    naptan_id         TEXT    NOT NULL REFERENCES station_dim (naptan_id),
    data_available    INTEGER          CHECK (data_available IN (0, 1)),
    pct_of_baseline   REAL,
    reading_time_utc  TEXT,
    fetch_error       TEXT,
    PRIMARY KEY (run_id, naptan_id),
    CHECK (data_available = 1 OR pct_of_baseline IS NULL),
    CHECK ((fetch_error IS     NULL AND data_available IS NOT NULL)
        OR (fetch_error IS NOT NULL AND data_available IS     NULL))
);
 
CREATE INDEX idx_crowding_station ON station_crowding_observation (naptan_id);
