# What the TFL API actually returns
first probe started around 20 Aug 2026; extended 21-24 Aug.

## Status
GET /Line/Mode/tube/Status?detail=true

detail=true is required. Without it the response omits reason, disruption and validityPeriods (defeats the whole purpose of this thing).

lineStatuses is an array. The Bakerloo returned two entries on 21 Aug: severity 6 (Severe Delays) north of Queen's Park and severity 9 (Minor Delays) elsewhere, same reason text. Reading lineStatuses[0] drops the second. Grain is (run_id, line_id, status_index).

Also important distinction: statusSeverity is a code, and not a scale. 10 = Good Service, 9 = Minor Delays, 6 = Severe Delays, 4 = Planned Closure, 20 = Service Closed. Do not average it. Do not write WHERE statusSeverity < 10 — that drops 11-20. Full list: /Line/Meta/Severity. Stored as severity_dim with an explicit ordinal_rank.

Text fields have trailing whitespace. Strip on ingest.

## No Archive
/Line/{id}/Status/{from}/to/{to} ignores the dates. Tested 1-3 Aug (past) and 29-31 Aug (future); both returned current state.

Nothing archives this data, so a day not collected is gone unfortunately

## Disruption
Nested inside each lineStatus when detail=true. The standalone /Line/Mode/tube/Disruption endpoint omits the line id, so it is unused.

description is templated: <Line>: <effect> due to <cause> at <location>. closureText already encodes the effect (minorDelays, severeDelays), so only the cause needs extracting.

validityPeriods[0].fromDate is a real start time and works as a dedup key. toDate is end-of-service, not a prediction — do not compute durations from it.

## Crowding
As for crowding of the stations, /crowding/{naptan} — static day-of-week profile. Reference data. Fetch once.

/crowding/{naptan}/Live — current value only, partial station coverage.

dataAvailable: false returns percentageOfBaseline: 0. Store NULL.

## Station IDs
/StopPoint/Search fuzzy-matches. "TCR" returns Brent Cross (940GZZLUBTX), HTTP 200, total: 1, no error.

Interchanges resolve to hub ids (HUBWAT, HUBVIC, HUBBAN, HUBLST, HUBTCR, HUBBDS, HUBLBG, HUBVXH). Hubs have no crowding feed; the underlying stations do — 940GZZLUWLO and 940GZZLUVIC both return live readings.

So: ids are resolved once by hand and hardcoded. src/probe_stations.py proposes and flags; it never selects. It confirmed 2 of 10 and referred 8. Auto-selection would have hardcoded hub ids.

Remaining ids come from /Line/{id}/StopPoints, which also supplies line_station.

## Ridership
Not in the API. Project NUMBAT (crowding.data.tfl.gov.uk) publishes 15-minute band entries/exits, but as a periodic typical-day survey. It cannot show that ridership fell on a given day; it can weight disruptions by expected demand.

## Auth
No key required. Unauthenticated polling has never been throttled. TfL does not publish quotas. app_key read from env if set.
