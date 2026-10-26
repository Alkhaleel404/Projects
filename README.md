# RainRoute NYC

RainRoute NYC is a Queens-focused civic technology app that compares real walking-route options with nearby historical flood-sensor observations. It is designed to show what public data can tell us—and what it cannot.

> **Important:** RainRoute is an experimental research tool, not an emergency service or safety-certified navigation app. FloodNet records are historical measurements, not live sidewalk conditions. No route is labeled safe or unsafe.

## What it does

- **Real walking routes:** Geocodes place names or addresses in Queens and requests pedestrian routes from OpenStreetMap-based public routing infrastructure.
- **Route-linked flood context:** Finds historical NYC FloodNet sensor events within 300 metres of each selected route's actual geometry.
- **Alternative comparison:** Compares route distance and routing-service time estimates alongside counts of nearby historical sensor events.
- **Transparent uncertainty:** Displays event timestamps, maximum measured depth, duration, and sensor-to-route distance. It does not turn historical measurements into a current safety score.
- **Privacy-aware design:** No account, device geolocation, database, location history, or public report submission. Place text is sent to the geocoder and coordinates to the routing service; these public services may log requests.

## Run locally

Requirements: Python 3.11 or newer and an internet connection.

### Windows (PowerShell)

From the repository folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

If Python 3.12 is not installed, check installed versions with `py -0p` and create the environment with an installed supported Python version.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Open the local URL printed by Streamlit. Keep the terminal open while using the app.

## Data sources and attribution

- **OpenStreetMap contributors** — geocoding and volunteered street/pedestrian network data. © OpenStreetMap contributors, licensed under the Open Database License (ODbL).
- **FOSS GIS routing service** — public walking-route calculations based on OpenStreetMap data. The community-operated service has usage limits and availability is not guaranteed.
- **NYC Open Data / FloodNet** — historical, quality-reviewed sensor-event summaries and sensor locations.

Public services can be unavailable, incomplete, rate-limited, or updated independently. A missing sensor event is not evidence that a route is dry. A sensor measures conditions at its own location; a nearby measurement does not establish conditions on a sidewalk, crossing, or the route as a whole.

## How route proximity works

The app requests actual walking-route geometry. It then calculates the approximate shortest geographic distance from each returned FloodNet sensor point to the selected route polyline. Sensor points within 300 metres are displayed as nearby historical context. This distance threshold is a research display rule, not a validated flood-impact radius. The app does not infer that a nearby street is flooded and does not rerank routes as “safe” or “unsafe.”

## Privacy and service limitations

The app does not ask for browser/device location, require an account, save submitted endpoints to a database, or accept public reports. The origin/destination text is sent to the OpenStreetMap Nominatim geocoder; coordinates are sent to the public routing service. Those providers may retain ordinary request logs. The app also fetches public FloodNet data. Do not enter sensitive personal information.

Public geocoding and routing endpoints are community services with fair-use policies, not guaranteed production APIs. For a public deployment, review current provider usage policies and consider hosting a properly licensed routing stack or using a service with a suitable service agreement.

## Testing

Run the repository's unit tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests cover the existing data-validation and supporting modules. They do not replace end-to-end testing against live geocoding, routing, or FloodNet services.

## Responsible use

RainRoute does not provide verified current street conditions, real-time sidewalk flooding, certified accessibility routing, official closures, or emergency guidance. Do not use it to make emergency decisions. Consult official NYC and National Weather Service information and follow local authorities' instructions.

## License

No license has been selected for the project. Publishing a repository on GitHub does not automatically grant others permission to reuse, modify, or redistribute its code. Choose a license before inviting reuse or contributions.
