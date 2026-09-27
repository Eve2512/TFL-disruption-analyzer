-- Analysis queries for data/tfl.db
-- Run one at a time by doing sqlite3 data/tfl.db or just open the db and paste the one you want

-- 1. COLLECTION HEALTH
-- Polls are not evenly spaced and some days have holes, so every count later is a count of polls, not of minutes

SELECT substr(observed_at, 1, 10) AS day,
       COUNT(*)                   AS polls,
       MIN(substr(observed_at, 12, 5)),
       MAX(substr(observed_at, 12, 5)),
FROM   collection_run
WHERE  endpoint = 'line_status'
GROUP  BY day
ORDER  BY day DESC
LIMIT  14;


-- 2. CLASSIFIER COVERAGE
-- what share of disruption notices the taxonomy actually explains.

SELECT cause_code,
       COUNT(*)                                                   AS distinct_reasons,
       COUNT(100.0 * COUNT(*) / (SELECT COUNT(*) FROM reason_cause), 1) AS pct_of_reasons
FROM   reason_cause
GROUP  BY cause_code
ORDER  BY distinct_reasons DESC;

-- 3. WHAT TO WRITE A RULE FOR NEXT
-- unclassified sentences ranked by how often they are observed

SELECT o.reason,
       COUNT(*) AS observations
need to finish theis latttter

-- 4. CAUSE FREQUENCY, TWO WAYS

-- 5. WHICH CAUSES DEGRADE SERVICE

-- 6. WHICH LINES

-- 7. WHAT TIME OF DAY

-- 8. WHERE TO INTERVENE FIRST

