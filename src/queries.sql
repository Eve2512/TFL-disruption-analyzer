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

-- 3. WHAT TO WRITE A RULE FOR NEXT

-- 4. CAUSE FREQUENCY, TWO WAYS

-- 5. WHICH CAUSES DEGRADE SERVICE

-- 6. WHICH LINES

-- 7. WHAT TIME OF DAY

-- 8. WHERE TO INTERVENE FIRST

