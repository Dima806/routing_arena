"""Vehicle-routing instances: depot, demands, capacities, optional time windows."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.problems.tsp import euclidean_distance_matrix


@dataclass(frozen=True)
class VRPInstance:
    """A capacitated VRP instance with an optional set of delivery time windows."""

    coords: np.ndarray  # (n, 2); index `depot` is the depot
    distances: np.ndarray  # (n, n)
    demands: np.ndarray  # (n,); demand at the depot is 0
    vehicle_capacity: int
    num_vehicles: int
    depot: int = 0
    time_windows: np.ndarray | None = None  # (n, 2) [earliest, latest], or None
    service_time: int = 0
    name: str = "vrp"

    @property
    def num_customers(self) -> int:
        """Number of stops that are not the depot."""
        return int(self.coords.shape[0]) - 1

    @property
    def total_demand(self) -> int:
        """Sum of all customer demands."""
        return int(self.demands.sum())


def generate_vrp_instance(
    num_customers: int,
    num_vehicles: int,
    vehicle_capacity: int,
    seed: int = 0,
    coordinate_range: float = 100.0,
    demand_low: int = 1,
    demand_high: int = 10,
    with_time_windows: bool = False,
) -> VRPInstance:
    """Generate a seeded VRP instance with a central-ish depot and random demands."""
    rng = np.random.default_rng(seed)
    n = num_customers + 1
    coords = rng.uniform(0.0, coordinate_range, size=(n, 2))
    coords[0] = [coordinate_range / 2.0, coordinate_range / 2.0]
    distances = euclidean_distance_matrix(coords)
    demands = np.zeros(n, dtype=int)
    demands[1:] = rng.integers(demand_low, demand_high + 1, size=num_customers)
    time_windows = None
    if with_time_windows:
        time_windows = _generate_time_windows(rng, n, coordinate_range)
    return VRPInstance(
        coords=coords,
        distances=distances,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        num_vehicles=num_vehicles,
        depot=0,
        time_windows=time_windows,
        name=f"vrp-{num_customers}-{seed}",
    )


def _generate_time_windows(
    rng: np.random.Generator,
    n: int,
    coordinate_range: float,
) -> np.ndarray:
    """Random [earliest, latest] windows; the depot stays open the whole horizon."""
    horizon = coordinate_range * 4.0
    windows = np.zeros((n, 2))
    windows[0] = [0.0, horizon]
    for i in range(1, n):
        start = float(rng.uniform(0.0, horizon * 0.7))
        width = float(rng.uniform(horizon * 0.2, horizon * 0.4))
        windows[i] = [start, start + width]
    return windows
