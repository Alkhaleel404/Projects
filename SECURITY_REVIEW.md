# Security review

This is a project-level review of the current RainRoute NYC implementation, not a professional security audit, penetration test, or guarantee of security.

## Controls implemented

- No account system, report submission endpoint, user database, analytics SDK, API secret, or user geolocation. Source requests use fixed geographic references.
- Outbound JSON requests are restricted to HTTPS and an allowlist of the official FEMA, NWS, and NYC Open Data hosts. Redirect targets are checked against the same allowlist; response reads have a byte limit and a timeout.
- FEMA polygons, FloodNet values and coordinates, NWS forecast fields, and source timestamps are validated and bounded before use. Malformed/unavailable data is surfaced as a source-specific error instead of a success-shaped empty layer.
- HTML originating from FloodNet sensor names and event times is escaped before being included in map popup/tooltip markup. FEMA attributes are not inserted into HTML labels.
- The app uses a fixed list of route endpoints and a fixed report schema. There is no user-controlled path, address, narrative, photograph, or report content.
- All seeded report and graph data are labeled simulated. Historical sensor events, modeled FEMA zones, forecast values, and alerts use separate UI sections and descriptions.
- Streamlit usage statistics are disabled in `.streamlit/config.toml`. The documented local launch binds to `127.0.0.1`.
- `.gitignore` excludes virtual environments, secrets files, environment files, logs, and serialized model artifacts. This project does not use a model or store credentials.
- Core route and checklist computation runs locally. Public API timeouts and malformed JSON are handled as explicit data-source errors.

## Remaining risks and limitations

- Streamlit and mapping dependencies must be kept updated; this project has not undergone dependency-vulnerability scanning.
- Public FEMA, NYC Open Data, NWS, and USGS tile services may observe ordinary network metadata, return stale/incomplete data, rate-limit, or become unavailable. A cloud deployment may additionally process visitor connection metadata.
- USGS map tiles are requested by the browser. The tile provider can observe IP address and tile coordinates. No sensitive location is sent by the app, but this is not an anonymity guarantee.
- A malicious or malformed upstream response could expose defects in the third-party JSON/map rendering libraries despite application validation.
- The map is an informational display. It is not a life-safety system and has not been tested for use during emergencies.
- Keyboard and semantic accessibility features are present where supported by Streamlit, but formal WCAG 2.2 AA evaluation and screen-reader/browser testing have not been performed.
- No dependency lockfile is included; dependency resolution can change across installs. For a public deployment, pin and review resolved versions as part of release preparation.

## Operational guidance

- Do not add private keys or credentials to source control. The current integrations require no API key.
- Keep demo reporting disabled unless a moderation, retention, rate-limiting, privacy, and deletion design is implemented.
- If routing is upgraded, use a verified pedestrian network and routing profile, disclose third-party requests, validate sidewalk/accessibility attributes, and never infer a route's present safety from broad polygons.
- Recheck source documentation, endpoints, service limits, licensing, and data timestamps before deployment or public presentation.
