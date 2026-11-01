"""Euclidean TSP instances, distance matrices, and tour helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TSPInstance:
    """A Euclidean TSP instance: point coordinates and their distance matrix."""

    coords: np.ndarray  # shape (n, 2)
    distances: np.ndarray  # shape (n, n), symmetric, zero diagonal
    name: str = "tsp"

    @property
    def n(self) -> int:
        """Number of stops."""
        return int(self.coords.shape[0])


def euclidean_distance_matrix(coords: np.ndarray) -> np.ndarray:
    """Full symmetric Euclidean distance matrix for a set of 2-D points."""
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    return np.sqrt((diff**2).sum(axis=-1))


def tour_length(tour: list[int], distances: np.ndarray) -> float:
    """Total length of a closed tour (the last stop returns to the first)."""
    total = 0.0
    n = len(tour)
    for i in range(n):
        total += float(distances[tour[i], tour[(i + 1) % n]])
    return total


def is_valid_tour(tour: list[int], n: int) -> bool:
    """True when `tour` visits every stop in 0..n-1 exactly once."""
    return sorted(tour) == list(range(n))


def generate_tsp_instance(
    n: int,
    seed: int = 0,
    layout: str = "uniform",
    coordinate_range: float = 100.0,
    num_clusters: int = 4,
) -> TSPInstance:
    """Generate a seeded Euclidean TSP instance with uniform or clustered points."""
    rng = np.random.default_rng(seed)
    if layout == "uniform":
        coords = rng.uniform(0.0, coordinate_range, size=(n, 2))
    elif layout == "clustered":
        coords = _clustered_points(rng, n, coordinate_range, num_clusters)
    else:
        raise ValueError(f"unknown layout: {layout!r} (use 'uniform' or 'clustered')")
    distances = euclidean_distance_matrix(coords)
    return TSPInstance(coords=coords, distances=distances, name=f"{layout}-{n}-{seed}")


def _clustered_points(
    rng: np.random.Generator,
    n: int,
    coordinate_range: float,
    num_clusters: int,
) -> np.ndarray:
    """Points drawn around a handful of random cluster centres."""
    centers = rng.uniform(0.0, coordinate_range, size=(num_clusters, 2))
    spread = coordinate_range / (num_clusters * 2)
    assignments = rng.integers(0, num_clusters, size=n)
    coords = centers[assignments] + rng.normal(0.0, spread, size=(n, 2))
    return np.clip(coords, 0.0, coordinate_range)
