"""Exact TSP as a MILP with Miller-Tucker-Zemlin subtour elimination."""

from __future__ import annotations

import numpy as np
import pulp

from src.problems.tsp import tour_length


def milp_tsp(
    distances: np.ndarray,
    time_limit: float | None = None,
    backend: str = "cbc",
) -> tuple[list[int], float]:
    """Solve the TSP to proven optimality as a mixed-integer program.

    Uses the MTZ subtour-elimination formulation. `backend` is 'cbc' (the open
    solver bundled with PuLP, the default) or 'highs' (the HiGHS command-line
    binary, if installed). `time_limit` caps the solve in seconds so a notebook
    never hangs.

    HiGHS is driven out-of-process via its CLI rather than the `highspy` Python
    bindings: `highspy` and `ortools` each bundle an incompatible copy of HiGHS
    and cannot be imported into the same process.
    """
    n = int(distances.shape[0])
    if n < 2:
        return list(range(n)), 0.0

    problem = pulp.LpProblem("tsp", pulp.LpMinimize)
    x = {
        (i, j): pulp.LpVariable(f"x_{i}_{j}", cat="Binary")
        for i in range(n)
        for j in range(n)
        if i != j
    }
    u = {
        i: pulp.LpVariable(f"u_{i}", lowBound=0, upBound=n - 1, cat="Continuous")
        for i in range(1, n)
    }

    problem += pulp.lpSum(float(distances[i, j]) * x[(i, j)] for (i, j) in x)
    for j in range(n):
        problem += pulp.lpSum(x[(i, j)] for i in range(n) if i != j) == 1
    for i in range(n):
        problem += pulp.lpSum(x[(i, j)] for j in range(n) if i != j) == 1
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                problem += u[i] - u[j] + n * x[(i, j)] <= n - 1

    problem.solve(_build_solver(backend, time_limit))
    tour = _extract_tour(x, n)
    return tour, tour_length(tour, distances)


def _build_solver(backend: str, time_limit: float | None):
    kwargs: dict[str, object] = {"msg": False}
    if time_limit is not None:
        kwargs["timeLimit"] = time_limit
    if backend == "cbc":
        return pulp.PULP_CBC_CMD(**kwargs)
    if backend == "highs":
        return pulp.HiGHS_CMD(**kwargs)
    raise ValueError(f"unknown backend: {backend!r} (use 'cbc' or 'highs')")


def _extract_tour(x: dict[tuple[int, int], pulp.LpVariable], n: int) -> list[int]:
    successor: dict[int, int] = {}
    for (i, j), var in x.items():
        value = var.value()
        if value is not None and value > 0.5:
            successor[i] = j
    tour = [0]
    current = 0
    for _ in range(n - 1):
        current = successor[current]
        tour.append(current)
    return tour
