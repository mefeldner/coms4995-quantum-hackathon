"""Shared helpers for the hackathon: pick a backend, run a circuit, get counts."""

from qhack.backends import get_backend
from qhack.run import expectation_values, run_counts

__all__ = ["expectation_values", "get_backend", "run_counts"]
