# FloodLens NYC

**Investigating where public urban-flood monitoring leaves gaps in the evidence.**

Flooding is a street-level problem, but the evidence used to understand it is uneven. FloodLens is a Queens-focused civic-data prototype that explores a simple question:

> **Where are we missing the evidence needed to understand urban flooding?**

The app maps listed NYC FloodNet sensor locations, estimates how far sampled points are from the nearest listed sensor, and lets users explore that coverage alongside available historical sensor events. It also includes an optional walking-route comparison to help investigate locations in context.

FloodLens is a research and learning tool—not a flood forecast, navigation authority, or emergency service.

## Explore the app

- **Monitoring coverage:** inspect the listed Queens sensor inventory and sampled points grouped by distance to the nearest sensor.
- **Coverage gaps:** see the most distant sample points and compare the distribution across three exploratory distance bands.
- **Historical context:** review event records returned by the public data source.
- **Route investigation:** compare public walking-route alternatives and nearby historical sensor context.

## How the coverage analysis works

1. Retrieve the publicly listed FloodNet sensor locations for Queens.
2. Generate a regular sample grid within the minimum-to-maximum latitude and longitude of the returned sensor coordinates.
3. Calculate the straight-line, great-circle distance from each sample point to its nearest listed sensor.
4. Group the sample points into distance bands: **within 1 km**, **1–2 km**, and **over 2 km**.
5. Display the results on a map and identify the farthest sampled points for further investigation.

These steps measure **proximity to listed sensors**, not flood danger. The bands are exploratory thresholds, not validated standards for adequate monitoring.

## Read the map carefully

| Map result | What you can conclude | What you cannot conclude |
|---|---|---|
| Listed sensor marker | A sensor appears in the public inventory | That it is online now or represents every nearby street |
| Sample point within 1 km | A listed sensor is relatively close in straight-line distance | That the area is adequately monitored or safe |
| Sample point over 2 km away | No listed sensor is within 2 km in straight-line distance | That the area is at higher flood risk |
| Percentage of sample points in a band | The share of generated grid points in that distance band | The share of Queens land area or population affected |
| Historical sensor event | A past measurement is present in the returned records | Current street conditions or a complete record of past flooding |

### Important limitations

- The grid uses the **coordinate envelope of the returned sensor inventory**, not an official Queens boundary. It can include water and non-residential areas.
- Straight-line distance does not account for drainage, elevation, flood pathways, barriers, sensor performance, or where people live.
- The historical-event request is limited to the **100 latest returned rows**, so it is not a complete archive.
- A missing event near a location does not mean flooding has never occurred there.
- The app does not currently calculate a flood-risk score or incorporate FEMA hazard layers.
- Public geocoding and routing services can be unavailable or rate-limited, and their service policies may apply to submitted queries.

## Data and attribution

FloodLens uses public data and open mapping services:

- [NYC Open Data — FloodNet street-flooding events](https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q)
- [NYC Open Data](https://data.cityofnewyork.us/) — public data portal and sensor metadata
- [FloodNet NYC](https://www.floodnet.nyc/)
- [OpenStreetMap](https://www.openstreetmap.org/copyright) — map and pedestrian-network data
- [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) — place-name geocoding
- [FOSS GIS routing service](https://routing.openstreetmap.de/about.html) — route geometry and estimated travel time

More detail: [DATA_SOURCES.md](DATA_SOURCES.md) · [DEPLOYMENT.md](DEPLOYMENT.md) · [SECURITY_REVIEW.md](SECURITY_REVIEW.md)

## Run locally

Python 3.12 is recommended. Internet access is needed to retrieve public datasets and routing/geocoding responses.

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.\.venv\Scripts\python.exe -m compileall -q .
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

## Deploy with Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Create an app from repository `Alkhaleel404/Projects`.
3. Select branch `main` and entrypoint `app.py`.
4. Choose Python 3.12 if prompted, then deploy.
5. Open the published app and complete the smoke checks below.

The GitHub repository and a hosted app are separate things: deployment is not confirmed until hosting finishes and the public URL is tested. The current version does not require app secrets.

## Release checklist

- [ ] The app opens without a traceback.
- [ ] Sensor inventory loads, or the app shows a clear unavailable state.
- [ ] Sensor markers and coverage sample points render on the map.
- [ ] Distance bands and farthest-point results are plausible.
- [ ] Historical events load, or a clear empty/unavailable state appears.
- [ ] Route comparison works when public routing services are available.
- [ ] Limitations and privacy notices are visible on desktop and mobile.
- [ ] GitHub Actions passes for the commit being deployed.

Automated tests do not confirm third-party uptime, correct rendering in every browser, accessibility compliance, or suitability for emergency use.

## Privacy and security

The current prototype does not require an account, app database, device geolocation, saved trip history, or user-submitted public reports. Place names entered for route investigation may be sent to external geocoding and routing providers; consult their policies before entering sensitive information. See [SECURITY_REVIEW.md](SECURITY_REVIEW.md).

## Next research direction

A stronger follow-up study would compare the sensor-proximity analysis with a documented Queens land boundary and relevant flood-hazard or vulnerability datasets, then test whether findings hold under different grid spacing and distance thresholds. Any conclusions should be validated against the limitations of each source before being treated as evidence of monitoring need.
