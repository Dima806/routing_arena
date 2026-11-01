"""Scaling: tour counts and solve time vs the number of stops (the explosion)."""

from __future__ import annotations

import math
from collections.abc import Callable
from functools import partial
from time import perf_counter
from typing import Any

import pandas as pd

# Order-of-magnitude count of atoms in the observable universe, for the
# explosion plot's reference line.
ATOMS_IN_OBSERVABLE_UNIVERSE = 1.0e80


def tour_count(n: int) -> int:
    """Number of distinct undirected tours through n stops: (n-1)! / 2."""
    if n < 3:
        return 1
    return math.factorial(n - 1) // 2


def time_call(func: Callable[[], Any]) -> tuple[Any, float]:
    """Run `func()` and return (result, elapsed_seconds)."""
    start = perf_counter()
    result = func()
    return result, perf_counter() - start


def measure_scaling(
    sizes: list[int],
    make_instance: Callable[[int], Any],
    solve: Callable[[Any], Any],
) -> pd.DataFrame:
    """Time `solve` on an instance of each size; return n, seconds, and tour_count."""
    rows: list[dict[str, Any]] = []
    for n in sizes:
        instance = make_instance(n)
        _, seconds = time_call(partial(solve, instance))
        rows.append({"n": n, "seconds": seconds, "tour_count": tour_count(n)})
    return pd.DataFrame(rows)
