"""OR-Tools must return a valid tour within a small gap of the exact optimum."""

from __future__ import annotations

import pytest

from src.evaluation.gap_to_optimal import gap_percent
from src.exact.brute_force import brute_force_tsp
from src.ortools_solver.routing import solve_tsp
from src.problems.tsp import generate_tsp_instance, is_valid_tour


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_ortools_tsp_near_optimal(seed: int) -> None:
    instance = generate_tsp_instance(9, seed=seed)
    _, optimum = brute_force_tsp(instance.distances)
    tour, length = solve_tsp(instance.distances, time_limit=2.0)

    assert is_valid_tour(tour, instance.n)
    assert length >= optimum - 1e-6
    assert gap_percent(length, optimum) <= 5.0
