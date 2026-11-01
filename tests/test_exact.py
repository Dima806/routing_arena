"""The MILP TSP must match the brute-force optimum on small instances."""

from __future__ import annotations

import pytest

from src.exact.brute_force import brute_force_tsp
from src.exact.milp_tsp import milp_tsp
from src.problems.tsp import generate_tsp_instance, is_valid_tour, tour_length


@pytest.mark.parametrize("n", [5, 6, 7, 8])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_milp_matches_brute_force(n: int, seed: int) -> None:
    instance = generate_tsp_instance(n, seed=seed)
    _, brute_length = brute_force_tsp(instance.distances)
    milp_tour, milp_length = milp_tsp(instance.distances, time_limit=10.0)

    assert is_valid_tour(milp_tour, n)
    assert milp_length == pytest.approx(brute_length, rel=1e-6)
    assert tour_length(milp_tour, instance.distances) == pytest.approx(milp_length, rel=1e-9)


def test_brute_force_refuses_large_instances() -> None:
    instance = generate_tsp_instance(15, seed=0)
    with pytest.raises(ValueError, match="brute force refuses"):
        brute_force_tsp(instance.distances, max_n=11)
