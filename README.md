# RainRoute NYC

RainRoute NYC is a Queens-focused civic technology research app. It compares real walking-route options with nearby historical NYC FloodNet sensor observations, making the relationship between geographic evidence and its limitations visible.

> **Important:** RainRoute is experimental. It is not an emergency service, a safety-certified navigation app, or a source of verified current sidewalk conditions. FloodNet events are historical measurements at fixed sensors. No route is labelled safe or unsafe.

## Feature inventory

### 1. Real walking-route planning
- Enter a starting point and destination as public place names, landmarks, or street addresses.
- Geocode each entry with OpenStreetMap Nominatim, requesting one result and restricting results to a Queens-area bounding box.
- Validate endpoint text length, require both endpoints, reject identical endpoint text, and reject geocoded points outside the configured study area.
- Request pedestrian routes from a public OpenStreetMap-based walking-routing service.
- Display up to three route alternatives when the service returns them.
- Show route distance and the routing service's estimated travel time.
- Keep successful route results in the current Streamlit session so the user can inspect route options without resubmitting the form.
- Provide source-specific messages for invalid locations, failed route requests, malformed service responses, and unavailable public services.

### 2. Interactive route map
- Render the actual returned route geometry on an interactive Folium/Leaflet map.
- Draw up to three route alternatives with different colours.
- Emphasize the currently selected route with a thicker, more opaque line.
- Mark origin and destination.
- Display route tooltips with route number and distance.
- Display historical FloodNet sensor-event markers within 300 metres of the selected route.
- Show sensor popups with sensor name, event timestamp, maximum measured depth, event duration, and distance from the selected route.
- Include map zoom/pan controls, scale, and a layer control.
- Attribute the underlying OpenStreetMap map data.

### 3. Historical FloodNet evidence linked to route geometry
- Fetch public NYC Open Data / FloodNet historical sensor-event records and sensor deployment metadata.
- Use sensor coordinates to compare each event point with the selected route's actual polyline.
- Calculate approximate point-to-route distance using a local equirectangular projection appropriate for short distances in Queens.
- Display returned events within 300 metres of the selected route.
- Show sensor name, recorded event timestamp, maximum measured depth in inches, event duration in minutes, and distance to the route.
- Order displayed events by proximity and timestamp and cap the displayed list at 12.
- Show the count of returned events within the 300-metre display radius.
- Show the data retrieval timestamp when supplied by the data client.
- Explain when no matching events are returned and keep the route available if FloodNet context cannot be loaded.

The 300-metre threshold is a display filter, not a validated flood-impact radius. Sensor coverage is sparse, events are historical, and a sensor measurement does not establish conditions on a nearby sidewalk or crossing. No matching event does not mean that a route is dry.

### 4. Route comparison
- Select an individual route for detailed inspection.
- Show selected-route metrics for distance, estimated travel time, and number of available alternatives.
- Compare every returned alternative in a table with distance, estimated time, and number of nearby historical FloodNet events.
- Calculate the nearby-event count separately against each route's own geometry.
- Explain that historical-event counts are context only, not a safety score; the app does not rank routes as safe or unsafe.

### 5. Interface and user experience
- RainRoute NYC-branded hero section with Queens civic-technology context.
- Clear experimental-use and uncertainty notice.
- Two-field route-entry form and primary route-finding action.
- Dashboard-style metric cards, map and evidence columns, historical-event cards, and route-comparison table.
- Custom typography, colour palette, spacing, borders, rounded panels, and narrow-screen CSS adjustments.
- Separate data/methods/limitations section describing the street network, flood observations, privacy, and uncertainty.
- Source attribution and explanatory captions near the map and results.

### 6. Privacy and security protections
- No account registration or login.
- No request for browser/device geolocation.
- No user database or saved endpoint-history feature.
- No public flood-report submission feature.
- Input length checks and Queens-area geographic bounds checks.
- HTTPS-only outbound requests to an explicit hostname allowlist.
- Network timeouts, response-size limits, JSON parsing checks, and source-specific error handling.
- Type/range checks for geocoded coordinates and route geometry before rendering.
- Streamlit caching to reduce repeated requests.
- Clear disclosure that place text is sent to Nominatim and route coordinates are sent to the public routing service; those providers may log requests.
- A warning not to enter sensitive personal information.

