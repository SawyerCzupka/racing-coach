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

Run some time series model against the lap with the number of known corners to segment the lap?
I don't want to execute the handlers at 60hz with each frame since they can't do anything with that,
but I also don't want to run all of them at the end of the lap. I found out I can get the sector information
from irsdk so I can segment the lap into sectors, but I can't say for sure that sector boundaries don't
cut off corners. Cutting off corners would be bad since running brake analysis on it would obviously fail since
it doesn't have all the information for a corner.

