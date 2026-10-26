# RainRoute NYC data-source registry

Last reviewed: 2026-10-25. A retrieval timestamp means when the app requested data; it does not mean the source data describes current conditions.

## Sources used by the current app

| Source | What RainRoute uses | Important limits |
|---|---|---|
| [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) | Geocodes user-entered Queens place names/addresses to coordinates. The app requests one result and restricts the search to a Queens-area bounding box. | Community geocoder with a usage policy and no production availability guarantee. User-entered place text is sent to the service and may be logged. |
| [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) | Street and foot-access network underlying walking routes and the map. | Volunteered geographic data can be incomplete or out of date. It does not certify sidewalk continuity, crossing safety, curb ramps, or accessibility. © OpenStreetMap contributors; ODbL. |
| [FOSS GIS public routing service](https://routing.openstreetmap.de/about.html) | Calculates pedestrian route geometry, distance, and a service-generated time estimate from the geocoded endpoints. | Community-operated, fair-use service; one request per second maximum per its published policy, and availability is not guaranteed. Route times are estimates, not observations of closures, weather, or flooding. Route coordinates are sent to the service, which states that requests are logged. |
| [NYC Open Data: FloodNet street flooding events](https://data.cityofnewyork.us/Environment/FloodNet-Street-Flooding-Events-Measured-by-FloodN/aq7i-eu5q) | Latest returned QC-reviewed historical event for each matched Queens sensor, joined to [sensor deployment metadata](https://data.cityofnewyork.us/resource/kb2e-tjy3.json) to get sensor coordinates. | Fixed sensors cover only some locations. The current request is limited to the 100 most recently returned event rows before matching sensor metadata; the display is not a complete historical archive. A measurement is at the sensor, not on every nearby street. Historical events are not live flood status. Dataset update cadence and source timestamps vary. |
| [NYC FloodNet project](https://www.floodnet.nyc/) | Background on sensor measurement and project methodology. | Interpret event summaries using the dataset documentation and attribution requirements. |

## How route-linked flood context works

1. The app geocodes the entered origin and destination.
2. A public walking router returns real route geometry based on OpenStreetMap data.
3. The app retrieves FloodNet historical event summaries and sensor coordinates.
4. For the selected route, it calculates approximate geographic distance from each sensor point to the route polyline and displays returned events within 300 metres.
5. Route alternatives show distance and routing-service time estimates alongside the number of nearby historical events. The app does not generate a safe/unsafe score or claim that nearby historical sensor measurements prove current sidewalk conditions.

The 300-metre threshold is a display filter, not a validated flood-impact radius. A lack of nearby sensor events does not establish that a route is dry. Sensor coverage is sparse, and the dataset is historical.

## Privacy and service behavior

The app does not request device/browser geolocation, create accounts, maintain a database, save endpoint history, or accept public reports. Place text is sent to Nominatim; coordinates are sent to the routing service. Providers may retain ordinary request logs. Public APIs can be unavailable, incomplete, or rate-limited.

## Sources researched but not used for route scoring

FEMA National Flood Hazard Layer zones, National Weather Service forecasts/alerts, and NYC stormwater scenario maps are useful contextual sources but do not establish whether a particular sidewalk is flooded now. They are not connected to route ranking in the current version, so the interface does not imply that they are.
