"""Or-opt local search: relocate short chains of stops to cheaper positions."""

from __future__ import annotations

import numpy as np

_EPS = 1e-10


def or_opt(
    tour: list[int],
    distances: np.ndarray,
    max_segment: int = 3,
) -> list[int]:
    """Relocate segments of length 1..max_segment until no move shortens the tour.

    Like 2-opt, only strictly-improving moves are applied, so the result is
    never longer than the input.
    """
    current = list(tour)
    n = len(current)
    if n < 5:
        return current
    improved = True
    while improved:
        improved = False
        move = _best_relocation(current, distances, max_segment)
        if move is not None:
            current = move
            improved = True
    return current


def _best_relocation(
    tour: list[int],
    distances: np.ndarray,
    max_segment: int,
) -> list[int] | None:
    """Apply the first strictly-improving relocation found, or return None."""
    n = len(tour)
    for seg_len in range(1, max_segment + 1):
        if seg_len >= n - 1:
            break
        for i in range(n - seg_len + 1):
            segment = tour[i : i + seg_len]
            prev_node = tour[(i - 1) % n]
            next_node = tour[(i + seg_len) % n]
            remove_delta = (
                distances[prev_node, next_node]
                - distances[prev_node, segment[0]]
                - distances[segment[-1], next_node]
            )
            rest = tour[:i] + tour[i + seg_len :]
            m = len(rest)
            for pos in range(m):
                a = rest[pos]
                b = rest[(pos + 1) % m]
                insert_fwd = distances[a, segment[0]] + distances[segment[-1], b] - distances[a, b]
                if remove_delta + insert_fwd < -_EPS:
                    return rest[: pos + 1] + segment + rest[pos + 1 :]
                insert_rev = distances[a, segment[-1]] + distances[segment[0], b] - distances[a, b]
                if remove_delta + insert_rev < -_EPS:
                    return rest[: pos + 1] + segment[::-1] + rest[pos + 1 :]
    return None
