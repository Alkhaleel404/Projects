from __future__ import annotations

import ast
import html
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium

from data_sources import DATA_SOURCES
from flood_data import (
    DataSourceError,
    fetch_fema_hazards,
    fetch_floodnet_events,
    fetch_nws_alerts,
    fetch_nws_forecast,
    parse_source_timestamp,
)
from preparedness import (
    CHECKLIST,
    create_checklist_text,
    select_checklist_items,
)
from routing import (
    DEMO_REPORT_SCENARIOS,
    DEMO_EDGES,
    DEMO_LOCATIONS,
    DEMO_NODES,
    REPORT_EXPIRY,
    Route,
    build_routes,
    demo_reports,
    format_distance,
    format_duration,
)


st.set_page_config(
    page_title="RainRoute NYC",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_floodnet_events() -> dict[str, Any]:
    return fetch_floodnet_events()


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_fema_hazards() -> dict[str, Any]:
    return fetch_fema_hazards()


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_nws_forecast() -> dict[str, Any]:
    return fetch_nws_forecast()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_nws_alerts() -> dict[str, Any]:
    return fetch_nws_alerts()


st.markdown(
    """
    <style>
        .block-container { max-width: 1440px; padding-top: 1.6rem; padding-bottom: 3rem; }
        h1, h2, h3 { letter-spacing: -.035em; }
        h1 { font-size: clamp(2.2rem, 4vw, 3.5rem) !important; line-height: 1.03 !important; }
        h2 { font-size: 1.55rem !important; }
        [data-testid="stMetric"] { border: 1px solid rgba(15,118,110,.18); border-radius: 14px; padding: 15px 16px; background: rgba(15,118,110,.035); }
        [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px; border-color: rgba(20,50,50,.15); }
        .eyebrow { font-size: .75rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: #0f766e; }
        .hero-panel { padding: clamp(1.2rem, 3vw, 2.4rem); border: 1px solid rgba(15,118,110,.2); border-radius: 22px; background: linear-gradient(135deg, rgba(15,118,110,.10), rgba(255,255,255,.72) 68%); }
        .hero-kicker { display: inline-block; margin-bottom: .8rem; padding: .32rem .62rem; border-radius: 999px; background: #d9f1eb; color: #115e59; font-size: .75rem; font-weight: 800; letter-spacing: .07em; text-transform: uppercase; }
        .hero-copy { max-width: 52rem; font-size: 1.08rem; line-height: 1.7; color: #355454; }
        .section-kicker { color: #0f766e; font-size: .74rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
        .status-note { border: 1px solid rgba(180,83,9,.24); border-left: 4px solid #b45309; border-radius: 12px; padding: 13px 16px; background: rgba(245,158,11,.07); }
        .feature-label { color: #0f766e; font-size: .74rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
        div.stButton > button { border-radius: 10px; min-height: 2.75rem; font-weight: 650; transition: border-color .15s ease, transform .15s ease; }
        div.stButton > button:hover { border-color: #0f766e; transform: translateY(-1px); }
        a:focus-visible, button:focus-visible, input:focus-visible { outline: 3px solid #0b83a0 !important; outline-offset: 2px !important; }
        @media (max-width: 700px) {
            .block-container { padding: 1rem .85rem 2rem; }
            h1 { font-size: 2.15rem !important; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def _page_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="eyebrow">RainRoute NYC · Queens</div><h1>{html.escape(title)}</h1>', unsafe_allow_html=True)
    st.write(subtitle)


def _navigate_to_page(page: str) -> None:
    st.session_state["main_navigation"] = page


def _render_start_here() -> None:
    st.markdown(
        """
        <div class="hero-panel">
          <div class="hero-kicker">Queens · Civic technology prototype</div>
          <h1>Flood decisions deserve better context.</h1>
          <p class="hero-copy">Explore how uncertain reports can change a route's ranking, and learn why public flood data is evidence—not a guarantee about any individual street.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        '<div class="status-note"><strong>Learning demo, not navigation.</strong> The route network, distances, and sample reports are fictional. Public datasets are shown separately and may have different coverage or timestamps. Do not use this app to choose a real-world route or make emergency decisions.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    main_col, preview_col = st.columns([1.05, 0.95], gap="large")
    with main_col:
        st.markdown('<div class="section-kicker">Start with the core experiment</div>', unsafe_allow_html=True)
        st.subheader("Compare two possible routes")
        st.write(
            "Choose a start and destination, change the simulated report scenario, "
            "and compare distance-only rankings with an illustrative report-weighted score."
        )
        st.button(
            "Explore route comparison  →",
            type="primary",
            width="stretch",
            on_click=_navigate_to_page,
            args=("Route Explorer",),
        )
        st.caption("The scoring rule is a teaching heuristic—not a flood probability or safety rating.")
    with preview_col:
        with st.container(border=True):
            st.markdown('<div class="feature-label">The demo network</div>', unsafe_allow_html=True)
            st.graphviz_chart(_route_diagram(None), use_container_width=True)
            st.caption("Fictional nodes and connections. No real streets or live route geometry.")
    st.write("")
    st.markdown('<div class="section-kicker">Explore the evidence</div>', unsafe_allow_html=True)
    reports_col, evidence_col, prep_col = st.columns(3, gap="medium")
    with reports_col:
        with st.container(border=True):
            st.markdown("### Sample reports")
            st.write("Filter fictional reports by type, age, and route segment. Explore why unverified reports are not confirmed conditions.")
            st.button("Explore reports", width="stretch", on_click=_navigate_to_page, args=("Flood Reports",))
    with evidence_col:
        with st.container(border=True):
            st.markdown("### Public flood context")
            st.write("Inspect available FloodNet events, FEMA modeled hazard zones, and National Weather Service information separately.")
            st.button("Open FloodLens", width="stretch", on_click=_navigate_to_page, args=("FloodLens",))
    with prep_col:
        with st.container(border=True):
            st.markdown("### Preparedness")
            st.write("Build a practical checklist for preparing for heavy rain and flooding, without collecting personal location data.")
            st.button("Open checklist", width="stretch", on_click=_navigate_to_page, args=("Preparedness",))
    st.divider()
    st.markdown('<div class="section-kicker">Designed around uncertainty</div>', unsafe_allow_html=True)
    st.subheader("What is real—and what is simulated?")
    real_col, demo_col = st.columns(2, gap="large")
    with real_col:
        with st.container(border=True):
            st.markdown("**Public information, when services respond**")
            st.write(
                "FloodLens can retrieve public FloodNet sensor-event summaries, FEMA modeled "
                "flood-hazard zones, and NWS forecast or alert context. Coverage and timestamps "
                "vary. None of these sources proves that a particular sidewalk is flooded now."
            )
    with demo_col:
        with st.container(border=True):
            st.markdown("**Simulated learning features**")
            st.write(
                "The route graph, route distances, and Flood Reports are fictional. "
                "There is no real pedestrian routing, geolocation, report submission, or "
                "community-report database."
            )
    st.info(
        "For real flood warnings, consult official NYC and National Weather Service channels. "
        "Avoid floodwater and follow local emergency guidance."
    )

def _format_timestamp(value: str | None) -> str:
    parsed = parse_source_timestamp(value)
    if parsed is None:
        return value or "Not supplied by the source"
    return parsed.strftime("%b %d, %Y %H:%M UTC")


def _route_diagram(selected: Route | None) -> str:
    selected_edges = set(selected.edge_ids) if selected is not None else set()
    endpoints = (
        {selected.nodes[0], selected.nodes[-1]}
        if selected is not None
        else set()
    )
    lines = [
        "graph RainRoute {",
        'graph [bgcolor="transparent", rankdir=LR, nodesep=0.65, ranksep=0.8];',
        'node [shape=box, style="rounded,filled", fillcolor="#e9f4f5", color="#6a8994", fontname="Arial", fontsize=11, margin="0.16,0.09"];',
        'edge [fontname="Arial", fontsize=9, color="#9aadb3", fontcolor="#536b78"];',
    ]
    for node in DEMO_NODES:
        is_endpoint = node.id in endpoints
        fill = "#d8eff0" if is_endpoint else "#f4f7f7"
        lines.append(
            f'"{node.id}" [label="{node.label}", fillcolor="{fill}"];'
        )
    for edge in DEMO_EDGES:
        if edge.id in selected_edges:
            lines.append(
                f'"{edge.start}" -- "{edge.end}" [label="{edge.distance_meters} m", color="#087e91", fontcolor="#087e91", penwidth=3];'
            )
        else:
            lines.append(
                f'"{edge.start}" -- "{edge.end}" [label="{edge.distance_meters} m"];'
            )
    lines.append("}")
    return "\n".join(lines)


def _swap_route_endpoints() -> None:
    st.session_state["route_origin"], st.session_state["route_destination"] = (
        st.session_state["route_destination"],
        st.session_state["route_origin"],
    )


def _reset_route() -> None:
    locations = tuple(DEMO_LOCATIONS)
    st.session_state["route_origin"] = locations[0]
    st.session_state["route_destination"] = locations[1]


def _render_route_explorer() -> None:
    _page_header(
        "Route Explorer",
        "A hands-on lesson in how route choices can change when uncertain reports are considered. This is a simulated network, not directions.",
    )
    st.warning(
        "Practice only: every point, segment, distance, and report is simulated. "
        "These options do not represent real streets or current conditions. Do not travel using these routes."
    )
    with st.container(border=True):
        st.markdown(
            "**How to use this page:** pick two demo points, choose a report scenario, "
            "then compare the alternatives and see what changes their ranking. "
            "All calculations happen locally in this app."
        )

    locations = tuple(DEMO_LOCATIONS)
    if "route_origin" not in st.session_state:
        st.session_state["route_origin"] = locations[0]
    if "route_destination" not in st.session_state:
        st.session_state["route_destination"] = locations[1]

    scenario_col, route_count_col, ranking_col = st.columns([1.1, 0.75, 1.2])
    with scenario_col:
        scenario = st.selectbox(
            "Simulated report scenario",
            DEMO_REPORT_SCENARIOS,
            key="demo_report_scenario",
            help="These sample records are fictional and only change the teaching demonstration.",
        )
    with route_count_col:
        route_limit = st.slider("Alternatives to compare", 1, 5, 3)
    with ranking_col:
        ranking_mode = st.radio(
            "Rank alternatives by",
            ("Include demo reports", "Distance only"),
            horizontal=True,
            help="The report penalty is an adjustable teaching heuristic, not a hazard probability.",
        )
    if ranking_mode == "Include demo reports":
        report_penalty = st.slider(
            "Illustrative penalty per recent unverified demo report",
            min_value=0,
            max_value=1000,
            value=300,
            step=100,
            format="%d m-equivalent",
        )
    else:
        report_penalty = 0

    left, right, switch = st.columns([1, 1, 0.65])
    with left:
        origin_label = st.selectbox(
            "Origin",
            locations,
            key="route_origin",
            help="Preset demonstration point only; no geocoding or location permission is used.",
        )
    with right:
        destination_label = st.selectbox(
            "Destination",
            locations,
            key="route_destination",
            help="Preset demonstration point only; no geocoding or location permission is used.",
        )
    with switch:
        st.write("")
        st.button(
            "Switch endpoints",
            width="stretch",
            on_click=_swap_route_endpoints,
        )
        st.button("Reset route", width="stretch", on_click=_reset_route)

    try:
        reports = demo_reports(scenario=scenario)
        routes = build_routes(
            DEMO_LOCATIONS[origin_label],
            DEMO_LOCATIONS[destination_label],
            reports=reports,
            limit=route_limit,
            report_penalty_meters=report_penalty,
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    if not routes:
        st.info("The demonstration graph has no connected path for this pair.")
        return

    options = {
        f"Option {index + 1} · {format_distance(route.distance_meters)} · {len(route.edge_ids)} segments": route
        for index, route in enumerate(routes)
    }
    comparison = [
        {
            "Option": f"Option {index + 1}",
            "Demo distance": format_distance(route.distance_meters),
            "Illustrative time": format_duration(route.estimated_minutes),
            "Recent demo reports": len(route.recent_reports),
            "Stale demo reports": len(route.stale_reports),
            "Unknown segments": route.unknown_segments,
            "Score (m-equivalent)": route.score_meters,
        }
        for index, route in enumerate(routes)
    ]
    st.subheader("Compare alternatives")
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    chosen_label = st.selectbox("Inspect an option", tuple(options))
    selected = options[chosen_label]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Demo distance", format_distance(selected.distance_meters))
    metric_columns[1].metric("Illustrative walk time", format_duration(selected.estimated_minutes))
    metric_columns[2].metric("Recent demo reports", str(len(selected.recent_reports)))
    metric_columns[3].metric(
        "Condition / access unknown",
        f"{selected.unknown_segments} / {selected.accessibility_unknown_segments}",
    )

    detail, graph = st.columns([0.95, 1.05], gap="large")
    with detail:
        st.subheader("Why this option ranks here")
        st.write(
            f"**Illustrative score:** {selected.score_meters:,} m-equivalent."
        )
        st.write(
            f"**Scoring rule:** {selected.distance_meters:,} m base length + "
            f"{len(selected.recent_reports)} recent unverified demo report(s) × "
            f"{report_penalty} m-equivalent each."
        )
        if ranking_mode == "Distance only":
            st.caption("Report records are shown for context, but do not affect this ranking.")
        if selected.stale_reports:
            st.write(
                f"**Stale demo reports:** {len(selected.stale_reports)}; older than "
                f"{REPORT_EXPIRY.total_seconds() / 3600:.0f} hours and excluded from scoring."
            )
        if selected.recent_reports:
            for report in selected.recent_reports:
                st.write(
                    f"Unverified simulated report on segment {report.edge_id}: "
                    f"{report.category}."
                )
        else:
            st.write("No recent simulated reports are attached to these segments.")
        st.write(
            "**Conditions:** unknown on all segments. No report is not evidence that a segment is dry."
        )
        st.write(
            "**Accessibility:** unknown. The graph has no verified curb-ramp, crossing, "
            "grade, sidewalk, or step-free attributes."
        )
        st.caption(
            "Walking time uses a fixed illustrative speed of 1.33 m/s. Neither route length, "
            "score, nor time is a measured street-route estimate."
        )

    with graph:
        st.subheader("Schematic demo network")
        st.caption("Not to scale. Highlighted edges show the selected graph path, not real streets.")
        st.graphviz_chart(_route_diagram(selected), use_container_width=True)

    st.markdown(
        '<div class="status-note">A lower heuristic score is not a safety rating. '
        'Flood hazards and historical sensor events are shown separately in FloodLens and '
        'are not map-matched to this simulated graph.</div>',
        unsafe_allow_html=True,
    )
    st.button(
        "Explore real flood context in FloodLens",
        type="primary",
        on_click=_navigate_to_page,
        args=("FloodLens",),
    )

    st.divider()
    st.subheader("What if the reports changed?")
    st.write(
        f"Compare Balanced and Rainy-day sample reports for the same "
        f"{origin_label} → {destination_label} trip. The routes remain fictional; "
        "only the report scenario changes."
    )
    balanced_routes = build_routes(
        DEMO_LOCATIONS[origin_label],
        DEMO_LOCATIONS[destination_label],
        reports=demo_reports(scenario="Balanced sample"),
        limit=route_limit,
        report_penalty_meters=report_penalty,
    )
    rainy_routes = build_routes(
        DEMO_LOCATIONS[origin_label],
        DEMO_LOCATIONS[destination_label],
        reports=demo_reports(scenario="Rainy-day sample"),
        limit=route_limit,
        report_penalty_meters=report_penalty,
    )
    scenario_columns = st.columns(2, gap="large")
    for column, scenario_name, scenario_routes in (
        (scenario_columns[0], "Balanced Scenario", balanced_routes),
        (scenario_columns[1], "Rainy-day Scenario", rainy_routes),
    ):
        with column:
            st.markdown(f"### {scenario_name}")
            if not scenario_routes:
                st.info("No path is available for these demo endpoints.")
                continue
            best = scenario_routes[0]
            st.metric(
                "Top-ranked demo option",
                format_distance(best.distance_meters),
                delta=f"{best.score_meters:,} m-equivalent score",
                delta_color="off",
            )
            st.caption(
                f"{len(best.recent_reports)} recent report(s) · "
                f"{len(best.stale_reports)} stale report(s) · "
                f"illustrative time {format_duration(best.estimated_minutes)}"
            )
            st.dataframe(
                [
                    {
                        "Option": f"Option {index + 1}",
                        "Demo distance": format_distance(route.distance_meters),
                        "Recent reports": len(route.recent_reports),
                        "Score (m-equivalent)": route.score_meters,
                        "Path": " → ".join(
                            next(node.label for node in DEMO_NODES if node.id == node_id)
                            for node_id in route.nodes
                        ),
                    }
                    for index, route in enumerate(scenario_routes)
                ],
                use_container_width=True,
                hide_index=True,
            )
    st.caption(
        "Both columns use the same origin, destination, alternative count, and penalty. "
        "This isolates how fictional report patterns affect a teaching example; it does not "
        "measure real flood risk or identify a safe route."
    )


def _render_demo_reports() -> None:
    _page_header(
        "Flood Reports",
        "Inspect fictional observations, filter by type and age, and see how uncertain evidence is handled—not a public reporting channel.",
    )
    st.warning(
        "Every record on this page is simulated demo data. RainRoute does not accept, store, "
        "or verify public flood reports."
    )
    now = datetime.now(timezone.utc)
    scenario = st.selectbox(
        "Choose a demonstration scenario",
        DEMO_REPORT_SCENARIOS,
        key="demo_report_scenario",
        help="The same sample scenario can be explored in Route Explorer.",
    )
    reports = demo_reports(now, scenario=scenario)
    filter_columns = st.columns(3)
    categories = sorted({report.category for report in reports})
    with filter_columns[0]:
        category_filter = st.selectbox("Report type", ("All types", *categories))
    with filter_columns[1]:
        age_filter = st.selectbox(
            "Report age",
            ("Recent and stale", "Recent only", "Stale only"),
        )
    with filter_columns[2]:
        segment_filter = st.selectbox(
            "Demo segment",
            ("All segments", *(edge.id for edge in DEMO_EDGES)),
        )

    visible_reports = []
    for report in reports:
        age = now - report.observed_at
        stale = age > REPORT_EXPIRY
        if category_filter != "All types" and report.category != category_filter:
            continue
        if age_filter == "Recent only" and stale:
            continue
        if age_filter == "Stale only" and not stale:
            continue
        if segment_filter != "All segments" and report.edge_id != segment_filter:
            continue
        visible_reports.append((report, age, stale))

    recent_count = sum(not stale for _, _, stale in visible_reports)
    stale_count = len(visible_reports) - recent_count
    metric_columns = st.columns(3)
    metric_columns[0].metric("Visible demo records", len(visible_reports))
    metric_columns[1].metric("Recent, unverified", recent_count)
    metric_columns[2].metric("Stale", stale_count)

    if not visible_reports:
        st.info("No demonstration records match those filters. That is not evidence that a real street is dry.")

    for report, age, stale in visible_reports:
        age_text = (
            f"{int(age.total_seconds() // 3600)} hours ago"
            if age >= timedelta(hours=1)
            else f"{max(1, int(age.total_seconds() // 60))} minutes ago"
        )
        with st.container(border=True):
            first, second, third = st.columns([0.8, 1.2, 1.3])
            first.markdown(f"**{report.id} · simulated**")
            second.write(f"**{report.category}**")
            third.write(f"{'Stale' if stale else 'Recent, unverified'} · {age_text}")
            st.caption(
                f"Demo segment {report.edge_id} · observed {report.observed_at.strftime('%Y-%m-%d %H:%M UTC')} · "
                f"{'excluded from the route heuristic because it is older than 24 hours.' if stale else 'unverified; may affect the illustrative route score.'}"
            )
    if visible_reports:
        st.caption(
            "The 24-hour freshness cutoff and the report penalty are teaching examples. "
            "They are not a validated measure of risk or a claim about real conditions."
        )
    st.button(
        "Use this scenario in Route Explorer",
        type="primary",
        on_click=_navigate_to_page,
        args=("Route Explorer",),
    )
    st.info(
        "No account, address, photo, free-text narrative, or exact location is requested. "
        "These records are fixed fictional examples; live community submissions and persistent storage are not implemented."
    )
    st.markdown(
        "Historical instrument readings are a separate source. See **FloodLens** for "
        "Queens FloodNet sensor events; those readings are not user reports and are not current street status."
    )


def _add_fema_layer(map_widget: folium.Map, hazards: dict[str, Any]) -> None:
    feature_collection = {
        "type": "FeatureCollection",
        "features": hazards["features"],
    }

    def style_feature(feature: dict[str, Any]) -> dict[str, Any]:
        zone = feature.get("properties", {}).get("FLD_ZONE", "Unknown")
        if zone in ("A", "AE", "AH", "AO", "AR", "V", "VE"):
            color = "#146b9a"
        elif zone == "X":
            color = "#df9b29"
        else:
            color = "#7c6ba8"
        return {
            "color": color,
            "weight": 1,
            "fillColor": color,
            "fillOpacity": 0.25,
        }

    folium.GeoJson(
        feature_collection,
        name="FEMA NFHL flood hazard zones",
        style_function=style_feature,
    ).add_to(map_widget)


def _base_map(location: list[float], zoom_start: int) -> folium.Map:
    m = folium.Map(
        location=location,
        zoom_start=zoom_start,
        control_scale=True,
        tiles=None,
    )
    folium.TileLayer(
        tiles=(
            "https://basemap.nationalmap.gov/arcgis/rest/services/"
            "USGSTopo/MapServer/tile/{z}/{y}/{x}"
        ),
        name="USGS The National Map Topo",
        attr="USGS The National Map",
        overlay=False,
        control=True,
        max_zoom=18,
        max_native_zoom=16,
    ).add_to(m)
    return m


def _render_fema_map(hazards: dict[str, Any]) -> None:
    m = _base_map([40.702, -73.805], 13)
    _add_fema_layer(m, hazards)
    folium.LayerControl(collapsed=False).add_to(m)
    st_folium(m, use_container_width=True, height=500, returned_objects=[], key="fema_map")
    zone_counts: dict[str, int] = {}
    for feature in hazards["features"]:
        zone = feature["properties"]["FLD_ZONE"]
        zone_counts[zone] = zone_counts.get(zone, 0) + 1
    if zone_counts:
        st.markdown("**Text summary of displayed FEMA zones**")
        st.write(" · ".join(f"{zone}: {count} mapped feature(s)" for zone, count in sorted(zone_counts.items())))
    st.caption(
        "FEMA NFHL flood zones are official mapped/regulatory hazard context—not current "
        "street conditions, a rainfall forecast, or proof that a particular sidewalk is flooded. "
        "The query requests WGS84 coordinates and does not include route geometry. If map tiles "
        "fail, the source polygons and text summary remain separate from any route."
    )
    if hazards["skipped_feature_count"]:
        st.warning(
            f"FEMA returned {hazards['skipped_feature_count']} feature(s) with unusable "
            "geometry or properties; the displayed map is incomplete."
        )
    if hazards["possibly_truncated"]:
        st.warning(
            "The service reached the app's 500-feature display cap; this map may omit features."
        )
    if hazards["feature_count"] == 0:
        st.info(
            "The service returned no features in this bounded query. This is not evidence that the area is hazard-free."
        )


def _render_floodnet_map(events: dict[str, Any]) -> None:
    features = events["features"]
    timestamps_have_offsets = all(
        feature["properties"]["event_timestamp_has_timezone"] for feature in features
    )
    m = _base_map([40.66, -73.79], 10)
    bounds: list[list[float]] = []
    for feature in features:
        longitude, latitude = feature["geometry"]["coordinates"]
        properties = feature["properties"]
        name = html.escape(properties["sensor_name"])
        timestamp = html.escape(properties["event_time"])
        popup = folium.Popup(
            (
                f"<b>{name}</b><br>"
                f"Recorded event time: {timestamp}<br>"
                f"Maximum measured depth: {properties['max_depth_inches']:.2f} in<br>"
                f"Event duration: {properties['duration_minutes']:.1f} min<br>"
                "Historical FloodNet sensor event; not current street conditions."
            ),
            max_width=310,
        )
        folium.CircleMarker(
            location=[latitude, longitude],
            radius=6,
            color="#087e91",
            fill=True,
            fill_color="#087e91",
            fill_opacity=0.75,
            tooltip=f"Historical sensor event: {name}",
            popup=popup,
        ).add_to(m)
        bounds.append([latitude, longitude])
    if bounds:
        m.fit_bounds(bounds, padding=(22, 22))
    st_folium(m, use_container_width=True, height=500, returned_objects=[], key="floodnet_map")
    st.caption(
        "Each marker is a FloodNet sensor site with its latest event among the API's "
        "100 newest Queens events. Depth is measured at that fixed sensor, not across the "
        "surrounding street. Event timestamps are shown exactly as supplied; "
        f"{'all displayed source timestamps include timezone offsets' if timestamps_have_offsets else 'some or all displayed source timestamps do not include timezone offsets'}."
    )


def _render_nws_context() -> None:
    st.subheader("Official weather context · Southern Queens")
    forecast_col, alert_col = st.columns(2, gap="large")
    with forecast_col:
        st.markdown("**NWS forecast**")
        try:
            forecast = _cached_nws_forecast()
        except DataSourceError as exc:
            st.error(f"NWS forecast unavailable: {exc}")
            st.caption("FloodNet, FEMA, and the offline demo remain separate.")
        else:
            st.caption(
                f"NWS grid data updated: {_format_timestamp(forecast['updated'])} · "
                f"forecast generated: {_format_timestamp(forecast['generated_at'])} · "
                f"retrieved: {_format_timestamp(forecast['retrieved_at'])}"
            )
            if forecast["skipped_period_count"]:
                st.warning(
                    f"NWS returned {forecast['skipped_period_count']} unusable forecast "
                    "period(s); displayed coverage may be incomplete."
                )
            for period in forecast["periods"][:4]:
                temperature = (
                    f"{period['temperature']}°{period['temperature_unit']}"
                    if period["temperature"] is not None
                    else "Temperature unavailable"
                )
                precipitation = period["precipitation_probability"]
                rain = (
                    f"{precipitation:g}% precipitation chance"
                    if precipitation is not None
                    else "Precipitation probability unavailable"
                )
                st.write(
                    f"**{period['name']}** · {temperature} · {period['short_forecast']} · {rain}"
                )
    with alert_col:
        st.markdown("**NWS active alerts**")
        try:
            alerts = _cached_nws_alerts()
        except DataSourceError as exc:
            st.error(f"NWS alerts unavailable: {exc}")
            st.caption("Check official emergency channels directly.")
        else:
            st.caption(
                f"Alert feed updated: {_format_timestamp(alerts['updated'])} · "
                f"retrieved: {_format_timestamp(alerts['retrieved_at'])}"
            )
            if alerts["skipped_alert_count"]:
                st.warning(
                    f"NWS returned {alerts['skipped_alert_count']} malformed alert(s); "
                    "the alert list may be incomplete."
                )
            if alerts["possibly_truncated"]:
                st.warning(
                    "NWS returned at least 50 alerts; only the first 50 are displayed."
                )
            if alerts["alerts"]:
                for alert in alerts["alerts"]:
                    st.warning(
                        f"{alert['event']} · {alert['severity']} · "
                        f"{alert['headline']} · expires {_format_timestamp(alert['expires'])}"
                    )
            else:
                st.success("NWS reports no active alerts in the Southern Queens zone.")


def _render_floodlens() -> None:
    _page_header(
        "FloodLens",
        "Explore modeled flood-hazard zones, measured historical flood events, and official weather context as distinct evidence types.",
    )
    st.markdown(
        '<div class="status-note">A modeled hazard zone, past sensor reading, weather forecast, '
        'and current sidewalk condition are different things. None of the first three alone '
        'proves that a particular street is flooded now.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    _render_nws_context()
    st.divider()
    data_view = st.radio(
        "Choose a FloodLens view",
        (
            "FloodNet event history",
            "Historical sensors vs demo route",
            "FEMA flood hazard zones",
        ),
        horizontal=True,
    )

    if data_view == "FloodNet event history":
        st.subheader("Measured historical sensor events · Queens")
        st.write(
            "FloodNet event summaries are based on instrument measurements and reviewed "
            "by the FloodNet team. They are historical records, not a live sensor feed."
        )
        try:
            with st.spinner("Loading FloodNet sensor-event summaries…"):
                events = _cached_floodnet_events()
        except DataSourceError as exc:
            st.error(f"FloodNet data unavailable: {exc}")
            st.info("The route and preparedness demonstrations remain available offline.")
        else:
            st.caption(
                f"Latest event in displayed sensor records: "
                f"{events['latest_event_time'] or 'No event timestamp returned'} · "
                f"fetched: {_format_timestamp(events['retrieved_at'])} · "
                f"{events['feature_count']} sensor sites"
            )
            if events["skipped_event_count"] or events["unmatched_sensor_count"]:
                st.warning(
                    f"FloodNet coverage is partial: {events['skipped_event_count']} "
                    "event record(s) were unusable and "
                    f"{events['unmatched_sensor_count']} sensor(s) lacked valid matching "
                    "Queens location metadata."
                )
            if events["features"]:
                _render_floodnet_map(events)
                with st.expander("Accessible text list of displayed sensor events"):
                    for feature in events["features"]:
                        details = feature["properties"]
                        timezone_note = (
                            "timezone offset supplied"
                            if details["event_timestamp_has_timezone"]
                            else "timezone offset not supplied"
                        )
                        st.write(
                            f"**{details['sensor_name']}** — event {details['event_time']} "
                            f"(source timestamp, {timezone_note}); maximum measured "
                            f"depth {details['max_depth_inches']:.2f} in; duration "
                            f"{details['duration_minutes']:.1f} min. Historical sensor event, "
                            "not current conditions."
                        )
                st.markdown(
                    "[FloodNet project](https://www.floodnet.nyc/) · "
                    "[NYC Open Data event summaries](https://data.cityofnewyork.us/resource/aq7i-eu5q.json) · "
                    "[sensor location metadata](https://data.cityofnewyork.us/resource/kb2e-tjy3.json)"
                )
            else:
                st.info(
                    "No usable Queens sensor events or matching sensor metadata were returned. "
                    "This does not mean there was no flooding."
                )
    elif data_view == "Historical sensors vs demo route":
        st.subheader("Historical sensor evidence beside a simulated route")
        st.write(
            "The left panel summarizes FloodNet's returned historical events. The right "
            "panel is a separate, fictional route exercise. They are not spatially joined."
        )
        history_col, route_col = st.columns(2, gap="large")
        with history_col:
            st.markdown("### Real data · FloodNet")
            try:
                with st.spinner("Loading FloodNet historical events…"):
                    events = _cached_floodnet_events()
            except DataSourceError as exc:
                st.error(f"FloodNet data unavailable: {exc}")
            else:
                features = events["features"]
                st.caption(
                    f"Retrieved {_format_timestamp(events['retrieved_at'])} · "
                    f"{len(features)} matched Queens sensor site(s) · "
                    "source event times are historical."
                )
                if features:
                    peak_features = sorted(
                        features,
                        key=lambda feature: feature["properties"]["max_depth_inches"],
                        reverse=True,
                    )
                    peak = peak_features[0]
                    peak_details = peak["properties"]
                    st.metric(
                        "Highest measured depth in this returned sample",
                        f"{peak_details['max_depth_inches']:.2f} in",
                        help=(
                            "Peak among the latest returned event per matched sensor "
                            "in the API's 100-newest-event query; not an all-time peak."
                        ),
                    )
                    st.write(
                        f"**Sensor:** {peak_details['sensor_name']} · "
                        f"**Source event time:** {peak_details['event_time']} · "
                        f"**Duration:** {peak_details['duration_minutes']:.1f} min"
                    )
                    chart_values = {
                        (
                            f"{feature['properties']['sensor_name']} · "
                            f"{feature['properties']['event_time'][:10]}"
                        ): feature["properties"]["max_depth_inches"]
                        for feature in peak_features[:8]
                    }
                    st.bar_chart(
                        {"Maximum event depth (in)": chart_values},
                        height=250,
                    )
                    st.caption(
                        "Top returned sensor-site events, not a continuous rainfall or "
                        "street-depth history. Source timestamps are shown as supplied."
                    )
                    st.dataframe(
                        [
                            {
                                "Sensor": feature["properties"]["sensor_name"],
                                "Event time": feature["properties"]["event_time"],
                                "Maximum depth (in)": round(
                                    feature["properties"]["max_depth_inches"], 2
                                ),
                                "Duration (min)": round(
                                    feature["properties"]["duration_minutes"], 1
                                ),
                            }
                            for feature in peak_features[:8]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
                    if events["skipped_event_count"] or events["unmatched_sensor_count"]:
                        st.warning(
                            "The returned historical sample has incomplete records or "
                            "sensor matches; see FloodNet's source for full coverage."
                        )
                else:
                    st.info(
                        "No usable sensor events were returned. This is not evidence "
                        "that the area had no flooding."
                    )
        with route_col:
            st.markdown("### Simulated data · route exercise")
            st.warning(
                "This route is entirely fictional. It is not on the FloodNet map, "
                "and sensor readings do not change its route score."
            )
            route_controls, scenario_controls = st.columns(2)
            with route_controls:
                demo_origin = st.selectbox(
                    "Demo origin",
                    tuple(DEMO_LOCATIONS),
                    key="history_demo_origin",
                )
                demo_destination = st.selectbox(
                    "Demo destination",
                    tuple(DEMO_LOCATIONS),
                    index=1,
                    key="history_demo_destination",
                )
            with scenario_controls:
                demo_scenario = st.selectbox(
                    "Fictional report scenario",
                    DEMO_REPORT_SCENARIOS,
                    key="history_demo_scenario",
                )
                demo_rank_mode = st.selectbox(
                    "Demo route ranking",
                    ("Distance only", "Include demo reports"),
                    key="history_demo_rank_mode",
                )
            try:
                demo_route_options = build_routes(
                    DEMO_LOCATIONS[demo_origin],
                    DEMO_LOCATIONS[demo_destination],
                    reports=demo_reports(scenario=demo_scenario),
                    report_penalty_meters=(
                        300 if demo_rank_mode == "Include demo reports" else 0
                    ),
                )
            except ValueError as exc:
                st.info(f"Choose two different demo points: {exc}")
            else:
                if demo_route_options:
                    chosen_demo_route = demo_route_options[0]
                    st.metric(
                        "Top-ranked fictional route",
                        format_distance(chosen_demo_route.distance_meters),
                        delta=(
                            f"{chosen_demo_route.score_meters:,} m-equivalent score"
                        ),
                        delta_color="off",
                    )
                    st.write(
                        "**Demo path:** "
                        + " → ".join(
                            next(node.label for node in DEMO_NODES if node.id == node_id)
                            for node_id in chosen_demo_route.nodes
                        )
                    )
                    st.write(
                        f"**Illustrative walk time:** "
                        f"{format_duration(chosen_demo_route.estimated_minutes)} · "
                        f"**Recent simulated reports:** "
                        f"{len(chosen_demo_route.recent_reports)}"
                    )
                    st.graphviz_chart(
                        _route_diagram(chosen_demo_route),
                        use_container_width=True,
                    )
                else:
                    st.info("No path is available for those demo endpoints.")
        st.info(
            "Use this view to contrast a measured historical sensor event with a "
            "fictional route calculation—not to infer current street conditions or route safety."
        )
    else:
        st.subheader("FEMA National Flood Hazard Layer · Jamaica reference area")
        st.write(
            "This official mapped hazard layer describes flood-zone designations; it is "
            "not NYC DEP's rainfall-scenario map and does not describe present street conditions."
        )
        try:
            with st.spinner("Loading FEMA flood-zone features…"):
                hazards = _cached_fema_hazards()
        except DataSourceError as exc:
            st.error(f"FEMA layer unavailable: {exc}")
            st.info("Use the official FEMA resource directly; the app's demo remains usable.")
        else:
            st.caption(
                f"Layer retrieved: {_format_timestamp(hazards['retrieved_at'])} · "
                f"{hazards['feature_count']} features · FEMA did not supply a layer-wide "
                "publication timestamp in this response."
            )
            _render_fema_map(hazards)
            st.markdown(
                "[FEMA NFHL MapServer](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer)"
            )

    st.divider()
    st.subheader("Flooding mechanisms are not interchangeable")
    for title, explanation in (
        (
            "Pluvial / stormwater",
            "Rainwater accumulates when rainfall exceeds drainage or local surface capacity. "
            "FloodNet events measure water at specific fixed sensors; NYC DEP maps model rainfall scenarios.",
        ),
        (
            "Coastal",
            "High coastal water levels and storm surge can affect low-lying shorelines. "
            "A tide station is not a sidewalk sensor.",
        ),
        (
            "Riverine",
            "Rivers and streams may overtop their banks; the displayed Queens-focused layers "
            "do not provide a complete riverine analysis.",
        ),
        (
            "Sewer backup",
            "Backups involve sewer and building plumbing systems; neither a broad surface map "
            "nor these sensor events diagnose a particular sewer connection.",
        ),
    ):
        with st.expander(title):
            st.write(explanation)
    st.markdown(
        "Official scenario resource: [NYC Stormwater Flood Maps dataset](https://data.cityofnewyork.us/api/views/9i7c-xyvv.json). "
        "Its downloadable file geodatabases are cataloged in About & Data; they are not loaded in this app."
    )


def _reset_checklist() -> None:
    for item in CHECKLIST:
        st.session_state[f"prepared_{item.id}"] = False


def _set_code_inventory_visible(visible: bool) -> None:
    st.session_state["show_code_inventory"] = visible


def _project_code_inventory() -> str:
    project_root = Path(__file__).resolve().parent
    source_files = (
        "app.py",
        "routing.py",
        "flood_data.py",
        "preparedness.py",
        "data_sources.py",
    )
    test_files = (
        "tests/test_routing.py",
        "tests/test_flood_data.py",
        "tests/test_preparedness.py",
    )
    lines = [
        "RAINROUTE NYC :: PROJECT INVENTORY",
        "===================================",
        "Mode: read-only source inventory; this display does not execute tests.",
        "",
        "APPLICATION MODULES",
    ]
    source_line_count = 0
    for relative_path in source_files:
        line_count = len(
            (project_root / relative_path).read_text(encoding="utf-8").splitlines()
        )
        source_line_count += line_count
        lines.append(f"  {relative_path:<28} {line_count:>4} lines")
    lines.extend(("", "TEST MODULES"))
    test_case_count = 0
    test_line_count = 0
    for relative_path in test_files:
        test_path = project_root / relative_path
        contents = test_path.read_text(encoding="utf-8")
        tree = ast.parse(contents, filename=relative_path)
        case_count = sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
        line_count = len(contents.splitlines())
        test_case_count += case_count
        test_line_count += line_count
        lines.append(
            f"  {relative_path:<28} {case_count:>2} test cases · {line_count:>4} lines"
        )
    lines.extend(
        (
            "",
            f"TOTAL: {source_line_count:,} application lines · "
            f"{test_line_count:,} test lines · {test_case_count} test cases",
            "",
            "Run the tests locally with:",
            "  python -m unittest discover -s tests -v",
        )
    )
    return "\n".join(lines)


def _render_preparedness() -> None:
    _page_header(
        "Preparedness",
        "Build a printable checklist without saving personal details or sending household selections to outside services.",
    )
    st.error(
        "Avoid floodwater. Do not walk, swim, or drive through it. Follow current instructions "
        "from emergency authorities; call 911 for immediate emergencies."
    )
    st.caption(
        "Checklist selections stay in this running Streamlit session. They are not written to "
        "a database and may be lost when the session ends."
    )
    preferences, progress = st.columns([1, 1.35], gap="large")
    with preferences:
        st.subheader("Customize")
        include_pets = st.checkbox("Include pet and service-animal planning", value=True)
        include_documents = st.checkbox("Include supplies and document planning", value=True)
        include_travel = st.checkbox("Include travel-disruption planning", value=True)
        st.button("Reset checklist", on_click=_reset_checklist)
    items = select_checklist_items(
        include_pets=include_pets,
        include_documents=include_documents,
        include_travel=include_travel,
    )
    with progress:
        st.subheader("Your checklist")
        for phase in dict.fromkeys(item.phase for item in items):
            st.markdown(f"**{phase}**")
            for item in items:
                if item.phase == phase:
                    st.checkbox(
                        f"{item.title} — {item.guidance}",
                        key=f"prepared_{item.id}",
                    )
        completed = sum(
            bool(st.session_state.get(f"prepared_{item.id}", False))
            for item in items
        )
        st.progress(completed / len(items) if items else 0.0, text=f"{completed} of {len(items)} complete")
        completed_ids = {
            item.id
            for item in items
            if st.session_state.get(f"prepared_{item.id}", False)
        }
        plan = create_checklist_text(completed_ids, items)
        st.download_button(
            "Download checklist",
            data=plan,
            file_name="rainroute-preparedness-checklist.txt",
            mime="text/plain",
            use_container_width=True,
        )
    st.markdown(
        "Official resources: [Ready.gov flood guidance](https://www.ready.gov/floods) · "
        "[NYC Emergency Management flood guidance](https://www.nyc.gov/site/em/ready/flooding.page) · "
        "[NWS alerts](https://www.weather.gov/okx/) · "
        "[NWS flood safety](https://www.weather.gov/safety/flood) · "
        "[NYC 311](https://portal.311.nyc.gov/) · "
        "[Call 911 for immediate emergencies](https://www.nyc.gov/site/em/about/emergency-response.page)"
    )


def _render_about() -> None:
    _page_header(
        "About & Data",
        "What RainRoute NYC uses, what remains a demonstration, and where every external request goes.",
    )
    st.subheader("What the app does—and does not do")
    st.write(
        "RainRoute NYC demonstrates explainable route comparison and neighborhood flood "
        "context for Queens. The route graph and reports are simulated. FloodNet historical "
        "events, FEMA mapped hazard zones, NWS forecasts, and NWS alerts are external official "
        "data products with different meanings and update schedules."
    )
    st.warning(
        "This project cannot tell whether a street is safe or currently flooded. It does not "
        "provide validated walking directions, predict flood depth, or replace official alerts."
    )
    st.subheader("Technical validation & project structure")
    st.write(
        "Inspect a live line-count and test-case inventory. The button does not execute "
        "code; the test command shown below is run locally during development."
    )
    if st.session_state.get("show_code_inventory", False):
        st.button(
            "Hide code breakdown",
            on_click=_set_code_inventory_visible,
            args=(False,),
        )
        st.code(_project_code_inventory(), language="text")
    else:
        st.button(
            "Show code and test breakdown",
            on_click=_set_code_inventory_visible,
            args=(True,),
        )
    st.subheader("Source registry")
    for source in DATA_SOURCES:
        with st.expander(f"{source['name']} · {source['status'].split(':')[0]}"):
            for label, key in (
                ("Responsible organization", "organization"),
                ("Documentation", "documentation"),
                ("API/download endpoint", "endpoint"),
                ("Format and fields", "format_fields"),
                ("Geographic coverage", "coverage"),
                ("Update frequency / timestamp", "update"),
                ("Latest available source timestamp", "latest_timestamp"),
                ("Authentication", "authentication"),
                ("Rate limits, cost, licensing", "cost_limits_license"),
                ("Freshness", "freshness"),
                ("Data type", "kind"),
                ("Integration status", "status"),
                ("Limitations", "limitations"),
            ):
                st.markdown(f"**{label}:** {source[key]}")

    st.subheader("Privacy, infrastructure, and limitations")
    st.markdown(
        """
        - No login, analytics SDK, geolocation permission, public-report submission, database, or paid API is used.
        - External server-side requests are limited to the published NYC FloodNet/Sensor metadata, FEMA NFHL, and NWS endpoints. Requests use fixed Queens reference areas; no entered home address or user location is transmitted.
        - USGS The National Map topographic tiles are loaded by the browser for FloodLens. The tile service may receive the browser's IP address and tile coordinates. Tiles require internet access; USGS attribution and service policies apply. The basemap is geographic context, not a validated pedestrian network.
        - Public data and map services may be unavailable, delayed, or rate-limited. Cached layers are shown with source timestamps; errors are displayed rather than replaced with fabricated live data.
        - Route calculations run locally in Python over a tiny simulated graph. External API parsing and GeoJSON coordinate validation also run locally. Data requests go to the source endpoints listed above.
        - Hosting on Streamlit Community Cloud is optional and is not configured or used here. A host may process connection metadata; do not describe hosted use as anonymous.
        - The app's security review is a project-level review, not a professional penetration test or accessibility certification.
        """
    )
    st.markdown(
        "For methodology, Windows setup, deployment, and known limitations, see [README.md](README.md), "
        "[DATA_SOURCES.md](DATA_SOURCES.md), and [SECURITY_REVIEW.md](SECURITY_REVIEW.md)."
    )


with st.sidebar:
    st.markdown("## RainRoute NYC")
    st.caption("Flood-route learning lab · not navigation")
    st.divider()
    page = st.radio(
        "Main navigation",
        (
            "Start Here",
            "Route Explorer",
            "Flood Reports",
            "FloodLens",
            "Preparedness",
            "About & Data",
        ),
        key="main_navigation",
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(
        "Routes and reports are simulated. Public-data layers appear only when their official services respond."
    )

if page == "Start Here":
    _render_start_here()
elif page == "Route Explorer":
    _render_route_explorer()
elif page == "Flood Reports":
    _render_demo_reports()
elif page == "FloodLens":
    _render_floodlens()
elif page == "Preparedness":
    _render_preparedness()
else:
    _render_about()
