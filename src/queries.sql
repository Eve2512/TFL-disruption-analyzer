-- Analysis queries for data/tfl.db
-- Run one at a time by doing sqlite3 data/tfl.db or just open the db and paste the one you want

-- 1. COLLECTION HEALTH
-- Polls are not evenly spaced and some days have holes, so every count later is a count of polls, not of minutes

SELECT substr(observed_at, 1, 10) AS day,
       COUNT(*)                   AS polls,
       MIN(substr(observed_at, 12, 5)) AS first_poll,
       MAX(substr(observed_at, 12, 5)) AS last_poll
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
FROM   line_status_observation o
LEFT   JOIN reason_cause rc ON rc.reason_text = o.reason
WHERE  o.reason IS NOT NULL
AND    (rc.cause_code IS NULL OR rc.cause_code = 'unclassified')
GROUP  BY o.reason
ORDER  BY observations DESC
LIMIT  20;

-- 4. CAUSE FREQUENCY, TWO WAYS
-- observations count as poll-rows, so it weights by how long a disruption lasted.
SELECT c.cause_code,
       c.description,
       COUNT(*)                          AS observations,
       COUNT(DISTINCT o.disruption_hash) AS episodes
FROM   line_status_observation o
JOIN   reason_cause rc ON rc.reason_text = o.reason
JOIN   cause_dim c oN c.cause_code       = rc.cause_code
GROUP  BY c.cause_code, c.description
ORDER  BY observations DESC;

-- 5. WHICH CAUSES DEGRADE SERVICE
-- btw service_impact_rank is my judgement as recorded in severity_dim, and not established TFL dogma.
-- also avg_rank is duration-weighted for the same reason as above
SELECT rc.cause_code,
       COUNT(*)                             AS observations,
       ROUND(AVG(s.service_impact_rank), 2) AS avg_rank,
       MAX(s.service_impact_rank)           AS worst_rank,
       SUM(s.is_planned)                    AS planned_observations
FROM   line_status_observation o
JOIN   reason_cause rc ON rc.reason_text   = o.reason
JOIN   severity_dim s  ON s.severity_level = o.severity_level
GROUP  BY rc.cause_code
HAVING COUNT(*) >= 20
ORDER  BY avg_rank DESC;
 
-- 6. WHICH LINES
-- share of polls where the line was in any disrupted state
SELECT o.line_name,
       COUNT(DISTINCT CASE WHEN s.is_disruption = 1 THEN o.run_id END) AS disrupted_polls,,
       ROUND (100.0 * COUNT(DISTINCT CASE WHEN s.is_disruption = 1 THEN o.run_id END) / (SELECT COUNT(*) FROM collection_run WHERE endpoint = 'line_status'), 1)
           AS pct_of_polls
FROM   line_status_observation o
JOIN   severity_dim s ON s.severity_level = o.severity_level
GROUP  BY o.line_id, o.line_name,
ORDER  BY pct_of_polls DESC;

-- 7. WHAT TIME OF DAY
-- dividing disruped line-rows by the number of polls in that hour gives the avg number of lines disrupted at once.
WITH polls AS (
       SELECT strftime('%H', observed_at) AS hour_utc,
              COUNT(*)                    AS poll_count
       FROM collection_run
       WHERE endpoint = 'line_status'
       GROUP BY hour_utc
)
SELECT p.hour_utc,
       p.poll_count,
       ROUND(1.0 * COUNT(o.run_id) / p.poll_count, 2) AS avg_lines_disrupted
FROM polls p
LEFT   JOIN collection_run r
       ON  strftime('%H', r.observed_at) = p.hour_utc
       AND r.endpoint = 'line_status'
LEFT   JOIN line_status_observation o ON o.run_id = r.run_id
LEFT   JOIN severity_dim s
       ON  s.severity_level = o.severity_level
       AND s.is_disruption  = 1
       AND s.is_planned     = 0
WHERE  s.severity_level IS NOT NULL
GROUP  BY p.hour_utc, p.poll_count
ORDER  BY p.hour_utc;

-- 8. WHERE TO INTERVENE FIRST
-- the whole crux of this repo, cause is crossed with line then ranked by duration weighted
-- impact rather than by count.
SELECT o.line_name,
       rc.cause_code,
       COUNT(*)                                            AS observations,
       ROUND(AVG(s.service_impact_rank), 2)                AS avg_rank,
       ROUND(COUNT(*) * AVG(s.service_impact_rank))        AS exposure_score
FROM   line_status_observation o
JOIN   reason_cause rc ON rc.reason_text   = o.reason
JOIN   severity_dim s  ON s.severity_level = o.severity_level
WHERE  s.is_planned = 0
GROUP  BY o.line_id, o.line_name, rc.cause_code
HAVING COUNT(*) >= 10
ORDER BY exposure_score DESC
LIMIT 15;


