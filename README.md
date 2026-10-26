# FloodLens NYC

**A Queens-focused civic research app that maps gaps in public urban flood-monitoring evidence.**

FloodLens asks: *Where are we missing the evidence needed to understand urban flooding?* It uses the published NYC FloodNet sensor inventory to measure proximity between a sampled geographic grid and the nearest listed sensor. It then places those coverage gaps alongside historical sensor-event context and optional walking-route analysis.

> **Important:** FloodLens is an exploratory civic-data project, not a flood prediction, emergency, or safety service. A location far from a sensor is not necessarily at higher flood risk. A location near a sensor is not necessarily safe. Sensor distance is only a proxy for direct monitoring coverage.

## What makes it different

- **Coverage-gap analysis:** fetches the Queens FloodNet sensor inventory, including listed sensors that may not appear in the app's limited event query.
- **Transparent spatial method:** samples a regular grid inside the sensor inventory's coordinate envelope and calculates great-circle distance to the nearest listed sensor.
- **Inspectable results:** classifies sample points as within 1 km, 1–2 km, or over 2 km from a listed sensor and exposes the most distant sample locations.
- **Historical evidence:** shows available FloodNet historical event summaries without describing them as live street conditions.
- **Optional route investigation:** compares public walking-route alternatives and nearby historical sensor context.
- **Privacy-conscious design:** no account, device geolocation, saved trip history, app database, or public report submission.

## How to interpret the coverage map

| Display | What it means | What it does not mean |
|---|---|---|
| Sensor marker | A sensor location listed in the public FloodNet inventory | Proof that the sensor is currently online or representative of surrounding streets |
| Grid point within 1 km | The sample is within 1 km of a listed sensor | The area is adequately monitored |
| Grid point over 2 km away | The sample is more than 2 km from every listed sensor | The area has greater flood risk or has flooded before |
| Sample-point percentage | Share of the generated grid points in a distance band | Borough-wide land-area percentage; the sampling envelope can include water and non-residential land |
| Historical event | A past sensor measurement in the returned records | Current water depth or current street conditions |
| No nearby event | No returned event met the selected distance filter | No past flooding or no present risk |

The 1 km and 2 km bands are exploratory display thresholds, not validated standards for monitoring adequacy. The grid covers the rectangular coordinate envelope of the returned sensor inventory, not the full Queens administrative boundary. The current event request is limited to the 100 latest returned rows and is not a complete historical archive.

## Data sources

- [NYC Open Data: FloodNet historical street-flooding events](https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q)
- [NYC Open Data: FloodNet sensor metadata](https://data.cityofnewyork.us/)
- [FloodNet project](https://www.floodnet.nyc/)
- [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) — map and pedestrian-network data.
- [OpenStreetMap Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) — place-name geocoding.
- [FOSS GIS public routing service](https://routing.openstreetmap.de/about.html) — route geometry and estimated travel time.

See [DATA_SOURCES.md](DATA_SOURCES.md), [DEPLOYMENT.md](DEPLOYMENT.md), and [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for more detail.

## Run locally

Python 3.12 is recommended.

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

The app needs internet access to retrieve public data and routing responses.

## Deploy to Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Create an app from repository `Alkhaleel404/Projects`, branch `main`, main file `app.py`.
3. Select Python 3.12 if prompted; no secrets are required for the current version.
4. Deploy and wait for the build to finish.
5. Open the published URL and run the smoke tests below.

A GitHub merge does not publish the app automatically. The repository owner must complete hosting setup and verify the resulting public URL.

## Release smoke test

- [ ] App loads without a traceback.
- [ ] The coverage panel retrieves sensor inventory or shows a clear unavailable state.
- [ ] Coverage points and sensor markers appear; tooltips show distance bands.
- [ ] The most distant sample table contains valid coordinates and distances.
- [ ] Route investigation returns a path for two known Queens locations when public services are available.
- [ ] Historical events load or a clear empty/unavailable state appears.
- [ ] The uncertainty and privacy notices are visible on desktop and mobile.
- [ ] GitHub Actions passes on the deployed commit.

Automated tests do not verify third-party uptime, a live deployment, map rendering in every browser, accessibility, or suitability for emergency use.

## Current limitations and next research questions

- The sensor-coordinate envelope is not a Queens boundary and may include water or non-residential areas.
- Straight-line distance does not account for barriers, drainage basins, topography, flood pathways, sensor performance, or neighborhood population.
- The distance thresholds are exploratory, not scientifically validated monitoring standards.
- Historical event retrieval is bounded to the 100 latest returned rows and does not represent the complete event archive.
- FloodNet coverage is sparse; sensor distance is not a flood-risk score.
- FEMA hazard mapping is not currently part of the coverage-gap calculation.
- Public geocoding/routing providers may log queries; services may rate-limit or fail.
- No formal accessibility review, load test, or professional security audit has been performed.

**Next research step:** compare the sensor-coverage grid with a clearly documented land/administrative boundary and relevant flood-hazard or vulnerability datasets, then validate whether the coverage gaps remain meaningful under alternative grid spacing and distance thresholds.
