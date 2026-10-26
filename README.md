# FloodLens NYC

**FloodLens NYC is a Queens-focused civic-data prototype for exploring gaps in public flood-monitoring coverage.** It maps listed FloodNet sensor locations, estimates the distance from sample points to the nearest listed sensor, and lets users inspect historical sensor events and optional walking-route context.

> **Important:** FloodLens is an educational research tool, not a flood forecast, emergency service, or safety-certified navigation app. A nearby sensor or a lack of historical events does not tell you whether a street is safe.

## Try the website

**Hosted app:** *Add your public Streamlit Community Cloud URL here after deployment and testing.*

The GitHub repository is the source code; it is not itself the running website. If no hosted-app link is shown above, follow the deployment instructions below or run the app on your computer.

## Run FloodLens on your computer

You will need:
- A computer running Windows, macOS, or Linux
- Git
- **Python 3.12** (recommended)
- An internet connection, because the app retrieves public data and uses external mapping, geocoding, and routing services

### 1. Download the project

Open a terminal (PowerShell on Windows, Terminal on macOS/Linux) and run:

```bash
git clone https://github.com/Alkhaleel404/Projects.git
cd Projects
```

If you downloaded the repository as a ZIP instead, extract it and open a terminal in the extracted **Projects** folder. The folder should contain `app.py` and `requirements.txt`.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -3.12 -m venv .venv
```

**macOS / Linux:**

```bash
python3.12 -m venv .venv
```

If the command says Python 3.12 is not installed, install Python 3.12 from [python.org](https://www.python.org/downloads/) and try again. On Windows, make sure the Python launcher (`py`) is installed. A virtual environment keeps this project's packages separate from other Python projects.

### 3. Install the dependencies

Run these commands from inside the **Projects** folder.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

### 4. Start the website

**Windows PowerShell:**

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS / Linux:**

```bash
.venv/bin/python -m streamlit run app.py
```

Streamlit should open your browser automatically. If it does not, copy the **Local URL** shown in the terminal (usually [http://localhost:8501](http://localhost:8501)) into your browser. Keep the terminal open while using the app. To stop the local server, press `Ctrl+C` in that terminal.

### Common problems

- **`requirements.txt` not found:** You are probably in the wrong directory. Run `cd Projects` (or open the extracted project folder) and check that `app.py` and `requirements.txt` are there.
- **`No module named streamlit` (or another package):** Install dependencies again from the project folder using the command in Step 3. Make sure you use the same virtual-environment Python for installation and startup.
- **Python 3.12 not found:** Install Python 3.12 from [python.org](https://www.python.org/downloads/), then reopen your terminal.
- **The page opens but data or routes do not load:** The app depends on public data and third-party mapping services. Check your internet connection and try again later; those services may be unavailable or rate-limited.
- **Port 8501 is already in use:** Streamlit may offer another local URL in the terminal. Open the URL it prints.

## Host a public website with Streamlit Community Cloud

To let people use FloodLens through a link without installing Python:

1. Push the project to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Choose **Create app** (or the equivalent deployment option).
4. Select repository **`Alkhaleel404/Projects`**, branch **`main`**, and main file **`app.py`**.
5. Choose Python **3.12** in the app's advanced settings if the option is shown. No app secrets are currently required.
6. Deploy and wait for the build to finish.
7. Open the generated `.streamlit.app` URL in a private/incognito browser window to check that it is publicly accessible.
8. Add the verified public URL to the **Try the website** section above.

**Note:** Do not invent or share a deployment URL until Streamlit has actually created the app and you have tested it. A GitHub repository link is not the same as a hosted website.

## What the app does

- **Monitoring coverage:** Maps the listed Queens FloodNet sensor inventory and sample points grouped by distance to the nearest listed sensor.
- **Coverage gaps:** Highlights sample points farther from listed sensors.
- **Historical context:** Displays event records returned by the public data source.
- **Route investigation:** Lets users compare walking-route alternatives and nearby historical sensor context when the external services are available.

## How to interpret the results

The analysis generates sample points within the latitude/longitude envelope of the returned sensor locations, calculates straight-line distance to the nearest listed sensor, and groups sample points into exploratory bands: **within 1 km**, **1–2 km**, and **over 2 km**.

These are measures of proximity to listed sensors—not flood risk, safety, or monitoring adequacy. The coordinate envelope is not an official Queens boundary and may include water or non-residential areas. The historical-event query is limited and is not a complete archive or a live flood-status feed. Straight-line distance does not account for elevation, drainage, flood pathways, or barriers.

## Data sources and attribution

- [NYC Open Data — FloodNet street-flooding events](https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q)
- [NYC Open Data](https://data.cityofnewyork.us/)
- [FloodNet NYC](https://www.floodnet.nyc/)
- [OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright)
- [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/)
- [OpenStreetMap routing service information](https://routing.openstreetmap.de/about.html)

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment notes and [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for privacy and security considerations.

## Privacy

The current prototype does not require an account, database, device geolocation, or saved trip history. Place names entered for route investigation may be sent to external geocoding services, and route requests may be sent to routing services. These providers may process or log requests. Do not enter sensitive personal information.

## Project structure

- `app.py` — Streamlit app entry point and user interface
- `requirements.txt` — Python package dependencies
- `coverage_analysis.py` — sensor-proximity sampling and analysis
- `flood_data.py` — retrieval and parsing of FloodNet data
- `data_sources.py` — public-data source helpers
- `routing.py` — route lookup and related context
- `preparedness.py` — preparedness-related functionality
- `DEPLOYMENT.md` — hosting and validation notes
- `SECURITY_REVIEW.md` — privacy and security review

## License

Check the repository for a license before reusing or redistributing this project.
