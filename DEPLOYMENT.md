# RainRoute NYC — deployment runbook

## App configuration

- Framework: Streamlit
- Entry point: `app.py`
- Recommended Python: 3.12
- Dependencies: `requirements.txt`
- Required secrets/environment variables: none in the current implementation
- Hosting target: Streamlit Community Cloud

## Publish

1. Confirm the latest intended code is on the repository's `main` branch.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
3. Create an app using repository `Alkhaleel404/Projects`, branch `main`, and file path `app.py`.
4. Select Python 3.12 in Advanced settings if prompted; leave secrets empty.
5. Deploy and wait for the build status to finish.
6. Open the generated public `.streamlit.app` URL and complete every check below.
7. Save the deployed URL somewhere safe so it can be added to the project submission/demo materials.

The repository owner must perform this hosting step and verify the resulting URL. Merging code does not publish or validate a live app.

## Release smoke test

- [ ] URL loads without a traceback, including in a signed-out/private browser.
- [ ] Test a known Queens origin and destination; a route appears if the public router is available.
- [ ] Select each returned route and confirm metrics and historical-record context update.
- [ ] Check map attribution and origin/destination markers.
- [ ] Try an invalid place and confirm the app shows a helpful error rather than crashing.
- [ ] Confirm an unavailable FloodNet response leaves the route visible and shows a warning.
- [ ] Read the privacy, source, and limitations notices.
- [ ] Check the layout at desktop and phone widths.
- [ ] Confirm the GitHub Actions workflow passed for the exact commit being shared.

Public service outages can prevent a successful live-route test; record that as a dependency limitation rather than implying the app passed.

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

## Public service and safety notes

The app depends on OpenStreetMap Nominatim, a community-operated OpenStreetMap-based routing service, and NYC Open Data/FloodNet. They can be incomplete, rate-limited, or unavailable. Place text is sent to the geocoder and route coordinates to the router; providers may log requests. Do not enter sensitive personal information.

RainRoute is an educational civic evidence tool, not an emergency service, real-time flood detector, safety-certified navigation system, or accessibility guarantee. Do not use it to decide whether a route is safe.
