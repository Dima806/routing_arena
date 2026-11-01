"""OR-Tools routing: TSP and VRP solved with guided local search.

A small, tested wrapper so notebooks and the app make clean calls instead of
touching the intricate OR-Tools API directly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from src.problems.tsp import tour_length
from src.problems.vrp import VRPInstance

_SCALE = 1000


@dataclass(frozen=True)
class VRPSolution:
    """Result of a VRP solve: one route per vehicle (depot at both ends)."""

    routes: list[list[int]]
    total_distance: float
    num_vehicles_used: int


def solve_tsp(distances: np.ndarray, time_limit: float = 5.0) -> tuple[list[int], float]:
    """Solve a single-vehicle TSP with PATH_CHEAPEST_ARC + guided local search."""
    n = int(distances.shape[0])
    if n <= 1:
        return list(range(n)), 0.0
    matrix = _int_matrix(distances)
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        return matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    solution = routing.SolveWithParameters(_search_params(time_limit))
    if solution is None:
        raise RuntimeError("OR-Tools found no TSP solution within the time limit")
    # _extract_route closes the loop with a trailing return to the depot;
    # a TSP tour is the open visiting order, so drop that last node.
    route = _extract_route(routing, manager, solution, vehicle=0)
    tour = route[:-1]
    return tour, tour_length(tour, distances)


def solve_vrp(
    instance: VRPInstance,
    time_limit: float = 5.0,
    use_time_windows: bool = False,
) -> VRPSolution:
    """Solve a capacitated VRP (optionally with time windows) via guided local search."""
    n = int(instance.distances.shape[0])
    matrix = _int_matrix(instance.distances)
    manager = pywrapcp.RoutingIndexManager(n, instance.num_vehicles, instance.depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        return matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    demands = [int(d) for d in instance.demands]

    def demand_callback(from_index: int) -> int:
        return demands[manager.IndexToNode(from_index)]

    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx,
        0,
        [instance.vehicle_capacity] * instance.num_vehicles,
        True,
        "Capacity",
    )

    if use_time_windows and instance.time_windows is not None:
        _add_time_windows(
            routing,
            manager,
            n,
            instance.depot,
            instance.time_windows,
            instance.distances,
            instance.service_time,
        )

    solution = routing.SolveWithParameters(_search_params(time_limit))
    if solution is None:
        raise RuntimeError("OR-Tools found no VRP solution within the time limit")
    routes = [
        _extract_route(routing, manager, solution, vehicle=v) for v in range(instance.num_vehicles)
    ]
    total = _routes_distance(routes, instance.distances)
    used = sum(1 for route in routes if len(route) > 2)
    return VRPSolution(routes=routes, total_distance=total, num_vehicles_used=used)


def _int_matrix(distances: np.ndarray, scale: int = _SCALE) -> list[list[int]]:
    """Integer distance matrix; OR-Tools arc costs must be integers."""
    scaled: np.ndarray = np.rint(distances * scale).astype(np.int64)
    return scaled.tolist()


def _search_params(time_limit: float):
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.FromMilliseconds(max(100, int(time_limit * 1000)))
    return params


def _extract_route(routing, manager, solution, vehicle: int) -> list[int]:
    index = routing.Start(vehicle)
    route = [int(manager.IndexToNode(index))]
    while not routing.IsEnd(index):
        index = solution.Value(routing.NextVar(index))
        route.append(int(manager.IndexToNode(index)))
    return route


def _routes_distance(routes: list[list[int]], distances: np.ndarray) -> float:
    total = 0.0
    for route in routes:
        for i in range(len(route) - 1):
            total += float(distances[route[i], route[i + 1]])
    return total


def _add_time_windows(
    routing,
    manager,
    num_nodes: int,
    depot: int,
    time_windows: np.ndarray,
    distances: np.ndarray,
    service_time: int,
) -> None:
    # Travel time is the raw (unscaled) distance plus service time, so it shares
    # units with the time windows, which are expressed in coordinate space.
    time_matrix = np.rint(distances).astype(np.int64).tolist()

    def time_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return time_matrix[from_node][to_node] + service_time

    time_idx = routing.RegisterTransitCallback(time_callback)
    horizon = int(time_windows[:, 1].max()) + 1
    routing.AddDimension(time_idx, horizon, horizon, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for node in range(num_nodes):
        if node == depot:
            continue
        cumul = time_dim.CumulVar(manager.NodeToIndex(node))
        cumul.SetRange(int(time_windows[node, 0]), int(time_windows[node, 1]))
