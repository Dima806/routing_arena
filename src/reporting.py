"""Persist notebook outputs: figures as PNG, numbers and text as JSON.

Every notebook routes its visuals through `save_figure` and every table, metric,
parameter block, and takeaway through `save_json`, so the repository carries a
reproducible record of each figure and number cited.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from matplotlib.figure import Figure

_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = _ROOT / "outputs" / "figures"
DATA_DIR = _ROOT / "outputs" / "data"


def save_figure(fig: Figure, name: str, dpi: int = 150) -> Path:
    """Save a matplotlib figure to outputs/figures/<name>.png and return its path."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return path


def save_json(name: str, data: Any) -> Path:
    """Save numbers/text to outputs/data/<name>.json (numpy types coerced) and return its path."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{name}.json"
    with path.open("w") as handle:
        json.dump(data, handle, indent=2, default=_to_jsonable)
    return path


def _to_jsonable(value: Any) -> Any:
    """Coerce numpy scalars and arrays to built-in types for json.dump."""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"not JSON-serialisable: {type(value).__name__}")
