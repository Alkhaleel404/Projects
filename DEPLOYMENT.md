# RainRoute NYC — deployment runbook

## App entry point
- File: `app.py`
- Framework: Streamlit
- Python: 3.12 recommended
- Dependency file: `requirements.txt`
- Required secrets: none for the current implementation

## Streamlit Community Cloud
1. Sign in at https://share.streamlit.io/ using GitHub.
2. Create an app from the repository `Alkhaleel404/Projects`.
3. Select branch `main` and main file path `app.py`.
4. Select Python 3.12 in Advanced settings if prompted.
5. Deploy and wait for the build to complete.
6. Open the generated app URL and perform the smoke test in README.md.

The hosting account owner must complete deployment and accept the hosting provider's terms. A GitHub commit alone does not publish a live app.

## Local validation
Windows PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS/Linux:
```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m compileall -q .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m streamlit run app.py
```

## Public service dependencies
The app relies on OpenStreetMap Nominatim for geocoding, a community OpenStreetMap-based pedestrian routing service, and NYC Open Data/FloodNet for historical sensor evidence. No uptime guarantee is made for these services. Keep timeouts, attribution, error messages, and limitations in place; do not represent historical sensor data as live flood detection.

## Before sharing
- Run the automated tests locally and confirm GitHub Actions passes.
- Perform the README release smoke test against the deployed URL.
- Confirm that the public URL opens in a signed-out/private browser.
- Review the [data source registry](DATA_SOURCES.md) and [security review](SECURITY_REVIEW.md).
- Do not add credentials, personal addresses, or private information to the repository.
