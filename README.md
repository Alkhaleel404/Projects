# RainRoute NYC

RainRoute NYC is a Queens-focused civic technology learning app about flood information and uncertainty. It compares routes on a small, fictional pedestrian graph and presents public flood and weather information as separate kinds of context.

> **Important:** RainRoute NYC is an educational demonstration, not a navigation, emergency, or street-condition service. The demo routes and reports are fictional. Nothing in the app can tell you whether a street or route is safe now. Follow official alerts and emergency instructions.

## What You Can Explore

- **Route Explorer:** Compare fictional route alternatives and see how a transparent, adjustable report penalty changes their ranking.
- **Flood Reports:** Filter simulated reports by category, age, and demo segment.
- **FloodLens:** View historical FloodNet sensor events, FEMA modeled flood-hazard zones, and National Weather Service forecasts and alerts in separate layers.
- **Preparedness:** Create and download a session-local flood-preparedness checklist.
- **About & Data:** Review the source and project information in the app.

All demo locations, route segments, distances, and sample reports are simulated. Public data are not matched to the demo graph or presented as current street conditions.

## Getting Started

### Requirements

- Python **3.12 recommended** (Python 3.11 or newer is intended; the project's CI tests with Python 3.12).
- Git, if you want to clone the repository instead of downloading it.
- An internet connection to install dependencies and retrieve public data.

### 1. Get the project files

Choose one option.

**Option A — Clone with Git**

Open PowerShell (Windows) or a terminal (macOS/Linux), navigate to the folder where you keep projects, and run:

```bash
git clone https://github.com/Alkhaleel404/Projects.git
cd Projects
```

**Option B — Download from GitHub**

1. Open https://github.com/Alkhaleel404/Projects
2. Select **Code → Download ZIP**.
3. Extract the ZIP.
4. Open a terminal in the extracted `Projects` folder — the folder that contains `app.py` and `requirements.txt`.

**Check that you are in the right folder before continuing.** These files should appear in the listing:

PowerShell:
```powershell
Get-ChildItem app.py, requirements.txt
```

macOS/Linux:
```bash
ls app.py requirements.txt
```

If either file cannot be found, you are not in the project directory yet. Use `cd` to move into the folder that contains them. Do not run the installation commands from your home directory unless the project files are there.

### 2. Install and run on Windows

In PowerShell, from the project directory, run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

These commands call the virtual environment's Python directly, so you do **not** need to activate it or change PowerShell's execution policy. If Python 3.12 is not installed, install it first or use another supported Python version that is installed; check available Python versions with `py -0p`.

### 3. Install and run on macOS or Linux

From the project directory, run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

### 4. Open the app

Streamlit prints a local address in the terminal. Open that address in your browser. The server is bound to `127.0.0.1`, which makes it accessible from your own computer rather than directly from other devices on your network.

Keep the terminal open while using the app. To stop the server, press `Ctrl+C` in that terminal.

### Troubleshooting

- **`requirements.txt` or `app.py` not found:** You are probably in the wrong directory. Navigate into the project folder and repeat the file check above.
- **PowerShell says script execution is disabled:** The commands above do not use the activation script, so activation is unnecessary.
- **`py -3.12` cannot find Python:** Python 3.12 may not be installed. Run `py -0p` to list installed versions, then install Python 3.12 or use an installed supported version.
- **`No module named streamlit`:** Install dependencies using the virtual environment's Python command shown above, then launch Streamlit using that same Python executable.
- **Dependency installation fails:** Confirm your Python version, internet connection, and the full error message. The CI workflow tests the project using Python 3.12.

The app does not require API keys or bundled datasets. Public-data features may depend on the availability of their external services.

## Testing

Run the unit tests from the project directory.

Windows:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS/Linux:
```bash
.venv/bin/python -m unittest discover -s tests -v
```

To check that the application and its core modules compile:

Windows:
```powershell
.\.venv\Scripts\python.exe -m compileall -q app.py routing.py flood_data.py preparedness.py data_sources.py
```

macOS/Linux:
```bash
.venv/bin/python -m compileall -q app.py routing.py flood_data.py preparedness.py data_sources.py
```

## Project Structure

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
└── README.md              Project documentation
```

The project uses a small set of top-level Python modules. This keeps the app straightforward to launch with Streamlit and allows tests to import the core logic without additional package setup.

## Data Sources

FloodLens retrieves public information from the following sources when available:

- **NYC Open Data / FloodNet:** Historical flood-sensor observations.
- **FEMA:** Modeled flood-hazard information.
- **National Weather Service (NWS):** Public weather forecasts and alerts.
- **USGS:** Topographic map tiles.

These sources have different coverage, timestamps, and limitations. Historical measurements, modeled hazard zones, forecasts, and alerts provide different kinds of information and must not be treated as interchangeable evidence of current street conditions.

For further details, see [DATA_SOURCES.md](DATA_SOURCES.md).

## Privacy and Security

RainRoute NYC is designed to minimize personal data collection.

- No user account is required.
- No database or report-submission service is used.
- The app does not request your home address or device geolocation.
- No API secrets are required by the documented setup.
- The preparedness checklist is session-local.
- Public data are presented separately from the fictional route graph.

The browser loads USGS map tiles directly, so that service may receive ordinary connection metadata, including your IP address and requested tile coordinates. Hosting the application publicly may also expose visitor connection metadata to the hosting provider.

Review [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for additional security considerations and known risks.

## Limitations and Responsible Use

RainRoute NYC is a learning and demonstration project, not a production routing or life-safety system.

It does not provide:

- A real pedestrian street network.
- Verified current street or flood conditions.
- Live, verified pedestrian reports.
- Verified accessibility attributes for routes.
- Public user-submitted reports.
- A guarantee that any route is safe.

Accessibility and emergency-use conformance have not been formally assessed.

**Never rely on this application to make emergency decisions.** Follow official alerts, local authorities, and emergency instructions.

## Deployment

No hosting service is configured by this project.

If you choose to deploy the application, Streamlit Community Cloud is one possible option. Configure the deployment to use `app.py` and install dependencies from `requirements.txt`.

Before deployment, verify that the public-data integrations, privacy disclosures, and service limits are appropriate for a publicly accessible application.

## License

No license has been selected for this project. Publishing a repository on GitHub does not automatically grant others permission to reuse, modify, or redistribute its code. Select an appropriate open-source license before inviting others to use or contribute to the project.
