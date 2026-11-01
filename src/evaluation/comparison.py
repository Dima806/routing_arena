"""Arena harness: run several methods on one instance and score them."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

import numpy as np
import pandas as pd

from src.evaluation.gap_to_optimal import gap_percent
from src.evaluation.scaling import time_call
from src.heuristics.christofides_like import cheapest_insertion_tour, savings_tour
from src.heuristics.nearest_neighbor import nearest_neighbor_tour
from src.heuristics.two_opt import two_opt
from src.problems.tsp import tour_length

TourSolver = Callable[[np.ndarray], list[int]]


@dataclass(frozen=True)
class MethodResult:
    """One method's outcome on an instance."""

    method: str
    length: float
    seconds: float
    gap_percent: float | None
    tour: list[int]


def run_arena(
    distances: np.ndarray,
    methods: dict[str, TourSolver],
    reference: float | None = None,
) -> pd.DataFrame:
    """Run each named method on `distances`, scoring length, time, and gap.

    `reference` is the optimum (exact, small n) or a best-known length; when
    given, each method's gap-to-optimal is reported in percent.
    """
    results: list[MethodResult] = []
    for name, method in methods.items():
        tour, seconds = time_call(partial(method, distances))
        length = tour_length(tour, distances)
        gap = gap_percent(length, reference) if reference is not None else None
        results.append(MethodResult(name, length, seconds, gap, tour))
    frame = pd.DataFrame(
        {
            "method": [r.method for r in results],
            "length": [r.length for r in results],
            "seconds": [r.seconds for r in results],
            "gap_percent": [r.gap_percent for r in results],
        }
    )
    return frame.sort_values("length").reset_index(drop=True)


def default_tsp_methods(time_limit: float = 2.0) -> dict[str, TourSolver]:
    """The standard arena line-up of from-scratch and solver methods."""
    from src.ortools_solver.routing import solve_tsp

    return {
        "nearest_neighbor": nearest_neighbor_tour,
        "savings": savings_tour,
        "cheapest_insertion": cheapest_insertion_tour,
        "nn+2opt": lambda d: two_opt(nearest_neighbor_tour(d), d),
        "or_tools": lambda d: solve_tsp(d, time_limit=time_limit)[0],
    }