These protections reduce some risks but do not constitute a professional security audit. Third-party services may retain request logs, and no security or availability guarantee is made.

## Data sources and attribution

- **OpenStreetMap Nominatim** — geocodes entered place names and addresses. [Usage policy](https://operations.osmfoundation.org/policies/nominatim/).
- **OpenStreetMap contributors** — volunteered map and pedestrian-network data. [Copyright and ODbL attribution](https://www.openstreetmap.org/copyright).
- **FOSS GIS public routing service** — calculates route geometry and service-generated distance/time estimates. [Service information](https://routing.openstreetmap.de/about.html).
- **NYC Open Data / FloodNet** — historical sensor-event summaries and sensor deployment metadata. [FloodNet event dataset](https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q) · [FloodNet project](https://www.floodnet.nyc/).

Public services can be unavailable, incomplete, rate-limited, or updated independently. OpenStreetMap data does not certify sidewalk continuity, crossings, curb ramps, or accessibility. Route estimates do not account reliably for an individual's walking speed, mobility needs, weather, current closures, or flooding.

## Deploy on Streamlit Community Cloud

RainRoute is a Streamlit app and can be hosted directly from this repository. No API keys or secrets are required for the current feature set.

1. Push the project to a GitHub repository you control.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Choose **Create app**, then select repository `Alkhaleel404/Projects`, branch `main`, and main file path `app.py`.
4. In **Advanced settings**, select Python **3.12** if a version is requested. Leave secrets empty; the current app does not need them.
5. Deploy. When the app finishes building, open its generated `.streamlit.app` URL and test a Queens origin and destination.
6. After later commits to `main`, check the app's deployment status and logs if the hosted version does not update.

If you fork or move the repository, choose your own repository and branch in step 3. The public geocoding, routing, and FloodNet services can rate-limit requests or be temporarily unavailable. Deployment does not make those services more reliable.

### Release smoke test

Before sharing the URL with judges, test the deployed app in a fresh browser session:

- [ ] The page loads without a Python traceback.
- [ ] A known Queens origin and destination return at least one route, when public services are available.
- [ ] The map shows the route geometry and origin/destination markers.
- [ ] Historical FloodNet context either loads with timestamps or shows a clear unavailable/empty state.
- [ ] Route alternatives can be selected and their metrics update.
- [ ] An invalid or out-of-area location produces a useful message instead of crashing.
- [ ] The limitations and privacy notice are visible.
- [ ] Test on a phone-sized viewport as well as desktop.

Do not call the app production-validated until this smoke test has been completed. The app is an educational research demonstration, not an emergency service.

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

If Python 3.12 is not installed, use `py -0p` to inspect installed versions and create the environment with an installed supported Python version.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Open the local URL printed by Streamlit. Keep the terminal open while using the app.

## Testing

Run the repository's unit tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The existing unit tests cover supporting/data-validation modules; they do not replace end-to-end tests of the live geocoder, router, FloodNet service, browser rendering, or accessibility. The app must be run and checked against live services before it is treated as production-ready.

## Not included / limitations

RainRoute does **not** currently provide:
- Verified live sidewalk-flooding detection or official street-closure data.
- A validated flood-risk model, machine-learning model, or route safety score.
- Certified wheelchair-accessibility routing.
- Emergency navigation, evacuation instructions, or a guarantee that any route is safe.
- User accounts, saved trips, user-submitted reports, or location history.
- FEMA flood-zone, National Weather Service forecast/alert, or NYC stormwater scenario layers in the current route-planning interface. These sources are discussed in the source registry but are not used to score routes.

Consult official NYC and National Weather Service information and follow local authorities' instructions. Do not use RainRoute for emergency decisions.

## License

No license has been selected for the project. Publishing a repository on GitHub does not automatically grant others permission to reuse, modify, or redistribute the code. Choose a license before inviting reuse or contributions.
