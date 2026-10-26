"""Explainable routing over an explicitly simulated demonstration graph."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable


REPORT_EXPIRY = timedelta(hours=24)
UNVERIFIED_REPORT_PENALTY_METERS = 300
WALKING_SPEED_METERS_PER_SECOND = 1.33
DEMO_REPORT_SCENARIOS = (
    "Balanced sample",
    "Rainy-day sample",
    "Quiet sample",
)


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    x: int
    y: int


@dataclass(frozen=True)
class Edge:
    id: str
    start: str
    end: str
    distance_meters: int
    condition_known: bool = False
    step_free: bool | None = None


@dataclass(frozen=True)
class FloodReport:
    id: str
    edge_id: str
    category: str
    observed_at: datetime
    verified: bool = False
    status: str = "unverified"
    simulated: bool = True


@dataclass(frozen=True)
class Route:
    nodes: tuple[str, ...]
    edge_ids: tuple[str, ...]
    distance_meters: int
    score_meters: int
    estimated_minutes: int
    recent_reports: tuple[FloodReport, ...]
    stale_reports: tuple[FloodReport, ...]
    unknown_segments: int
    accessibility_unknown_segments: int


DEMO_NODES = (
    Node("A", "Jamaica Center · demo", 0, 0),
    Node("B", "South connector · demo", 1, 1),
    Node("C", "East connector · demo", 1, -1),
    Node("D", "Library endpoint · demo", 3, 0),
    Node("E", "Central connector · demo", 2, -1),
)

DEMO_LOCATIONS = {
    "Jamaica Center (demo)": "A",
    "Queens Library endpoint (demo)": "D",
    "South connector (demo)": "B",
    "East connector (demo)": "C",
    "Central connector (demo)": "E",
}

DEMO_EDGES = (
    Edge("AB", "A", "B", 460),
    Edge("BD", "B", "D", 520),
    Edge("AC", "A", "C", 540),
    Edge("CE", "C", "E", 290),
    Edge("ED", "E", "D", 430),
    Edge("BC", "B", "C", 360),
)


def demo_reports(
    now: datetime | None = None,
    *,
    scenario: str = "Balanced sample",
) -> tuple[FloodReport, ...]:
    observed_now = now or datetime.now(timezone.utc)
    if observed_now.tzinfo is None:
        raise ValueError("The report clock must include a timezone.")
    scenarios = {
        "Balanced sample": (
            ("DEMO-01", "BD", "Street pooling", timedelta(minutes=45)),
            ("DEMO-02", "AB", "Standing water near crossing", timedelta(hours=2)),
            ("DEMO-03", "CE", "Drain inlet concern", timedelta(hours=5)),
            ("DEMO-04", "CE", "Uncertain sidewalk observation", timedelta(hours=30)),
        ),
        "Rainy-day sample": (
            ("DEMO-11", "BD", "Street pooling", timedelta(minutes=8)),
            ("DEMO-12", "AB", "Standing water near crossing", timedelta(minutes=16)),
            ("DEMO-13", "AC", "Drain inlet concern", timedelta(minutes=35)),
            ("DEMO-14", "BC", "Uncertain sidewalk observation", timedelta(minutes=54)),
            ("DEMO-15", "CE", "Street pooling", timedelta(minutes=80)),
            ("DEMO-16", "ED", "Standing water near crossing", timedelta(minutes=130)),
            ("DEMO-17", "CE", "Drain inlet concern", timedelta(hours=29)),
        ),
        "Quiet sample": (
            ("DEMO-21", "BD", "Street pooling", timedelta(hours=31)),
            ("DEMO-22", "AB", "Drain inlet concern", timedelta(hours=52)),
        ),
    }
    if scenario not in scenarios:
        raise ValueError(f"Unknown demonstration report scenario: {scenario}")
    return tuple(
        FloodReport(
            id=report_id,
            edge_id=edge_id,
            category=category,
            observed_at=observed_now - age,
            status="stale" if age > REPORT_EXPIRY else "unverified",
        )
        for report_id, edge_id, category, age in scenarios[scenario]
    )


def _edge_map(edges: Iterable[Edge]) -> dict[frozenset[str], Edge]:
    result: dict[frozenset[str], Edge] = {}
    for edge in edges:
        if (
            not edge.id
            or edge.start == edge.end
            or edge.distance_meters <= 0
            or frozenset((edge.start, edge.end)) in result
        ):
            raise ValueError("The routing graph contains an invalid or duplicate edge.")
        result[frozenset((edge.start, edge.end))] = edge
    return result


def _shortest_path(
    start: str,
    destination: str,
    edges: tuple[Edge, ...],
    *,
    edge_costs: dict[str, int],
    banned_nodes: frozenset[str] = frozenset(),
    banned_edges: frozenset[str] = frozenset(),
) -> tuple[str, ...] | None:
    adjacency: dict[str, list[tuple[str, Edge]]] = {}
    for edge in edges:
        if edge.id in banned_edges:
            continue
        if edge.start in banned_nodes or edge.end in banned_nodes:
            continue
        adjacency.setdefault(edge.start, []).append((edge.end, edge))
        adjacency.setdefault(edge.end, []).append((edge.start, edge))

    pending: list[tuple[int, tuple[str, ...], str]] = [(0, (start,), start)]
    best: dict[str, tuple[int, tuple[str, ...]]] = {}
    while pending:
        distance, path, node = heapq.heappop(pending)
        if node in best:
            continue
        best[node] = (distance, path)
        if node == destination:
            return path
        for neighbor, edge in sorted(adjacency.get(node, ()), key=lambda item: item[0]):
            if neighbor not in best:
                heapq.heappush(
                    pending,
                    (distance + edge_costs[edge.id], path + (neighbor,), neighbor),
                )
    return None


def _path_edges(path: tuple[str, ...], edge_map: dict[frozenset[str], Edge]) -> tuple[Edge, ...]:
    return tuple(
        edge_map[frozenset((start, end))]
        for start, end in zip(path, path[1:])
    )


def _k_shortest_paths(
    start: str,
    destination: str,
    edges: tuple[Edge, ...],
    limit: int,
    edge_costs: dict[str, int],
) -> list[tuple[str, ...]]:
    first = _shortest_path(start, destination, edges, edge_costs=edge_costs)
    if first is None:
        return []

    edge_map = _edge_map(edges)
    accepted = [first]
    candidates: list[tuple[int, tuple[str, ...]]] = []
    seen = {first}

    while len(accepted) < limit:
        previous = accepted[-1]
        for spur_index in range(len(previous) - 1):
            root = previous[: spur_index + 1]
            banned_edges: set[str] = set()
            for path in accepted:
                if len(path) > spur_index and path[: spur_index + 1] == root:
                    banned_edges.add(
                        edge_map[frozenset((path[spur_index], path[spur_index + 1]))].id
                    )
            spur = _shortest_path(
                root[-1],
                destination,
                edges,
                edge_costs=edge_costs,
                banned_nodes=frozenset(root[:-1]),
                banned_edges=frozenset(banned_edges),
            )
            if spur is None:
                continue
            candidate = root[:-1] + spur
            if candidate in seen:
                continue
            seen.add(candidate)
            score = sum(edge_costs[edge.id] for edge in _path_edges(candidate, edge_map))
            heapq.heappush(candidates, (score, candidate))

        if not candidates:
            break
        accepted.append(heapq.heappop(candidates)[1])
    return accepted


def _report_age(report: FloodReport, now: datetime) -> timedelta:
    if report.observed_at.tzinfo is None:
        raise ValueError("Report timestamps must include a timezone.")
    age = now - report.observed_at
    if age < timedelta(0):
        return timedelta.max
    return age


def build_routes(
    start: str,
    destination: str,
    *,
    edges: tuple[Edge, ...] = DEMO_EDGES,
    reports: tuple[FloodReport, ...] | None = None,
    limit: int = 3,
    report_penalty_meters: int = UNVERIFIED_REPORT_PENALTY_METERS,
    now: datetime | None = None,
) -> tuple[Route, ...]:
    if not start or not destination:
        raise ValueError("Choose both an origin and a destination.")
    if start == destination:
        raise ValueError("Choose different origin and destination locations.")
    if limit < 1 or limit > 5:
        raise ValueError("Route alternatives must be between one and five.")
    if report_penalty_meters < 0:
        raise ValueError("The report penalty cannot be negative.")
    graph_nodes = {node for edge in edges for node in (edge.start, edge.end)}
    if start not in graph_nodes or destination not in graph_nodes:
        raise ValueError("The selected location is not in the available demo network.")

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        raise ValueError("The route clock must include a timezone.")
    report_rows = reports if reports is not None else demo_reports(current_time)
    edge_map = _edge_map(edges)
    active_report_counts: dict[str, int] = {}
    for report in report_rows:
        if (
            not report.verified
            and _report_age(report, current_time) <= REPORT_EXPIRY
        ):
            active_report_counts[report.edge_id] = (
                active_report_counts.get(report.edge_id, 0) + 1
            )
    edge_costs = {
        edge.id: edge.distance_meters
        + active_report_counts.get(edge.id, 0) * report_penalty_meters
        for edge in edges
    }
    routes: list[Route] = []
    for path in _k_shortest_paths(start, destination, edges, limit, edge_costs):
        path_edges = _path_edges(path, edge_map)
        path_edge_ids = {edge.id for edge in path_edges}
        associated = tuple(report for report in report_rows if report.edge_id in path_edge_ids)
        stale = tuple(
            report
            for report in associated
            if _report_age(report, current_time) > REPORT_EXPIRY
        )
        recent = tuple(
            report
            for report in associated
            if not report.verified and report not in stale
        )
        distance = sum(edge.distance_meters for edge in path_edges)
        score = distance + len(recent) * report_penalty_meters
        routes.append(
            Route(
                nodes=path,
                edge_ids=tuple(edge.id for edge in path_edges),
                distance_meters=distance,
                score_meters=score,
                estimated_minutes=round(distance / WALKING_SPEED_METERS_PER_SECOND / 60),
                recent_reports=recent,
                stale_reports=stale,
                unknown_segments=sum(not edge.condition_known for edge in path_edges),
                accessibility_unknown_segments=sum(edge.step_free is None for edge in path_edges),
            )
        )
    return tuple(sorted(routes, key=lambda route: (route.score_meters, route.distance_meters, route.nodes)))


def format_distance(distance_meters: int) -> str:
    return f"{distance_meters / 1609.344:.2f} mi"


def format_duration(minutes: int) -> str:
    return f"About {minutes} min at {WALKING_SPEED_METERS_PER_SECOND:.2f} m/s"
