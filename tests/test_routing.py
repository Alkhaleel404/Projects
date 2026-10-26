import unittest
from datetime import datetime, timedelta, timezone

from routing import (
    DEMO_EDGES,
    DEMO_LOCATIONS,
    DEMO_REPORT_SCENARIOS,
    Edge,
    FloodReport,
    build_routes,
    demo_reports,
)


class RoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)

    def test_computes_distinct_alternatives_and_scores_reports(self) -> None:
        routes = build_routes(
            "A",
            "D",
            reports=(
                FloodReport(
                    "R1",
                    "BD",
                    "Pooling",
                    self.now - timedelta(minutes=30),
                ),
            ),
            now=self.now,
        )

        self.assertEqual(len(routes), 3)
        self.assertNotEqual(routes[0].edge_ids, routes[1].edge_ids)
        self.assertEqual(routes[0].score_meters, routes[0].distance_meters)
        self.assertEqual(routes[1].score_meters, routes[1].distance_meters + 300)
        self.assertIn("BD", routes[1].edge_ids)

    def test_stale_report_does_not_change_score(self) -> None:
        route = build_routes(
            "A",
            "D",
            reports=(
                FloodReport(
                    "OLD",
                    "BD",
                    "Pooling",
                    self.now - timedelta(hours=25),
                    status="stale",
                ),
            ),
            now=self.now,
        )[0]

        self.assertEqual(route.score_meters, route.distance_meters)
        self.assertEqual(len(route.stale_reports), 1)
        self.assertEqual(route.recent_reports, ())

    def test_unknown_conditions_are_reported_not_scored_as_safe(self) -> None:
        routes = build_routes("A", "D", reports=(), now=self.now)

        self.assertTrue(all(route.unknown_segments == len(route.edge_ids) for route in routes))

    def test_disconnected_graph_has_no_route(self) -> None:
        routes = build_routes(
            "A",
            "D",
            edges=(Edge("AB", "A", "B", 10), Edge("CD", "C", "D", 10)),
            reports=(),
            now=self.now,
        )

        self.assertEqual(routes, ())

    def test_rejects_same_or_unknown_locations(self) -> None:
        with self.assertRaises(ValueError):
            build_routes("A", "A", now=self.now)
        with self.assertRaises(ValueError):
            build_routes("outside", "A", now=self.now)

    def test_invalid_graph_and_route_limit_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_routes(
                "A",
                "B",
                edges=(Edge("loop", "A", "A", 10),),
                now=self.now,
            )
        with self.assertRaises(ValueError):
            build_routes("A", "D", limit=6, now=self.now)

    def test_location_catalog_uses_only_demo_nodes(self) -> None:
        graph_node_ids = {node for edge in DEMO_EDGES for node in (edge.start, edge.end)}
        self.assertTrue(set(DEMO_LOCATIONS.values()).issubset(graph_node_ids))
        self.assertGreaterEqual(len(DEMO_LOCATIONS), 5)

    def test_demo_report_scenarios_vary_report_count_and_freshness(self) -> None:
        balanced = demo_reports(self.now, scenario="Balanced sample")
        rainy = demo_reports(self.now, scenario="Rainy-day sample")
        quiet = demo_reports(self.now, scenario="Quiet sample")

        self.assertEqual(len(balanced), 4)
        self.assertEqual(len(rainy), 7)
        self.assertEqual(len(quiet), 2)
        self.assertEqual(
            set(DEMO_REPORT_SCENARIOS),
            {"Balanced sample", "Rainy-day sample", "Quiet sample"},
        )
        self.assertTrue(any(report.status == "stale" for report in rainy))
        self.assertTrue(all(report.simulated for report in balanced + rainy + quiet))
        with self.assertRaises(ValueError):
            demo_reports(self.now, scenario="Unknown")

    def test_balanced_and_rainy_scenarios_can_change_the_top_ranked_path(self) -> None:
        balanced = build_routes(
            "A",
            "D",
            reports=demo_reports(self.now, scenario="Balanced sample"),
            report_penalty_meters=300,
            now=self.now,
        )
        rainy = build_routes(
            "A",
            "D",
            reports=demo_reports(self.now, scenario="Rainy-day sample"),
            report_penalty_meters=300,
            now=self.now,
        )

        self.assertEqual(balanced[0].nodes, ("A", "C", "E", "D"))
        self.assertEqual(rainy[0].nodes, ("A", "B", "D"))

    def test_report_penalty_is_configurable(self) -> None:
        report = FloodReport(
            "R1",
            "BD",
            "Pooling",
            self.now - timedelta(minutes=10),
        )
        no_penalty = build_routes(
            "A", "D", reports=(report,), report_penalty_meters=0, now=self.now
        )
        larger_penalty = build_routes(
            "A", "D", reports=(report,), report_penalty_meters=900, now=self.now
        )

        self.assertEqual(no_penalty[0].score_meters, no_penalty[0].distance_meters)
        affected_route = next(route for route in larger_penalty if "BD" in route.edge_ids)
        self.assertEqual(affected_route.score_meters, affected_route.distance_meters + 900)
        with self.assertRaises(ValueError):
            build_routes("A", "D", report_penalty_meters=-1, now=self.now)

    def test_equal_cost_routes_have_stable_tie_breaking(self) -> None:
        edges = (
            Edge("AB", "A", "B", 10),
            Edge("BD", "B", "D", 10),
            Edge("AC", "A", "C", 10),
            Edge("CD", "C", "D", 10),
        )
        routes = build_routes("A", "D", edges=edges, reports=(), now=self.now, limit=2)

        self.assertEqual(routes[0].nodes, ("A", "B", "D"))
        self.assertEqual(routes[1].nodes, ("A", "C", "D"))

    def test_report_only_affects_the_graph_segment_it_names(self) -> None:
        routes = build_routes(
            "A",
            "D",
            reports=(
                FloodReport(
                    "OTHER",
                    "AB",
                    "Pooling",
                    self.now - timedelta(minutes=2),
                ),
            ),
            now=self.now,
        )

        self.assertEqual(routes[0].recent_reports, ())
        self.assertEqual(routes[1].recent_reports[0].id, "OTHER")
        self.assertEqual(routes[2].recent_reports, ())

    def test_alternatives_are_ranked_using_evidence_adjusted_cost(self) -> None:
        edges = (
            Edge("AB", "A", "B", 100),
            Edge("BD", "B", "D", 100),
            Edge("AC", "A", "C", 220),
            Edge("CD", "C", "D", 220),
        )
        reports = (
            FloodReport(
                "R1",
                "AB",
                "Pooling",
                self.now - timedelta(minutes=10),
            ),
        )

        routes = build_routes(
            "A",
            "D",
            edges=edges,
            reports=reports,
            now=self.now,
            limit=2,
        )

        self.assertEqual(routes[0].nodes, ("A", "C", "D"))
        self.assertEqual(routes[0].score_meters, 440)
        self.assertEqual(routes[1].nodes, ("A", "B", "D"))
        self.assertEqual(routes[1].score_meters, 500)


if __name__ == "__main__":
    unittest.main()
