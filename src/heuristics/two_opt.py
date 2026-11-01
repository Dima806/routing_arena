"""2-opt local search: uncross wasteful edge pairs by reversing segments."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

_EPS = 1e-10


def two_opt(
    tour: list[int],
    distances: np.ndarray,
    max_passes: int | None = None,
) -> list[int]:
    """Improve a tour until no 2-opt swap shortens it.

    Each applied move strictly reduces the tour length, so the result is never
    longer than the input (monotone improvement).
    """
    result = list(tour)
    n = len(result)
    if n < 4:
        return result
    improved = True
    passes = 0
    while improved and (max_passes is None or passes < max_passes):
        improved = False
        passes += 1
        for i in range(1, n - 1):
            for k in range(i + 1, n):
                a = result[i - 1]
                b = result[i]
                c = result[k]
                d = result[(k + 1) % n]
                delta = distances[a, c] + distances[b, d] - distances[a, b] - distances[c, d]
                if delta < -_EPS:
                    result[i : k + 1] = result[i : k + 1][::-1]
                    improved = True
    return result


def two_opt_steps(tour: list[int], distances: np.ndarray) -> Iterator[list[int]]:
    """Yield the tour after each improving swap, for the 2-opt animator."""
    result = list(tour)
    n = len(result)
    yield list(result)
    if n < 4:
        return
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for k in range(i + 1, n):
                a = result[i - 1]
                b = result[i]
                c = result[k]
                d = result[(k + 1) % n]
                delta = distances[a, c] + distances[b, d] - distances[a, b] - distances[c, d]
                if delta < -_EPS:
                    result[i : k + 1] = result[i : k + 1][::-1]
                    improved = True
                    yield list(result)
