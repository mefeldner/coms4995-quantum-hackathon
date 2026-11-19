"""Checks a reviewer can rerun: the classical ceiling and the quantum value of the game."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "solution"))
import chsh_experiment as ce


def test_classical_ceiling_is_75_percent():
    wins = [s["win"] for s in ce.classical_strategies()]
    assert len(wins) == 16
    assert max(wins) == pytest.approx(0.75)


def test_entangled_strategy_reaches_tsirelson_bound():
    for x in (0, 1):
        for y in (0, 1):
            assert ce.exact_win(x, y) == pytest.approx(math.cos(math.pi / 8) ** 2)


def test_noise_model_matches_formula():
    v = float(ce.win_to_visibility(0.82))
    sim = ce.simulate_rounds(40_000, v, seed=7)
    assert sim["win_rate"] == pytest.approx(0.82, abs=0.01)
    # No signalling: desk A's answers are a coin flip whatever desk B's input was.
    assert all(abs(p - 0.5) < 0.02 for p in sim["p_a1_given_xy"].values())


def test_unit_economics():
    u = ce.unit_economics()
    assert u["quantum_trades_for_50M"] == pytest.approx(781_250)
    assert u["classical_trades_for_50M"] == pytest.approx(1_000_000)
