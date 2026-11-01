"""Gap to optimal: percent above the exact optimum or a best-known reference."""

from __future__ import annotations


def gap_percent(length: float, reference: float) -> float:
    """Percent by which `length` exceeds `reference` (the optimum or best-known)."""
    if reference <= 0.0:
        return 0.0
    return (length - reference) / reference * 100.0


def gap_fraction(length: float, reference: float) -> float:
    """Fractional gap: `gap_percent` divided by 100."""
    return gap_percent(length, reference) / 100.0
