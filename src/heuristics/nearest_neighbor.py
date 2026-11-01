"""Nearest-neighbor construction: always drive to the closest unvisited stop."""

from __future__ import annotations

import numpy as np


def nearest_neighbor_tour(distances: np.ndarray, start: int = 0) -> list[int]:
    """Greedy construction. Instant and complete, typically ~20-25% above optimal."""
    n = int(distances.shape[0])
    visited = np.zeros(n, dtype=bool)
    tour = [start]
    visited[start] = True
    current = start
    for _ in range(n - 1):
        masked = np.where(visited, np.inf, distances[current])
        nxt = int(np.argmin(masked))
        tour.append(nxt)
        visited[nxt] = True
        current = nxt
    return tour
