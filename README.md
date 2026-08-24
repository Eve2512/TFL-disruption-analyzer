# Toxic-TFL
TfL disruption and ridership analyser which classifies disruption notices into typed causes (signal failure, staffing, planned works, incident, etc..)

## TLDR
This is an exercise to see which kinds of Tube disruption actually degrade service, on which lines, at what times and where would one intervene first?

## Why this exists
Because TFL only reports current state of tube lines, and there is no public archive of line status or disruption history. So this project builds its own: a collector runs on a schedule, fetches live status and station crowding, archives the raw JSON, and appends typed rows to SQLite.

Which means that the dataset accrues in calendar days, so a day the collector doesn't run is a day of time series that can't be recovered (nvm just set up gh actions!).

## Limitation: TfL has all of this set up internally, so this is like reinventing the wheel 3000 years later.
More specifically they have NUMBAT, comprised of actual fault logs, and they have gateline counts, so this project isn't discovering something TfL doesn't know. I'm just doing my best to reconstruct it from outside, from public data only, with no access to the source systems, and learning as I go on!

Also for the real limitations they are recorded honestly as they're found > see docs/feasibility-probe.md
