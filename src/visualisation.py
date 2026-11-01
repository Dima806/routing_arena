"""Shared plotting: routes, the explosion curve, VRP solutions, the scoreboard."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes

from src.evaluation.scaling import ATOMS_IN_OBSERVABLE_UNIVERSE
from src.ortools_solver.routing import VRPSolution
from src.problems.tsp import TSPInstance
from src.problems.vrp import VRPInstance


def plot_tour(
    instance: TSPInstance,
    tour: list[int],
    ax: Axes | None = None,
    title: str = "",
) -> Axes:
    """Draw a closed tour over its stops."""
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))
    coords = instance.coords
    order = [*tour, tour[0]]
    ax.plot(coords[order, 0], coords[order, 1], "-", color="#4C78A8", linewidth=1.5, zorder=1)
    ax.scatter(coords[:, 0], coords[:, 1], color="#E45756", s=40, zorder=2)
    ax.scatter(coords[tour[0], 0], coords[tour[0], 1], color="#111111", s=90, zorder=3)
    ax.set_title(title)
    ax.set_aspect("equal")
    return ax


def plot_explosion(sizes: list[int], tour_counts: list[int], ax: Axes | None = None) -> Axes:
    """Tour count vs stops on a log scale, with the atoms-in-the-universe line."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    ax.semilogy(sizes, tour_counts, "-o", color="#4C78A8")
    ax.axhline(
        ATOMS_IN_OBSERVABLE_UNIVERSE,
        color="#E45756",
        linestyle="--",
        label="atoms in the observable universe",
    )
    ax.set_xlabel("number of stops")
    ax.set_ylabel("distinct tours (log scale)")
    ax.set_title("The combinatorial explosion")
    ax.legend()
    return ax


def plot_scaling(frame: pd.DataFrame, ax: Axes | None = None) -> Axes:
    """Solve time vs number of stops from `measure_scaling` output."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    ax.plot(frame["n"], frame["seconds"], "-o", color="#4C78A8")
    ax.set_xlabel("number of stops")
    ax.set_ylabel("solve time (seconds)")
    ax.set_title("Exact solve time vs instance size")
    return ax


def plot_arena(frame: pd.DataFrame, ax: Axes | None = None) -> Axes:
    """Bar chart of each method's gap to optimal."""
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 5))
    gaps = frame["gap_percent"].fillna(0.0)
    ax.barh(frame["method"], gaps, color="#4C78A8")
    ax.set_xlabel("gap to optimal (%)")
    ax.set_title("Arena scoreboard")
    ax.invert_yaxis()
    return ax


def plot_vrp_solution(
    instance: VRPInstance,
    solution: VRPSolution,
    ax: Axes | None = None,
) -> Axes:
    """Draw each vehicle's route from a VRP solution in its own colour."""
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))
    coords = instance.coords
    palette = plt.get_cmap("tab10")
    for v, route in enumerate(solution.routes):
        if len(route) <= 2:
            continue
        ax.plot(coords[route, 0], coords[route, 1], "-o", color=palette(v % 10), zorder=1)
    depot = instance.depot
    ax.scatter(coords[depot, 0], coords[depot, 1], color="#111111", marker="s", s=120, zorder=3)
    ax.set_title(f"VRP: {solution.num_vehicles_used} routes, length {solution.total_distance:.1f}")
    ax.set_aspect("equal")
    return ax
