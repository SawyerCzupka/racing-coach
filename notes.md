# Project Notes

rust sdk: [github](https://github.com/superfell/iracing-telem)
setup diff: [SetupDiffer](https://svappslab.com/iRacing/SetupDiffer)
coachdaveacademy delta:

Use TimescaleDB for storing and querying telemetry data.

[IRSDK Docs](https://sajax.github.io/irsdkdocs/)

## Database

TimescaleDB

Tables:

- Session: Session info like weather conditions, track, car, series, session type (practice, etc.)
- Telemetry:
- Tracks: Include Sector location info
- Cars?
