from __future__ import annotations

import math
import socket
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import folium
import streamlit as st
from streamlit_folium import st_folium

from coverage_analysis import sample_monitoring_gaps
from flood_data import DataSourceError, fetch_floodnet_events, fetch_floodnet_sensor_locations, parse_source_timestamp

st.set_page_config(
    page_title="FloodLens NYC · Flood monitoring evidence gaps",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root { --ink:#17252c; --muted:#62727b; --line:#d8e0e3; --paper:#f2f5f4; --teal:#087e8b; --amber:#b86a1d; }
html, body, [class*="css"] { font-family:Arial,Helvetica,sans-serif; color:var(--ink); }
.stApp { background:var(--paper); }
.block-container { max-width:1500px; padding-top:1.1rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:Arial,Helvetica,sans-serif; letter-spacing:-.035em; color:var(--ink); }
h2 { margin-top:.4rem; }
.hero { padding:1.6rem 1.9rem; border:1px solid #1f3e46; border-radius:8px; background:#122c34; color:#fff; margin-bottom:1rem; position:relative; overflow:hidden; }
.hero:after { content:"FL / EVIDENCE SYSTEM 01"; position:absolute; right:1.5rem; bottom:1.1rem; font:500 .7rem 'Courier New',monospace; letter-spacing:.1em; color:#86b8bc; }
.hero h1 { color:white; font-size:clamp(2.1rem,4vw,3.25rem); line-height:1.02; margin:.55rem 0 .7rem; max-width:900px; }
.hero p { color:#d1e0e2; font-size:1rem; max-width:850px; line-height:1.6; margin-bottom:.25rem; }
.kicker { font:500 .72rem 'Courier New',monospace; text-transform:uppercase; letter-spacing:.14em; color:#81ded0; }
.notice { padding:.9rem 1rem; border-left:4px solid #c48a34; border-radius:3px; background:#fff8e9; color:#654c24; }
.section-tag { font:500 .7rem 'Courier New',monospace; letter-spacing:.12em; text-transform:uppercase; color:#527078; }
.panel { border:1px solid var(--line); border-radius:8px; padding:1rem 1.1rem; background:#fff; }
.small-muted { color:var(--muted); font-size:.88rem; }
[data-testid="stMetric"] { border:1px solid var(--line); border-radius:6px; padding:.9rem 1rem; background:#fff; }
[data-testid="stMetricLabel"] { font-size:.75rem; text-transform:uppercase; letter-spacing:.07em; }
div.stButton > button { border-radius:5px; min-height:2.9rem; font-weight:700; border:1px solid #0f5961; }
div.stButton > button[kind="primary"] { background:#087e8b; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:7px; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:6px; overflow:hidden; }
hr { border-color:var(--line); }
code { font-family:'Courier New',monospace; }
@media(max-width:700px){.hero{padding:1.2rem;border-radius:6px}.hero:after{display:none}.block-container{padding-left:.7rem;padding-right:.7rem}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="kicker">Queens, New York · Urban flood evidence lab</div>
  <h1>Where are we missing<br>the evidence?</h1>
  <p>FloodLens maps gaps in public flood-monitoring coverage. It measures how far sampled locations are from listed FloodNet sensors, then lets you inspect historical observations and route-level context without turning missing data into a false safety score.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="notice"><strong>Important:</strong> This is an experimental research tool, not an emergency or safety-certified navigation service. FloodNet records below are historical, quality-reviewed sensor events—not a live flood-status feed. A route with no nearby records is not necessarily dry or safe. Follow official alerts and local instructions.</div>
""", unsafe_allow_html=True)


st.markdown('<div class="section-tag">01 / Monitoring coverage investigation</div>', unsafe_allow_html=True)
st.markdown("### Where is the sensor evidence thin?")
st.write("This analysis uses the published Queens FloodNet sensor inventory, including listed sensors that may have no event in the app's limited historical-event query. It samples a grid inside the inventory's coordinate envelope and measures distance to the nearest listed sensor.")
st.caption("A monitoring gap means less direct sensor coverage—not higher flood risk. The grid envelope is not a Queens boundary and may include water or land uses; sample percentages are not a borough-wide area estimate.")
@st.cache_data(ttl=3600, show_spinner=False)
def floodnet_sensor_inventory() -> list[dict[str, Any]]:
    return fetch_floodnet_sensor_locations()

try:
    with st.spinner("Loading the Queens FloodNet sensor inventory and sampling coverage…"):
        sensor_inventory = floodnet_sensor_inventory()
        coverage = sample_monitoring_gaps(sensor_inventory)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Listed Queens sensors", coverage["sensor_count"])
    m2.metric("Sample points over 2 km away", f'{coverage["over_2km_count"] / coverage["sample_count"]:.0%}')
    m3.metric("Median nearest-sensor distance", f'{coverage["median_distance_m"]:,} m')
    m4.metric("Farthest sample from a sensor", f'{max(point["distance_m"] for point in coverage["points"]):,} m')
    coverage_map = folium.Map(
        location=[(coverage["envelope"][0] + coverage["envelope"][2]) / 2,
                  (coverage["envelope"][1] + coverage["envelope"][3]) / 2],
        zoom_start=12, tiles="OpenStreetMap", control_scale=True,
    )
    bands = {"Within 1 km": "#16866b", "1–2 km": "#e0a12d", "Over 2 km": "#b64235"}
    for point in coverage["points"]:
        folium.CircleMarker(
            [point["lat"], point["lon"]], radius=3, weight=0,
            fill=True, fill_color=bands[point["band"]], fill_opacity=0.68,
            tooltip=f'{point["band"]} from nearest listed sensor · {point["distance_m"]:,} m',
        ).add_to(coverage_map)
    for sensor in sensor_inventory:
        folium.CircleMarker(
            [sensor["lat"], sensor["lon"]], radius=5, color="#123c52",
            fill=True, fill_color="#ffffff", fill_opacity=1,
            tooltip=f'Listed FloodNet sensor: {sensor["name"]}',
        ).add_to(coverage_map)
    legend = """
    <div style="position:fixed;bottom:24px;left:24px;z-index:9999;background:white;padding:10px 12px;border:1px solid #ccd6da;border-radius:5px;font-size:12px">
    <b>Distance to listed sensor</b><br>
    <span style="color:#16866b">●</span> Within 1 km<br>
    <span style="color:#e0a12d">●</span> 1–2 km<br>
    <span style="color:#b64235">●</span> Over 2 km<br>
    <span style="color:#123c52">○</span> Listed sensor location
    </div>
    """
    coverage_map.get_root().html.add_child(folium.Element(legend))
    st_folium(coverage_map, use_container_width=True, height=520, returned_objects=[])
    st.markdown("#### What the coverage calculation does")
    st.write("For each grid sample, FloodLens calculates great-circle distance to the nearest listed Queens sensor. Samples more than 2 km away are flagged for investigation. This is a transparent proximity screen, not a scientifically validated threshold for flood monitoring adequacy.")
    with st.expander("Inspect the most distant sample locations"):
        farthest = sorted(coverage["points"], key=lambda point: point["distance_m"], reverse=True)[:10]
        st.dataframe([{
            "Latitude": round(point["lat"], 5),
            "Longitude": round(point["lon"], 5),
            "Nearest listed sensor": point["nearest_sensor"],
            "Distance (m)": point["distance_m"],
            "Coverage band": point["band"],
        } for point in farthest], use_container_width=True, hide_index=True)
except (DataSourceError, ValueError) as exc:
    st.warning(f"Monitoring coverage analysis is temporarily unavailable: {exc}")
    st.caption("The route investigation can still be used when the sensor inventory service is unavailable.")

st.markdown('<div class="section-tag">02 / Route investigation</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("### Define your journey")
    st.caption("Enter two public Queens locations. RainRoute will map walking alternatives and inspect nearby historical sensor evidence. Your entries are not stored as trip history.")
    c1, c2, c3 = st.columns([1, 1, .7], gap="medium")
    with c1:
        origin_text = st.text_input("ORIGIN", placeholder="Jamaica Center, Queens", key="origin_input")
    with c2:
        destination_text = st.text_input("DESTINATION", placeholder="Rufus King Park, Queens", key="destination_input")
    with c3:
        st.write("")
        st.write("")
        run_route = st.button("Investigate routes  ↗", type="primary", use_container_width=True)
    st.caption("Privacy note: place text is sent to OpenStreetMap Nominatim; route coordinates are sent to a public routing service. Providers may log requests.")

ALLOWED_HOSTS = {"nominatim.openstreetmap.org", "routing.openstreetmap.de", "data.cityofnewyork.us"}

def _json_request(url: str, *, timeout: float = 15.0) -> Any:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise DataSourceError("A request was blocked because its destination was not an approved public-data service.")
    request = Request(url, headers={
        "User-Agent": "FloodLensNYC/1.0 (student civic technology project)",
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(5_000_001)
    except HTTPError as exc:
        raise DataSourceError(f"A public service returned HTTP {exc.code}. Please try again later.") from exc
    except (URLError, TimeoutError, socket.timeout, OSError) as exc:
        raise DataSourceError("A public mapping service could not be reached. Please retry later.") from exc
    if len(raw) > 5_000_000:
        raise DataSourceError("The public mapping response was larger than expected.")
    import json
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise DataSourceError("A public mapping service returned invalid data.") from exc

@st.cache_data(ttl=86400, show_spinner=False)
def geocode_place(query: str) -> dict[str, Any]:
    cleaned = query.strip()
    if len(cleaned) < 3 or len(cleaned) > 180:
        raise DataSourceError("Enter a place name or address between 3 and 180 characters.")
    payload = _json_request("https://nominatim.openstreetmap.org/search?" + urlencode({
        "q": cleaned + ", Queens, New York City, NY",
        "format": "jsonv2", "limit": 1, "countrycodes": "us",
        "viewbox": "-73.96,40.82,-73.70,40.54", "bounded": 1,
    }))
    if not isinstance(payload, list) or not payload:
        raise DataSourceError(f"No matching Queens location was found for “{cleaned}”. Try a nearby landmark or a more specific address.")
    item = payload[0]
    try:
        lat, lon = float(item["lat"]), float(item["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DataSourceError("The geocoder returned an unusable location.") from exc
    if not (40.45 <= lat <= 40.82 and -73.96 <= lon <= -73.70):
        raise DataSourceError("The selected result was outside the Queens study area. Try a Queens, NY location.")
    return {"label": str(item.get("display_name", cleaned))[:240], "lat": lat, "lon": lon}

@st.cache_data(ttl=600, show_spinner=False)
def walking_routes(start_lon: float, start_lat: float, end_lon: float, end_lat: float) -> list[dict[str, Any]]:
    coords = f"{start_lon:.6f},{start_lat:.6f};{end_lon:.6f},{end_lat:.6f}"
    url = "https://routing.openstreetmap.de/routed-foot/route/v1/driving/" + coords + "?" + urlencode({
        "alternatives": "3", "overview": "full", "geometries": "geojson", "steps": "false"
    })
    payload = _json_request(url, timeout=25)
    if not isinstance(payload, dict) or payload.get("code") != "Ok" or not isinstance(payload.get("routes"), list):
        raise DataSourceError("The walking router could not find a route for these locations. Try closer or more specific endpoints.")
    routes = []
    for item in payload["routes"][:3]:
        geometry = item.get("geometry", {}).get("coordinates", [])
        distance = item.get("distance")
        duration = item.get("duration")
        if not isinstance(geometry, list) or len(geometry) < 2 or not isinstance(distance, (int, float)):
            continue
        points = []
        for pair in geometry[:10000]:
            if isinstance(pair, list) and len(pair) >= 2:
                try:
                    lon, lat = float(pair[0]), float(pair[1])
                except (TypeError, ValueError):
                    continue
                if -180 <= lon <= 180 and -90 <= lat <= 90:
                    points.append((lat, lon))
        if len(points) >= 2:
            routes.append({"points": points, "distance_m": float(distance), "duration_s": float(duration or 0)})
    if not routes:
        raise DataSourceError("The walking router returned no usable route geometry.")
    return routes

@st.cache_data(ttl=3600, show_spinner=False)
def floodnet_events() -> dict[str, Any]:
    return fetch_floodnet_events()

def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    radius = 6371000.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2-lat1, lon2-lon1
    value = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*radius*math.asin(min(1.0, math.sqrt(value)))

def nearest_route_distance_m(point: tuple[float, float], line: list[tuple[float, float]]) -> float:
    # Local equirectangular projection is accurate enough for short-distance proximity screening in Queens.
    lat0 = math.radians(point[0])
    px, py = math.radians(point[1])*6371000*math.cos(lat0), math.radians(point[0])*6371000
    best = float("inf")
    for a, b in zip(line, line[1:]):
        ax, ay = math.radians(a[1])*6371000*math.cos(lat0), math.radians(a[0])*6371000
        bx, by = math.radians(b[1])*6371000*math.cos(lat0), math.radians(b[0])*6371000
        dx, dy = bx-ax, by-ay
        denom = dx*dx+dy*dy
        t = 0 if denom == 0 else max(0.0, min(1.0, ((px-ax)*dx+(py-ay)*dy)/denom))
        best = min(best, math.hypot(px-(ax+t*dx), py-(ay+t*dy)))
    return best

def event_rows_near_route(route: dict[str, Any], events: dict[str, Any]) -> list[dict[str, Any]]:
    matches = []
    for feature in events.get("features", []):
        if not isinstance(feature, dict):
            continue
        coords = feature.get("geometry", {}).get("coordinates", [])
        props = feature.get("properties", {})
        if not isinstance(coords, list) or len(coords) < 2 or not isinstance(props, dict):
            continue
        try:
            lon, lat = float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            continue
        distance = nearest_route_distance_m((lat, lon), route["points"])
        if distance <= 300:
            matches.append({
                "sensor": str(props.get("sensor_name", "FloodNet sensor")),
                "event_time": str(props.get("event_time", "Timestamp unavailable")),
                "depth": props.get("max_depth_inches"),
                "duration": props.get("duration_minutes"),
                "distance_m": round(distance),
                "lat": lat, "lon": lon,
            })
    return sorted(matches, key=lambda x: (x["distance_m"], x["event_time"]))[:12]

def _route_map(start: dict[str, Any], end: dict[str, Any], routes: list[dict[str, Any]], selected_index: int, events: list[dict[str, Any]]) -> folium.Map:
    center = [(start["lat"]+end["lat"])/2, (start["lon"]+end["lon"])/2]
    m = folium.Map(location=center, zoom_start=14, tiles="OpenStreetMap", control_scale=True)
    colors = ["#087e8b", "#d97706", "#64748b"]
    for idx, route in enumerate(routes):
        folium.PolyLine(route["points"], color=colors[idx % len(colors)], weight=7 if idx == selected_index else 4, opacity=0.95 if idx == selected_index else 0.55, tooltip=f"Route {idx+1} · {route['distance_m']/1000:.2f} km").add_to(m)
    folium.Marker([start["lat"], start["lon"]], tooltip="Origin", popup="Origin", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker([end["lat"], end["lon"]], tooltip="Destination", popup="Destination", icon=folium.Icon(color="blue", icon="flag")).add_to(m)
    for row in events:
        popup = f"{row['sensor']}<br>Recorded event: {row['event_time']}<br>Max depth: {row['depth']} in<br>Event duration: {row['duration']} min<br>Distance to route: {row['distance_m']} m"
        folium.CircleMarker([row["lat"], row["lon"]], radius=6, color="#b45309", fill=True, fill_opacity=.85, tooltip="Historical FloodNet event", popup=popup).add_to(m)
    folium.LayerControl().add_to(m)
    return m

if run_route:
    if not origin_text.strip() or not destination_text.strip():
        st.error("Enter both a starting point and destination.")
    elif origin_text.strip().casefold() == destination_text.strip().casefold():
        st.error("Choose two different locations.")
    else:
        try:
            with st.spinner("Finding the locations and calculating walking routes…"):
                origin = geocode_place(origin_text)
                destination = geocode_place(destination_text)
                routes = walking_routes(origin["lon"], origin["lat"], destination["lon"], destination["lat"])
            st.session_state["live_route_result"] = {"origin": origin, "destination": destination, "routes": routes}
        except DataSourceError as exc:
            st.error(str(exc))

result = st.session_state.get("live_route_result")
if result:
    origin, destination, routes = result["origin"], result["destination"], result["routes"]
    st.write("")
    st.markdown('<div class="section-tag">03 / Route analysis</div>', unsafe_allow_html=True)
    st.markdown("### Walking-route alternatives")
    st.caption(f"From {origin['label']} to {destination['label']}. Routes use OpenStreetMap pedestrian-network data; coverage and accessibility tags may be incomplete.")
    options = [f"Route {i+1} · {r['distance_m']/1000:.2f} km · about {max(1, round(r['duration_s']/60))} min" for i, r in enumerate(routes)]
    selected_label = st.selectbox("Inspect a route", options, key="selected_live_route")
    selected_index = options.index(selected_label)
    selected_route = routes[selected_index]
    a, b, c = st.columns(3)
    a.metric("Walking distance", f"{selected_route['distance_m']/1000:.2f} km")
    b.metric("Router time estimate", f"{max(1, round(selected_route['duration_s']/60))} min")
    c.metric("Route alternatives", str(len(routes)))
    st.caption("Time is the routing service's estimate and may not reflect walking speed, crossings, closures, mobility needs, weather, or flood conditions.")
    try:
        with st.spinner("Retrieving historical FloodNet sensor events…"):
            events_payload = floodnet_events()
        nearby = event_rows_near_route(selected_route, events_payload)
        left, right = st.columns([1.3, .9], gap="large")
        with left:
            st.markdown('<div class="section-tag">04 / Geographic evidence</div>', unsafe_allow_html=True)
            st.markdown("#### Route and sensor locations")
            st_folium(_route_map(origin, destination, routes, selected_index, nearby), use_container_width=True, height=560, returned_objects=[])
            st.caption("Map © OpenStreetMap contributors. Walking route calculated by the FOSS GIS routing service. Historical sensor points are shown only when within 300 m of the selected route.")
        with right:
            st.markdown('<div class="section-tag">05 / Historical observations</div>', unsafe_allow_html=True)
            st.markdown("#### Nearby FloodNet records")
            st.metric("Historical records within 300 m", str(len(nearby)))
            if nearby:
                for row in nearby:
                    with st.container(border=True):
                        st.markdown(f"**{row['sensor']}**")
                        st.write(f"Recorded: {row['event_time']}")
                        st.write(f"Maximum measured depth: {row['depth']} in")
                        st.write(f"Event duration: {row['duration']} min")
                        st.caption(f"{row['distance_m']} m from this route · historical sensor event")
            else:
                st.info("No returned FloodNet sensor events were found within 300 m of this route. This does not mean the route is dry: sensor coverage is sparse and the dataset is historical.")
            st.caption(f"FloodNet data retrieved: {events_payload.get('retrieved_at', 'timestamp unavailable')}")
        st.markdown('<div class="section-tag">06 / Compare</div>', unsafe_allow_html=True)
        st.markdown("#### What differs between routes?")
        comparison = []
        for idx, route in enumerate(routes):
            matched = event_rows_near_route(route, events_payload)
            comparison.append({
                "Route": f"Route {idx+1}",
                "Distance (km)": round(route["distance_m"]/1000, 2),
                "Router estimate (min)": max(1, round(route["duration_s"]/60)),
                "Historical records within 300 m": len(matched),
                "Interpretation": "Historical context only; not a safety score",
            })
        st.dataframe(comparison, use_container_width=True, hide_index=True)
        st.markdown('<div class="notice"><strong>How to interpret this:</strong> Route geometry and flood-sensor locations are real geographic data. Sensor events are quality-reviewed historical measurements at the sensor itself, not observations of every nearby sidewalk. RainRoute does not convert these records into a “safe/unsafe” label or claim that a route is currently flooded.</div>', unsafe_allow_html=True)
    except DataSourceError as exc:
        st.warning(f"The walking route was found, but FloodNet context could not be loaded: {exc}")
        st.caption("The route and distance remain real; no flood-data conclusion is available when the public dataset cannot be reached.")

st.divider()
st.markdown('<div class="section-tag">06 / Transparency</div>', unsafe_allow_html=True)
st.markdown("### Sources, methods & known blind spots")
d1, d2, d3 = st.columns(3)
with d1:
    st.markdown("**Street network**")
    st.write("OpenStreetMap contributors supply volunteered geographic street and foot-access data. Routes are calculated by the FOSS GIS public walking router.")
    st.caption("Attribution: © OpenStreetMap contributors · ODbL")
with d2:
    st.markdown("**Flood observations**")
    st.write("NYC FloodNet sensor-event summaries provide historical quality-reviewed measurements. Nearby means a sensor point is within 300 metres of route geometry; the display uses the latest returned historical record per matched sensor, not a count of every event in the source dataset.")
    st.caption("Source: NYC Open Data / FloodNet")
with d3:
    st.markdown("**Privacy and uncertainty**")
    st.write("No account, database, device geolocation, or public-report submission. Place text is sent to the geocoder; coordinates are sent to the routing service. These services may log requests.")
    st.caption("No location history is stored by this app.")
st.caption("RainRoute NYC · Student civic technology project · Public services can be unavailable, incomplete, rate-limited, or updated independently. Do not use for emergency decisions.")
