# RainRoute NYC

**A Queens-focused civic evidence tool for exploring walking routes and nearby historical flood-sensor records.**

RainRoute asks a narrow question: *What can public flood data tell us—and what can’t it tell us—about a mapped walking route?* It combines OpenStreetMap-based pedestrian routes with NYC FloodNet’s returned historical sensor records and makes the uncertainty visible instead of inventing a safety score.

> **Not for emergency decisions.** RainRoute does not detect live street flooding, verify current sidewalk conditions, or certify a route as safe or accessible. Historical sensor records are not live flood status. A route with no nearby records may still be flooded. Follow current official alerts and local instructions.

## What it does

- **Maps real route alternatives** between two entered Queens locations, when public services return them.
- **Compares route geometry** by distance and the routing service’s estimated travel time.
- **Shows nearby FloodNet evidence** by measuring the approximate distance from sensor points to the selected route.
- **Makes limitations explicit**: the 300 m radius is a display filter, not a validated impact zone. The current data request is limited, and the display uses the latest returned historical record for each matched sensor—not a complete count of all past flood events.
- **Keeps the experience low-data**: no account, device geolocation, app database, saved trip history, or public report submission.

## How to read the results

| You see | It means | It does **not** mean |
|---|---|---|
| Route line | A public routing service returned this path from OpenStreetMap-based network data | Every sidewalk, crossing, curb ramp, or path is present, open, safe, or accessible |
| Distance and time | The routing service’s estimate for the returned route | A guarantee of actual travel time |
| Nearby FloodNet record | A historical measurement was associated with a sensor near the route | That the route is flooded now—or that nearby streets are dry |
| No nearby records | No records returned by this query met the app’s distance filter | No flood risk or no past flooding |

The app does not calculate a route safety score, predict flooding, or label routes safe/unsafe. FloodNet context can fail independently while route results remain available.

## Data sources

- [OpenStreetMap Nominatim](https://operations.osmfoundation.org/policies/nominatim/) — place-name/address geocoding.
- [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) — map and pedestrian-network data (© OpenStreetMap contributors, ODbL).
- [FOSS GIS public routing service](https://routing.openstreetmap.de/about.html) — route geometry, distance, and estimated time.
- [NYC Open Data / FloodNet historical street-flooding events](https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q) and [FloodNet project](https://www.floodnet.nyc/) — historical sensor-event summaries and deployment metadata.

See [DATA_SOURCES.md](DATA_SOURCES.md) for the source registry and [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for privacy and security limits.

## Deploy on Streamlit Community Cloud

1. Confirm the repository is pushed to your GitHub account: `Alkhaleel404/Projects`.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Choose **Create app**, repository **Alkhaleel404/Projects**, branch **main**, and main file **app.py**.
4. Choose **Python 3.12** in Advanced settings if prompted. No secrets are required for the current version.
5. Deploy and wait for the build to finish. Copy the generated `.streamlit.app` URL.
6. Run the release smoke test below before sharing the link.

**A GitHub commit does not itself publish the website.** The repository owner must complete hosting setup and confirm that the live URL works. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Local setup

Python 3.12 is recommended. From the repository root:

**Windows PowerShell**
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS / Linux**
```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m compileall -q .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m streamlit run app.py
```

Keep the terminal open and use the local URL printed by Streamlit. The app requires an internet connection to contact its public data services.

## Release smoke test

- [ ] App opens without a traceback in a fresh/private browser.
- [ ] A known Queens origin and destination return a route when public services are available.
- [ ] Route lines, origin/destination markers, and route selection work.
- [ ] Historical records load, or the app displays a clear unavailable/empty state.
- [ ] Changing the selected route updates route metrics and nearby-record context.
- [ ] Invalid and out-of-area locations produce a useful message.
- [ ] Privacy and uncertainty notices are visible.
- [ ] Layout is usable on desktop and a phone-sized screen.
- [ ] GitHub Actions validation passes on the deployed commit.

Do not describe the app as production-validated until these checks are completed. Automated unit tests do not verify live third-party services, deployment health, accessibility, or emergency-use suitability.

## Current limitations and next improvements

- Historical FloodNet coverage is sparse and the current request is bounded; it is not a complete historical archive.
- No route-specific live flood observations or alert overlay is currently integrated.
- Public geocoding and routing services can rate-limit requests or be unavailable, and providers may log submitted place text or coordinates.
- OpenStreetMap data does not guarantee sidewalk continuity, curb ramps, crossings, closures, or accessibility.
- Formal accessibility testing, load testing, and a professional security audit have not been performed.

The most valuable next technical step is to integrate clearly timestamped official alerts as a separate context panel—not to turn incomplete data into a misleading “safe route” score.
