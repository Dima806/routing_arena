"""Stronger constructions: Clarke-Wright savings and cheapest insertion.

These start closer to optimal than nearest-neighbor and make better seeds for
local search. (Named for the family of smarter constructions; this is not the
Christofides 3/2-approximation, which needs a matching routine.)
"""

from __future__ import annotations

import numpy as np


def cheapest_insertion_tour(distances: np.ndarray, start: int = 0) -> list[int]:
    """Grow a tour by always inserting the stop with the cheapest insertion cost."""
    n = int(distances.shape[0])
    if n <= 2:
        return list(range(n))
    row = distances[start].copy()
    row[start] = np.inf
    second = int(np.argmin(row))
    tour = [start, second]
    in_tour = {start, second}
    while len(tour) < n:
        best_city = -1
        best_pos = 1
        best_cost = np.inf
        for k in range(n):
            if k in in_tour:
                continue
            for pos in range(len(tour)):
                i = tour[pos]
                j = tour[(pos + 1) % len(tour)]
                cost = distances[i, k] + distances[k, j] - distances[i, j]
                if cost < best_cost:
                    best_cost = cost
                    best_city = k
                    best_pos = pos + 1
        tour.insert(best_pos, best_city)
        in_tour.add(best_city)
    return tour


def savings_tour(distances: np.ndarray, depot: int = 0) -> list[int]:
    """Clarke-Wright savings: merge out-and-back legs by descending savings."""
    n = int(distances.shape[0])
    if n <= 2:
        return list(range(n))
    routes: dict[int, list[int]] = {i: [i] for i in range(n) if i != depot}
    route_of: dict[int, int] = {i: i for i in range(n) if i != depot}

    savings: list[tuple[float, int, int]] = []
    for i in range(n):
        if i == depot:
            continue
        for j in range(i + 1, n):
            if j == depot:
                continue
            value = float(distances[depot, i] + distances[depot, j] - distances[i, j])
            savings.append((value, i, j))
    savings.sort(reverse=True)

    for _, i, j in savings:
        ri = route_of[i]
        rj = route_of[j]
        if ri == rj:
            continue
        route_i = routes[ri]
        route_j = routes[rj]
        if i not in (route_i[0], route_i[-1]) or j not in (route_j[0], route_j[-1]):
            continue
        if route_i[-1] != i:
            route_i = route_i[::-1]
        if route_j[0] != j:
            route_j = route_j[::-1]
        merged = route_i + route_j
        routes[ri] = merged
        del routes[rj]
        for city in merged:
            route_of[city] = ri

    tour = [depot]
    for route in routes.values():
        tour.extend(route)
    return tour
