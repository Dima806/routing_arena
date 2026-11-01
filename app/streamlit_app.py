"""routing_arena Streamlit app: explosion meter, route builder, 2-opt, fleet dispatcher."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from src.evaluation.gap_to_optimal import gap_percent
from src.evaluation.scaling import ATOMS_IN_OBSERVABLE_UNIVERSE, tour_count
from src.heuristics.nearest_neighbor import nearest_neighbor_tour
from src.heuristics.two_opt import two_opt, two_opt_steps
from src.ortools_solver.routing import solve_tsp, solve_vrp
from src.problems.tsp import generate_tsp_instance, tour_length
from src.problems.vrp import generate_vrp_instance
from src.visualisation import plot_tour, plot_vrp_solution

st.set_page_config(page_title="routing_arena", layout="wide")
st.title("routing_arena")
st.caption("Give up on optimality on purpose: exact vs heuristic routing on a 2-CPU machine.")

explosion, builder, animator, dispatcher = st.tabs(
    ["Explosion meter", "Route builder", "2-opt animator", "Fleet dispatcher"]
)

with explosion:
    st.header("The combinatorial explosion")
    stops = st.slider("Number of stops", min_value=3, max_value=60, value=20)
    count = tour_count(stops)
    st.metric("Distinct tours", f"{count:.3e}")
    ratio = count / ATOMS_IN_OBSERVABLE_UNIVERSE
    if ratio >= 1.0:
        st.warning(f"That is {ratio:.2e}x the atoms in the observable universe.")
    else:
        st.info(f"That is {ratio:.2e} of the atoms in the observable universe.")

with builder:
    st.header("Route builder")
    size = st.slider("Stops", min_value=5, max_value=40, value=12, key="builder_size")
    seed = st.number_input("Seed", min_value=0, max_value=9999, value=0, key="builder_seed")
    instance = generate_tsp_instance(size, seed=int(seed))

    nn_tour = nearest_neighbor_tour(instance.distances)
    opt_tour = two_opt(nn_tour, instance.distances)
    ortools_tour, reference = solve_tsp(instance.distances, time_limit=2.0)

    columns = st.columns(3)
    labelled = [("Nearest-neighbor", nn_tour), ("+ 2-opt", opt_tour), ("OR-Tools", ortools_tour)]
    for col, (label, tour) in zip(columns, labelled, strict=True):
        length = tour_length(tour, instance.distances)
        fig, ax = plt.subplots(figsize=(4, 4))
        plot_tour(instance, tour, ax=ax, title=label)
        col.pyplot(fig)
        col.metric(label, f"{length:.1f}", f"{gap_percent(length, reference):+.1f}% vs OR-Tools")

with animator:
    st.header("2-opt animator")
    size = st.slider("Stops", min_value=6, max_value=30, value=15, key="anim_size")
    seed = st.number_input("Seed", min_value=0, max_value=9999, value=1, key="anim_seed")
    instance = generate_tsp_instance(size, seed=int(seed))
    nn_tour = nearest_neighbor_tour(instance.distances)
    steps = list(two_opt_steps(nn_tour, instance.distances))
    step = st.slider("Swap", min_value=0, max_value=len(steps) - 1, value=len(steps) - 1)
    fig, ax = plt.subplots(figsize=(5, 5))
    length = tour_length(steps[step], instance.distances)
    plot_tour(instance, steps[step], ax=ax, title=f"after {step} swaps — length {length:.1f}")
    st.pyplot(fig)

with dispatcher:
    st.header("Fleet dispatcher")
    customers = st.slider("Customers", min_value=5, max_value=40, value=20)
    vehicles = st.slider("Vehicles", min_value=1, max_value=8, value=4)
    capacity = st.slider("Vehicle capacity", min_value=10, max_value=150, value=60)
    vrp = generate_vrp_instance(customers, vehicles, capacity, seed=0)
    st.caption(f"Total demand {vrp.total_demand} vs fleet capacity {vehicles * capacity}.")
    try:
        solution = solve_vrp(vrp, time_limit=3.0)
        fig, ax = plt.subplots(figsize=(6, 6))
        plot_vrp_solution(vrp, solution, ax=ax)
        st.pyplot(fig)
        st.metric("Routes used", solution.num_vehicles_used)
        st.metric("Total distance", f"{solution.total_distance:.1f}")
    except RuntimeError:
        st.error("No feasible plan: raise the capacity or add vehicles.")
