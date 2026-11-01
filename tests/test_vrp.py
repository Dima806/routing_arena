"""The VRP solution must respect capacities and visit every stop exactly once."""

from __future__ import annotations

import pytest

from src.ortools_solver.routing import solve_vrp
from src.problems.vrp import generate_vrp_instance


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_vrp_is_feasible(seed: int) -> None:
    customers = 12
    vehicles = 4
    capacity = 50
    instance = generate_vrp_instance(customers, vehicles, capacity, seed=seed)

    solution = solve_vrp(instance, time_limit=3.0)

    # Every customer is visited exactly once; the depot opens and closes each route.
    visited = [node for route in solution.routes for node in route if node != instance.depot]
    assert sorted(visited) == list(range(1, customers + 1))
    for route in solution.routes:
        assert route[0] == instance.depot
        assert route[-1] == instance.depot

    # No route exceeds the vehicle capacity.
    for route in solution.routes:
        load = sum(int(instance.demands[node]) for node in route)
        assert load <= capacity

    assert solution.num_vehicles_used <= vehicles


def test_vrp_total_distance_matches_routes() -> None:
    instance = generate_vrp_instance(10, 3, 60, seed=0)
    solution = solve_vrp(instance, time_limit=2.0)

    recomputed = 0.0
    for route in solution.routes:
        for i in range(len(route) - 1):
            recomputed += float(instance.distances[route[i], route[i + 1]])
    assert solution.total_distance == pytest.approx(recomputed, rel=1e-9)
