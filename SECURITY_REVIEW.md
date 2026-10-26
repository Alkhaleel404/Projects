# Security and privacy review

This is a project-level review, not a professional security audit or a guarantee of security.

## Current design

- No account, user database, public report submission, analytics SDK, or device/browser geolocation.
- Origin/destination text is sent to OpenStreetMap Nominatim for geocoding. The resulting coordinates are sent to the community-operated OpenStreetMap-based walking router. Both services may log requests; do not enter sensitive personal information.
- FloodNet public data is fetched from NYC Open Data. No API secrets are required.
- Requests are HTTPS-only and the JSON helper checks hostnames against a fixed allowlist, applies timeouts, caps response size, and handles HTTP/network/JSON errors.
- Geocoded coordinates are checked against a Queens-area bounding box. Returned route coordinates and event coordinates are type-checked and range-checked before display.
- Route geometry is real OpenStreetMap-based pedestrian routing. FloodNet event points are compared geometrically with the selected route and only shown within the documented 300 m display threshold.
- The app does not convert historical measurements into a current safe/unsafe label. A missing event is not evidence that a route is dry.
- Streamlit usage statistics are disabled in .streamlit/config.toml; the documented local command binds to 127.0.0.1.
- The interface uses system fonts rather than importing fonts from a separate font CDN, reducing unnecessary third-party browser requests.

## Remaining risks

- Public geocoding/routing services are community services with fair-use limits and no guaranteed uptime. Providers may log request metadata and route coordinates.
- OpenStreetMap data may be incomplete or stale; foot access, sidewalk continuity, curb ramps, crossing details, and closures are not guaranteed.
- FloodNet sensors are sparse and events are historical. A sensor measurement does not describe the entire route or present conditions.
- Third-party dependencies and public service responses can change. No dependency vulnerability scan, formal penetration test, or emergency-use validation has been performed.
- Streamlit hosting may expose visitor connection metadata to the hosting provider. Before public deployment, review hosting and provider privacy policies and usage terms.
- Formal WCAG accessibility testing and screen-reader/browser compatibility testing have not been completed.

## Responsible use

RainRoute is a student civic technology research tool, not an emergency service or safety-certified navigation system. Follow official alerts and local emergency instructions. Do not rely on this app to decide whether a route is safe.
