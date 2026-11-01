"""Brute-force TSP: enumerate every tour. The ground truth for tiny instances."""

from __future__ import annotations

from itertools import permutations

import numpy as np

from src.problems.tsp import tour_length


def brute_force_tsp(distances: np.ndarray, max_n: int = 11) -> tuple[list[int], float]:
    """Return the provably shortest tour by enumerating all (n-1)! orderings.

    City 0 is fixed as the start, so only the remaining stops are permuted.
    Refuses instances larger than `max_n`, which would never finish.
    """
    n = int(distances.shape[0])
    if n > max_n:
        raise ValueError(f"brute force refuses n={n} > max_n={max_n}; it would never finish")
    if n <= 1:
        return list(range(n)), 0.0
    best_tour = list(range(n))
    best_length = tour_length(best_tour, distances)
    for perm in permutations(range(1, n)):
        tour = [0, *perm]
        length = tour_length(tour, distances)
        if length < best_length:
            best_length = length
            best_tour = tour
    return best_tour, best_length
