# CLAUDE.md — routing_arena

Guidance for any Claude session working in this repository. Read this before writing code,
notebooks, or tests. For the full rationale, see
[.llm/PRD_routing_arena.md](.llm/PRD_routing_arena.md).

---

## 1. What this project is

`routing_arena` is a portfolio project for a data-science audience: a **head-to-head
comparison of ways to route a vehicle through a set of stops**, run entirely on CPU inside a
**2-CPU / 8 GB GitHub Codespace, no GPU**.

It is a GitHub repo with six Jupyter notebooks, a `src/` library, and a lightweight Streamlit
app. Everything completes on 2 CPUs in under five minutes per notebook.

**The thesis (keep every deliverable pointed at this):**

- The TSP and its generalization the VRP are **NP-hard**: the number of distinct tours through
  `n` stops grows **factorially**. Fifty stops has more possible tours than there are atoms in
  the observable universe. No solver escapes this.
- An **exact** solver (brute force, or a MILP with subtour elimination) is instant at ~10 stops
  and hopeless past ~tens of stops on a 2-CPU machine. The wall is arithmetic, not solver
  quality.
- A **nearest-neighbor** construction is ten lines of code, returns instantly, and is reliably
  **~20–25 % above optimal**. A baseline, never a production solution.
- **2-opt** local search on a nearest-neighbor start reaches **within a few percent of optimal**
  in a fraction of a second.
- **OR-Tools** guided local search lands within a percent or two *and* handles capacities,
  multiple vehicles, and time windows the exact MILP cannot touch at scale.
- The practical lesson: **give up on optimality on purpose.** Pick the method by instance size
  and constraints, and always know your gap-to-optimal by checking against exact on a small
  same-type instance.

**The narrative arc (notebooks, in order):**
the explosion → exact TSP → construction heuristics → local search → vehicle routing →
arena and decisions.

**Audience.** Data scientists and engineers who touch delivery, logistics, field service, or
warehouse operations and treat routing as a black box or an intractable mystery. Write code and
prose for someone who is technically strong but new to combinatorial optimization.

