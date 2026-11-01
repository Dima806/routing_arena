"""2-opt must never lengthen a tour and must improve a nearest-neighbor start."""

from __future__ import annotations

import pytest

from src.heuristics.nearest_neighbor import nearest_neighbor_tour
from src.heuristics.or_opt import or_opt
from src.heuristics.two_opt import two_opt, two_opt_steps
from src.problems.tsp import generate_tsp_instance, is_valid_tour, tour_length


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_two_opt_never_lengthens(seed: int) -> None:
    instance = generate_tsp_instance(25, seed=seed)
    nn_tour = nearest_neighbor_tour(instance.distances)
    nn_length = tour_length(nn_tour, instance.distances)

    improved = two_opt(nn_tour, instance.distances)
    improved_length = tour_length(improved, instance.distances)

    assert is_valid_tour(improved, instance.n)
    assert improved_length <= nn_length + 1e-9


def test_two_opt_strictly_improves_a_clumsy_tour() -> None:
    instance = generate_tsp_instance(30, seed=7)
    nn_tour = nearest_neighbor_tour(instance.distances)
    improved = two_opt(nn_tour, instance.distances)
    assert tour_length(improved, instance.distances) < tour_length(nn_tour, instance.distances)


def test_two_opt_steps_are_monotone() -> None:
    instance = generate_tsp_instance(20, seed=3)
    nn_tour = nearest_neighbor_tour(instance.distances)
    lengths = [
        tour_length(step, instance.distances)
        for step in two_opt_steps(nn_tour, instance.distances)
    ]
    for earlier, later in zip(lengths, lengths[1:], strict=False):
        assert later <= earlier + 1e-9


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_or_opt_never_lengthens(seed: int) -> None:
    instance = generate_tsp_instance(25, seed=seed)
    nn_tour = nearest_neighbor_tour(instance.distances)
    nn_length = tour_length(nn_tour, instance.distances)

    improved = or_opt(nn_tour, instance.distances)
    assert is_valid_tour(improved, instance.n)
    assert tour_length(improved, instance.distances) <= nn_length + 1e-9
