
## Two programs
- src/archive_raw.py  fetches, writes raw bytes to disk and runs in Actions. 
- src/parse.py reads the archive, writes rows, doesn't need network

written as separate programs so the parsing stays reversible and so a parser bug cannot cost a fetch

## Inputs
Every run: /Line/Mode/tube/Status?detail=true

Once, as dimensions:

/Line/Meta/Severity
/Line/Meta/DisruptionCategories
/Line/{id}/StopPoints — source of line_station
/crowding/{naptan} — static baseline

Planned for later: /crowding/{naptan}/Live for a hand-verified station list.

### Some known traps (see feasibility-probe.md) TLDR below:

- lineStatuses is an array
- statusSeverity is a code, not ordinal
- dataAvailable: false arrives as 0
- StopPoint/Search fuzzy-matches
- Interchange searches return hub ids
- Disruptions have no stable id; use fromDate
- toDate is end-of-service


## Outputs

data/raw/YYYY-MM-DD/HHMM_status.json.gz : response bytes, unmodified, gzipped. Committed. UTC, from one timestamp computed per run.

data/tfl.db : derived, gitignored, rebuildable.

## Failure modes

| Event | Result | Because |
| ------ | ----------- | ------ |
| HTTP 500 / timeout | Exit non-zero, write nothing | gap is honest whereas a null row isn't |
| 200, empty array | Nothing. Not a failure | "No disruptions" is data |
| dataAvailable: false | Store NULL | 0 is a measurement |
| Two lineStatuses | Two rows, status_index | Seen on the Bakerloo |
| Same notice repeatedly | Store every observation | Dedup is a query concern |
| Collector didn't run | No collection_run row | Absence is the downtime record |

## Out of scope for v1
- Arrivals (/Line/{id}/Arrivals). ~100 predictions per line per poll; real headways, ~40x the volume. Best upgrade after v1.
- Non-tube modes. One-line change later.
- Lifts and escalators. Different question.
- Dashboards, charts, web UI. Deliverable is a db and queries.
- LLM extraction. v2, and only if it beats a " due to " split plus a keyword lookup on a labelled set.
