# TfL Disruption Analyzer
Classifies Tube disruption notices into typed causes: signal failure, staffing, planned works, incident, and tracks which ones actually degrade service on which lines, at what times.

### TLDR
This is a practice exercise to see which kinds of Tube disruption actually degrade service, on which lines, at what times and where would one intervene first

### Why this exists
Because TFL only reports current state of tube lines, and there is no public archive of line status or disruption history. So this project builds its own: a collector runs on a schedule, fetches live status and station crowding, archives the raw JSON, and appends typed rows to SQLite.

Which means that the dataset accrues in calendar days, so a day the collector doesn't run is a day of time series that can't be recovered 

### Limitation: TfL has all of this set up internally, so this is like reinventing the wheel 3000 years later.
More specifically they have NUMBAT, comprised of actual fault logs, and they have gateline counts, so this project isn't discovering something TfL doesn't know. I'm just doing my best to reconstruct it from outside, from public data only, with no access to the source systems, and learning as I go on!

Also for the real limitations they are recorded honestly as they're found > see docs/feasibility-probe.md

### Data
The parsed dataset is published on Hugging Face at <https://huggingface.co/datasets/Eve39570/London-Tube-Status-Archive>, as Parquet, under an open licence. Anyone can use it without running the collector.

### Running it yourself
Install with pip install -r requirements.txt then run python src/archive_raw.py to fetch, and python src/parse.py to build the database and python src/classify.py to label the disruption notices. Queries in src/queries.sql run against data/tfl.db with sqlite3 


### The files
src/archive_raw.py fetches 2 things on every poll, the status of all tube line and the crowding level at a fixed set of stations, then writes every response to data/raw/ as raw jSON with the fetch timestamp and the HTTP outcome recorded alongside it. Parsing is in a separate file bc if TFL later adds a field I ignored for example, the raw files will persist and I can still reprise the entire history.

src/parse.py reads the raw files and appends rows to data/tfl.db, applying src/schema.sql first so the database can be rebuilt from scratch by deleting it and rerunning. Every statement in the schema is IF NOT EXISTS, so reapplying it is safe.

src/classify.py reads every distinct reason string out of the database, matches it against an ordered keyword list, and writes the result to reason_cause. It classifies distinct sentences rather than observations because the same notice is stored on every poll while a disruption lasts; at the time of writing that's 3,535 observations carrying 391 distinct sentences, so the table version does a ninth of the work. More to the point, when I add a keyword the classification is rewritten in one place and every observation picks it up through a join, instead of an UPDATE sweeping thousands of rows that could fail halfway and leave half the data on an old taxonomy.

src/causes.json holds the keyword to cause rules, ordered from the most specific to general, the first match wins. Sentences with no rule matches get an explicit unclassified code.

src/queries.sql holds the analysis: cause frequency, which causes correlate with the worst severity levels, and how disruption distributes across the day.

.github/workflows/collect.yml runs the collector, its an hourly cron but each run polls 16 times with 870 seconds of sleep in between, so a run lasts about three and a half hours and overruns its own schedule. The concurrency group then serialises the runs, so they chain back to back and polling is effectively continuous at roughly 15 minute intervals. That detour exists because GitHub throttles high frequency crons hard: a */15 cron was honoured about 5 times a day, while asking for fewer starts and doing more inside each one gets the sampling rate I wanted.
