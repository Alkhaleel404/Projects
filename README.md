# RainRoute NYC

RainRoute NYC is a Queens-focused civic technology learning app about flood information and uncertainty. It compares routes on a small, fictional pedestrian graph and presents public flood and weather information as separate kinds of context.

> **Important:** RainRoute NYC is an educational demonstration, not a navigation, emergency, or street-condition service. The demo routes and reports are fictional. Nothing in the app can tell you whether a street or route is safe now. Follow official alerts and emergency instructions.

## What you can explore

- **Route Explorer:** compare fictional route alternatives and see how a transparent, adjustable report penalty changes their ranking.
- **Flood Reports:** filter simulated reports by category, age, and demo segment.
- **FloodLens:** view historical FloodNet sensor events, FEMA modeled flood-hazard zones, and National Weather Service forecasts and alerts in separate layers.
- **Preparedness:** make and download a session-local flood-preparedness checklist.
- **About & Data:** review the source and project information in the app.

All demo locations, route segments, distances, and sample reports are simulated. Public data are not matched to the demo graph or presented as current street conditions.

## Run locally

Requires Python 3.11 or newer. Python 3.15.1 was used for the latest workspace checks.

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Open the local address printed by Streamlit. The app does not need API keys or bundled datasets. Binding to `127.0.0.1` keeps the development server on your computer.

## Run tests

The unit tests use Python's standard `unittest` library:

```bash
python -m unittest discover -s tests -v
```

To compile-check the application and its modules:

```bash
python -m compileall -q app.py routing.py flood_data.py preparedness.py data_sources.py
```

## Project layout

```text
.
├── app.py                 Streamlit pages and user interface
├── routing.py             Fictional graph and route-ranking logic
├── flood_data.py          Validated public-data API clients
├── data_sources.py        Source metadata used by the app
├── preparedness.py        Checklist content and download formatting
├── requirements.txt       Runtime Python dependencies
├── .streamlit/
│   └── config.toml        Streamlit defaults
├── tests/                 Unit tests for core modules
├── DATA_SOURCES.md        Source research, endpoints, and limitations
├── SECURITY_REVIEW.md     Project-level security notes and risks
└── README.md
```

The app is intentionally kept as a small set of top-level modules: it can be launched directly with Streamlit, and the test modules can import the core logic without extra package setup.

## Data, privacy, and limitations

FloodLens retrieves public data from NYC Open Data (FloodNet), FEMA, and the National Weather Service when those services are available. The map uses USGS topographic tiles. These sources have different coverage, timestamps, and limitations; historical measurements and modeled hazard zones do not establish present street conditions. External services may be unavailable or change.

The app uses fixed public reference areas and does not request your address or geolocation. No account, database, report-submission service, or API secret is used. USGS map tiles are loaded by the browser, so that service may receive ordinary connection metadata, including your IP address and tile coordinates. See [DATA_SOURCES.md](DATA_SOURCES.md) and [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for details.

This is not a production routing or life-safety system. It has no real pedestrian network, current street reports, verified accessibility attributes, or public submissions. Accessibility and emergency-use conformance have not been formally assessed.

## Deployment

No hosting service is configured by this project. If you choose to deploy it, Streamlit Community Cloud can run the app using `app.py` and `requirements.txt`; verify the live data integrations, privacy disclosures, and service limits after deployment. The hosting provider may process visitor connection metadata.

## License

No license has been selected for this project. Publishing the repository on GitHub does not by itself grant permission to reuse, modify, or redistribute its code. Add a license that reflects your intent before inviting others to use or contribute to it.