**Sibling projects** (do not depend on them in code; cross-link in prose only): builds on
[`optimization_101`](https://github.com/Dima806/optimization_101) (routing as a MILP, where exact
optimization runs out of road), feeds
[`supply_chain_arena`](https://github.com/Dima806/supply_chain_arena) (last-mile delivery is the
routing layer of the supply chain — the VRP notebook names this handoff), and is the discrete
cousin of [`curse_of_dimensionality_101`](https://github.com/Dima806/curse_of_dimensionality_101)
(combinatorial explosion as the discrete version of the curse). The README's "Related projects"
section carries their one-line descriptions.

---

## 2. Stack and hard constraints

- **Python 3.11+.**
- **Package manager: `uv`.** No `pip`, no `conda`, no `poetry`. Install deps with
  `uv sync --all-extras`; run everything through `uv run ...`.
- **Solvers are ALL open-source. No commercial solver, no license key, ever.**
  - `ortools` — routing library with guided local search (TSP + VRP).
  - `pulp` — models the exact MILP, solved with the bundled open CBC (`PULP_CBC_CMD`),
    the default `milp_tsp` backend. Pinned to `>=2.9,<3`: PuLP 4.x is a Rust rewrite with an
    incompatible API.
  - HiGHS is available as the `milp_tsp(backend="highs")` option **only via its CLI**
    (`HiGHS_CMD`), run out-of-process. The `highspy` Python bindings are **deliberately not a
    dependency**: `highspy` and `ortools` each bundle a different, ABI-incompatible copy of
    HiGHS, and importing both into one process crashes with an `undefined symbol` error
    regardless of import order. Do not add `highspy` back.
- **Core deps:** `ortools`, `pulp`, `numpy`, `scipy`, `pandas`, `matplotlib`,
  `plotly`, `streamlit`, `pydantic`, `pydantic-settings`, `pyyaml`.
- **Dev deps:** `pytest`, `ruff`, `ty`, `jupyter`, `ipykernel`, `nbconvert`, `nbclient`.
- **Resource budget:** 2 CPU cores, 8 GB RAM, no GPU. Distance matrices stay at most a few
  hundred × a few hundred. Every demonstrated heuristic run is near-instant; exact methods are
  run **only on small instances by design**, precisely to show where they stop.
- **Every long-running solve (OR-Tools, any exact run that is pushed past the easy range) is
  capped by an explicit time limit** so notebooks are bounded. Never leave a solve open-ended.

---

## 3. Repository layout

```
config/settings.yaml            Instance sizes, vehicle counts, capacities, time budgets, seeds
notebooks/                      01_the_explosion … 06_arena_and_decisions (the narrative arc)
src/
  config.py                     pydantic-settings loader for config/settings.yaml
  exact/
    brute_force.py              Enumerate all tours (tiny n only) — the ground truth
    milp_tsp.py                 MILP TSP, subtour elimination (MTZ or lazy cuts)
  heuristics/
    nearest_neighbor.py         Greedy construction from scratch
    christofides_like.py        Savings (Clarke-Wright) / cheapest-insertion construction
    two_opt.py                  2-opt local search from scratch
    or_opt.py                   Or-opt (segment relocation) from scratch
  ortools_solver/
    routing.py                  OR-Tools TSP/VRP with guided local search
  problems/
    tsp.py                      Distance matrices, Euclidean instances
    vrp.py                      Capacities, multiple vehicles, time windows
  evaluation/
    gap_to_optimal.py           Percent above exact optimum (small n) or best-known (large n)
    scaling.py                  Solve time vs number of stops (the explosion)
    comparison.py               Arena harness across methods
  visualisation.py              Shared plotting (routes, scaling curves, scoreboards)
  reporting.py                  save_figure (PNG) / save_json — persist every notebook artifact
app/streamlit_app.py            Explosion meter, route builder, 2-opt animator, fleet dispatcher
tests/                          test_exact, test_two_opt, test_ortools, test_vrp
outputs/figures/                Saved PNG figures (one file per notebook visual)
outputs/data/                   Saved JSON (every numeric/text result and parameter block)
```

Keep this module boundary. Algorithms live in `src/`; notebooks and the app **import and call
them**, they do not reimplement algorithms inline. The OR-Tools API is intricate — keep it
wrapped behind the small, tested `src/ortools_solver/routing.py` interface so notebooks show
clean calls; the raw setup is shown once, in a notebook, for teaching.

---

## 4. The methods (what each module must deliver)

- **Brute force** (`exact/brute_force.py`): enumerate every tour, tiny `n` only. Establishes the
  true optimum everything else is measured against, and viscerally demonstrates factorial growth
  as it crawls past a handful of stops.
- **Exact MILP** (`exact/milp_tsp.py`): TSP as a mixed-integer program with subtour-elimination
  constraints (MTZ, or lazy cut generation). Exact and fast on small instances; the star of the
  explosion demonstration as solve time detonates with size. Validated against brute force where
  both run.
- **Nearest-neighbor** (`heuristics/nearest_neighbor.py`): always go to the closest unvisited
  stop. Instant, complete, ~20–25 % above optimal. The calibration baseline for all heuristics.
- **Savings / insertion** (`heuristics/christofides_like.py`): Clarke-Wright savings and
  cheapest-insertion, from scratch. Better starting points than nearest-neighbor; the middle
  ground before local search.
- **2-opt and or-opt** (`heuristics/two_opt.py`, `heuristics/or_opt.py`): from scratch. 2-opt
  uncrosses wasteful edge pairs by reversing the segment between them; or-opt relocates short
  chains of stops. Both drive a nearest-neighbor start down to within a few percent of optimal,
  with tour length improving monotonically.
- **OR-Tools routing** (`ortools_solver/routing.py`): guided local search; the production tool.
  Solves TSP and the full VRP (capacities, multiple vehicles, time windows).

---

## 5. Data and reproducibility

- **All data is synthetic and generated with known structure.** No external data is downloaded.
  The arena measures gap-to-optimal, which needs either an exact optimum (small `n` only) or a
  strong best-known reference (a long OR-Tools run at larger sizes) — state which one is in use.
- Generate **Euclidean TSP instances at a ladder of sizes**, from tiny (brute force and MILP give
  the true optimum) up to sizes where only heuristics finish, so both the explosion and the
  gap-to-optimal are measurable.
- Provide **clustered and uniform** point layouts to show heuristics behaving differently on
  different geometry. Provide **VRP instances** with depot, capacities, demands, and time windows.
- **Everything is seeded.** Seeds, instance sizes, vehicle counts, capacities, and time budgets
  live in `config/settings.yaml` and load through `src/config.py` (pydantic-settings). Do not
  scatter magic numbers through notebooks — pull them from config.
- Keep the instance format **compatible with TSPLIB** so a reader can point the code at real
  benchmark instances.

---

## 6. Coding conventions

- **Lint/format: ruff.** Line length 99 (`E501` ignored). Lint rule sets:
  `E, F, W, I, UP, N, B, A, SIM, PTH`. Use `pathlib` (PTH), not `os.path`. Run `make lint` before
  calling anything done; it must pass with zero errors.
- **Type checking: `ty`** over `src/`. Add type hints to all public functions.
- **Prefer small, pure, testable functions.** A solver takes a problem (distance matrix / instance
  object) and returns a tour (and its length / metadata); keep I/O, plotting, and solving separate.
- **Numerics:** use `numpy` for distance matrices and vectorizable work. Keep matrices at a few
  hundred square at most.
- **No reimplementation in notebooks or the app** — import from `src/`. Match the style, naming,
  and comment density of the surrounding module when editing existing code.
- **Persist notebook outputs through `src/reporting.py`, never ad hoc.** Every figure goes through
  `save_figure(fig, name)` → `outputs/figures/<name>.png`; every table, metric, parameter block,
  schedule, and the decision rules go through `save_json(name, data)` → `outputs/data/<name>.json`
  (numpy scalars/arrays are coerced automatically). Name artifacts `<nb-number>_<slug>`.

---

## 7. Testing and success criteria

Tests encode the project's claims — they must stay green (`make test`, zero failures):

- `test_exact.py`: **MILP TSP matches brute force** at small `n` (true optimum, asserted).
- `test_two_opt.py`: **2-opt never lengthens a tour** (monotonicity, asserted) and improves a
  nearest-neighbor start.
- `test_ortools.py`: OR-Tools returns a **valid tour within a small gap** of optimal.
- `test_vrp.py`: VRP **respects capacities and visits every stop exactly once** (feasibility,
  asserted).

The broader success criteria the deliverables must demonstrate:

| Claim | Threshold |
|---|---|
| MILP vs brute force (small n) | Match the true optimum (asserted) |
| Exact solve-time explosion | Shown across the size ladder |
| Nearest-neighbor gap | ~20–25 % above optimal (quantified) |
| Nearest-neighbor + 2-opt gap | Within a few percent of optimal (shown) |
| OR-Tools TSP | Valid tour, small gap |
| VRP feasibility | Capacities respected, every stop once (asserted) |
| Arena crossover | Exact best at tiny n, heuristics dominate at scale (shown) |
| All solvers open-source | No commercial solver, no license (verified) |
| Notebook runtime | < 5 min each on a 2-CPU Codespace |
| `make lint` + `make test` | Zero errors |

---

## 8. Notebooks

Six notebooks, implemented and executing in ~3.5 min total (each well under the 5-minute budget),
each self-contained and executable top-to-bottom. `make notebooks` re-runs all six **in place**
(nbconvert `--inplace`, 300 s timeout each) using the `routing-arena` kernel that `make setup`
registers. Every visual is saved as a PNG and every number/text block as a JSON via
`src/reporting.py` (see §6) — currently 16 PNGs in `outputs/figures/` and 16 JSONs in
`outputs/data/`.

1. **01_the_explosion** (the showpiece) — tour count vs stops on a log scale next to physical
   reference points (atoms in the universe); brute force slowing from instant to hopeless.
2. **02_exact_tsp** — MILP with subtour elimination, validated against brute force, then pushed
   until solve time explodes; locate the exact frontier on a 2-CPU machine.
3. **03_construction_heuristics** — nearest-neighbor and its measured gap, then savings/insertion.
4. **04_local_search** — 2-opt uncrossing edges, dropping the NN route to within a few percent;
   or-opt as the complement. The single most valuable routing lesson.
5. **05_vehicle_routing** — VRP with capacities, multiple vehicles, time windows via OR-Tools;
   the last-mile layer of `supply_chain_arena`.
6. **06_arena_and_decisions** — the scoreboard across the size ladder (gap-to-optimal and solve
   time), the exact→heuristic crossover, and the decision framework.

**Decision framework to state in notebook 06:** under ~15–20 stops and you need
proof → exact MILP; anything larger → a construction plus 2-opt, or OR-Tools for capacities and
time windows; **never nearest-neighbor alone in production**; always know your gap-to-optimal.

---

## 9. Streamlit app (`app/streamlit_app.py`)

Four interactive pieces, all calling `src/`:
1. **Explosion meter** — add stops, watch the tour count and exact solve time climb.
2. **Route builder** — drop stops on a map, watch nearest-neighbor, 2-opt, and OR-Tools each draw
   their route with lengths and gap-to-optimal.
3. **2-opt animator** — watch local search uncross edges one swap at a time.
4. **Fleet dispatcher** — set vehicles, capacities, and time windows; watch OR-Tools split stops
   into routes.

---

## 10. Commands

Everything goes through the Makefile (which wraps `uv run`):

```
make setup       First-time setup: install uv if missing, uv sync --all-extras, register kernel
make lint        ruff format + ruff check --fix + ty check   (run before "done")
make test        pytest
make test-cov    pytest with coverage
make notebooks   Execute all notebooks in place, headless (300 s timeout each)
make run         Streamlit app on port 8501
make lab         JupyterLab
make ci          sync + lint + test
make dev         lint + test (fast local loop)
make clean       Remove caches
```

---

## 11. Do / don't

- **Do** keep every deliverable pointed at the thesis in §1 and back claims with the asserted tests
  in §7.
- **Do** cap every OR-Tools / pushed-exact solve with an explicit time limit; the explosion is
  shown deliberately and bounded, never left open-ended.
- **Do** pull sizes, seeds, capacities, and budgets from `config/settings.yaml`.
- **Don't** add a commercial solver, a license key, a GPU dependency, or `pip`/`conda`.
- **Don't** reimplement algorithms in notebooks or the app — import from `src/`.
- **Don't** let a distance matrix or instance grow past what 8 GB / 2 CPU handles in the notebook
  budget.

## 12. Working style

- **Caveman mode: ON** — code-first, terse prose in responses. This file is deliberately detailed;
  the mode governs working output, not this reference.
- Run `/compact` at notebook boundaries to keep context lean.
