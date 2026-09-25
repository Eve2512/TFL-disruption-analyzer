---
license: other
license_name: tfl-transport-data-service-licence
license_link: https://tfl.gov.uk/corporate/terms-and-conditions/transport-data-service
pretty_name: London Tube Status Archive
tags:
- transport
- time-series
- london
size_categories:
- 1K<n<10K
configs:
- config_name: line_status
  data_files: "line_status.parquet"
  default: true
- config_name: station_crowding
  data_files: "station_crowding.parquet"
---

# London Tube Status Archive

Snapshots of London Underground line status and live station crowding, polled from
TfL's public API. TfL only serves current state and keeps no public archive of past
line status, so these observations can't be recovered for any time they weren't collected.

This data was collected in the context of a personal side project
([TFL-disruption-analyzer](https://github.com/Eve2512/TFL-disruption-analyzer)), where
the raw API responses are also archived. It is not affiliated with or endorsed by
Transport for London.

## Contents

`line_status`: one row per status condition per line per poll, from
`GET /Line/Mode/tube/Status?detail=true`. Every line appears in every successful poll,
including lines with Good Service. A line can have more than one status at once
(for example Severe Delays on one section and Minor Delays elsewhere), so rows are
keyed by `(observed_at, line_id, status_index)`.

`station_crowding`: one row per station per poll, from `GET /crowding/{naptan}/Live`.
`data_available` is 1 for a real reading, 0 when TfL has no sensor data, and empty
when the request failed (see `fetch_error`).

All timestamps are UTC. `source_file` points to the raw response in the GitHub repo.

## Collection

Polled roughly every 15 minutes by a scheduled GitHub Actions workflow. Line status
starts 21 August 2026; station crowding starts 12 September 2026.

## Limitations

- Coverage is uneven. GitHub throttled the original 15-minute schedule, so until
  13 September 2026 many polls never ran and gaps cluster at certain times of day.
  Coverage is much denser from 13 September onward. A missing timestamp means no
  observation, not an absence of disruption.
- Failed status polls are not recorded.
- `severity_level` is a category code, not a scale (10 = Good Service, 6 = Severe
  Delays, 20 = Service Closed). Averaging it is meaningless.
- `valid_to` is end of service, not a predicted end of disruption. Don't compute
  disruption durations from it.
- `disruption_hash` is a hash of TfL's full disruption object, useful for telling
  identical-looking disruptions apart. The object itself is in the raw archive.
- Live crowding covers a small, hand-picked set of stations. The set changed after
  the first few polls on 12 September (Blackhorse Road, Brixton and Pimlico were
  dropped). Interchange hub IDs have no crowding feed.

## Attribution

Powered by TfL Open Data. Contains OS data © Crown copyright and database rights 2016
and Geomni UK Map data © and database rights [2019].
