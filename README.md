# FloodLens NYC

**Explore gaps in public flood-monitoring coverage and investigate walking routes in Queens, NYC.**

FloodLens NYC is a student-built civic technology prototype. It maps listed FloodNet sensor locations, estimates how far sample points are from the nearest listed sensor, and lets users compare walking-route alternatives with nearby historical FloodNet observations.

> **Important:** FloodLens is a research and educational tool—not a flood forecast, emergency service, or safety-certified navigation app. Historical sensor events and the absence of nearby records cannot tell you whether a street or route is safe right now. Follow official alerts and local emergency instructions.

## Try the website

**Live website:** Not listed yet. A GitHub repository is the source code, not the running website. To publish a public website, follow [Deploy on Streamlit Community Cloud](#deploy-on-streamlit-community-cloud) below and add the verified app URL here.

**Source code:** [Alkhaleel404/Projects on GitHub](https://github.com/Alkhaleel404/Projects)

## Run it on your computer

You can run the app locally on Windows, macOS, or Linux. You will need:

- Python 3.12 (recommended)
- Git, or the ability to download this repository as a ZIP
- An internet connection to retrieve public data and use mapping services

### 1. Get the project

Open PowerShell on Windows or Terminal on macOS/Linux. Run:

```bash
git clone https://github.com/Alkhaleel404/Projects.git
cd Projects
```

Alternatively, open the [repository page](https://github.com/Alkhaleel404/Projects), select **Code → Download ZIP**, extract the ZIP, and open a terminal **inside the extracted `Projects` folder**.

Before continuing, make sure this folder contains `app.py` and `requirements.txt`. The commands below will not work from your general home folder.

### 2. Create a virtual environment

A virtual environment keeps this app's Python packages separate from other projects.

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
```

**macOS / Linux**

```bash
python3.12 -m venv .venv
```

If Python 3.12 is not installed, install it from [python.org](https://www.python.org/downloads/), then reopen your terminal and repeat this step. If you already use another compatible Python version, you can try it, but the project is documented and recommended for Python 3.12.

### 3. Install the required packages

Run the commands for your operating system **from the same `Projects` folder**.

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

### 4. Start the website

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS / Linux**

```bash
.venv/bin/python -m streamlit run app.py
```

Streamlit will print a local address, usually **http://localhost:8501**, and may open it in your browser automatically. If it does not, copy that address into your browser. Keep the terminal open while using the app. To stop it, press **Ctrl+C** in the terminal.

### Troubleshooting

- **`requirements.txt` not found:** You are not in the project folder. Use `cd Projects`, or open the extracted folder that contains `app.py` and `requirements.txt`.
- **`No module named streamlit`:** The dependencies were not installed in this environment. Repeat Step 3, then start the app using the same virtual-environment Python shown in Step 4.
- **Python 3.12 or `py` not found:** Install Python 3.12 from [python.org](https://www.python.org/downloads/). On Windows, make sure the Python launcher is included.
- **The app opens but data or routes fail to load:** FloodLens uses external public data and community-operated mapping services. Check your internet connection and try again later; a service may be unavailable or rate-limited.
- **Port 8501 is busy:** Use the local URL Streamlit prints in the terminal; it may offer a different port.

## Deploy on Streamlit Community Cloud

This is the route for making the app available to other people through a public website link, without asking them to install Python.

1. Make sure the code you want to publish is pushed to the `main` branch of this GitHub repository.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Select **Create app**.
4. Choose repository `Alkhaleel404/Projects`, branch `main`, and main file path `app.py`.
5. In advanced settings, select Python 3.12 if a Python-version option is available. The current app does not require any secrets or API keys.
6. Deploy and wait for Streamlit to finish building the app.
7. Open the generated `.streamlit.app` link. Test it in a private/incognito browser window and check that the app loads.
8. After you have verified that the public link works, replace the “Live website” note near the top of this README with that exact URL.

**Important:** A successful GitHub push does not deploy the app by itself. Do not list a live website URL until Streamlit has generated it and you have tested it.

## What FloodLens does

- **Sensor coverage map:** Displays listed Queens FloodNet sensors and sample points grouped by distance to the nearest listed sensor.
- **Coverage-gap investigation:** Highlights sample points that are more than 2 km from a listed sensor.
- **Walking-route comparison:** Geocodes two Queens locations and retrieves up to three walking-route alternatives when the public routing service is available.
- **Historical flood context:** Displays returned FloodNet sensor events within 300 metres of a selected route, when the data service is available.
- **Transparent comparison:** Shows route distance, a routing-service time estimate, and the number of nearby historical records without turning those records into a safety score.

## How to interpret the results

The coverage analysis samples a grid within the coordinate envelope of the listed sensor locations and measures straight-line distance to the nearest sensor. This envelope is **not an official Queens boundary** and may include water or non-residential areas. Distance bands are exploratory indicators of sensor proximity, not validated standards for adequate flood monitoring.

For route investigation, FloodLens uses OpenStreetMap-based walking routes and looks for returned historical sensor events within 300 metres of route geometry. The 300-metre distance is a display filter, not a validated flood-impact radius. The event query is limited and does not represent a complete archive or live flood status. Sensor measurements describe conditions at the sensor, not every nearby sidewalk.

A route with no nearby historical events may still experience flooding. Route times may not reflect closures, weather, crossing conditions, mobility needs, or current street conditions. FloodLens does not certify that a route is safe or accessible.

## Data sources and attribution

- [NYC Open Data — FloodNet street-flooding events](https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q)
- [NYC Open Data — FloodNet sensor deployment metadata](https://data.cityofnewyork.us/resource/kb2e-tjy3.json)
- [FloodNet NYC](https://www.floodnet.nyc/)
- [OpenStreetMap contributors and copyright](https://www.openstreetmap.org/copyright)
- [Nominatim geocoding service and usage policy](https://operations.osmfoundation.org/policies/nominatim/)
- [OpenStreetMap-based routing service information](https://routing.openstreetmap.de/about.html)

See [DATA_SOURCES.md](DATA_SOURCES.md) for source details, [DEPLOYMENT.md](DEPLOYMENT.md) for deployment checks, and [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for privacy and security considerations.

## Privacy

The app does not require an account, database, device geolocation, or saved trip history. Place names entered for route investigation are sent to OpenStreetMap Nominatim for geocoding, and route coordinates are sent to the public routing service. Those providers may process or log requests. Do not enter sensitive personal information.

## Project structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit app entry point and interface |
| `requirements.txt` | Python package dependencies |
| `coverage_analysis.py` | Sensor-proximity sampling and coverage analysis |
| `flood_data.py` | Validated public-data retrieval and parsing |
| `data_sources.py` | Public-data source helpers |
| `routing.py` | Route-related helpers |
| `preparedness.py` | Preparedness-related functionality |
| `tests/` | Automated tests |
| `DATA_SOURCES.md` | Data sources, methods, and limitations |
| `DEPLOYMENT.md` | Deployment and release-check instructions |
| `SECURITY_REVIEW.md` | Privacy and security review |

## Run the tests

After completing Steps 1–3 above, run the following from the project folder.

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**macOS / Linux**

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Passing automated tests does not guarantee that external public-data, geocoding, or routing services are currently available.

## License

No license is specified in this README. Check the repository for a license before reusing or redistributing the project.
