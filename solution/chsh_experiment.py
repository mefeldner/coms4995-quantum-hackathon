"""Challenge 03, The Quantum Trading Edge: is the CHSH result a business?

Compares three ways two desks can play the startup's game:
  A. best classical strategy, no communication
  B. shared entanglement, no communication (ideal and at the measured quality)
  C. classical strategy over the private line the desks already have

Run:  uv run python solution/chsh_experiment.py
Writes solution/results/results.json, results.md and chsh_decision.png.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from scipy import optimize, stats

from qhack import run_counts

SEED = 20261119
OUT = Path(__file__).parent / "results"

# ---- Case file (every value is the startup's claim) -------------------------------------
N_TRIALS = 1000
P_QUANTUM_CLAIM = 0.82
P_CLASSICAL_CLAIM = 0.74
PAYOFF = 100.0  # +$100 on success, -$100 on failure
COST_QUANTUM = 0.08
COST_CLASSICAL = 0.001  # the startup's no-communication classical demo
ANNUAL_CLAIM = 50e6
TEST_LINK_KM = 40.0
PAIR_RATE_HZ = 1000.0

# ---- My assumptions (stated in WRITEUP.md) -----------------------------------------------
NY_LONDON_KM = 5570.0  # great-circle distance
C_KM_S = 299_792.458
FIBRE_DB_PER_KM = 0.2  # standard telecom fibre at 1550 nm
FIBRE_ROUTE_KM = 6000.0  # a transatlantic cable route is longer than the great circle
FIBRE_INDEX = 1.47
ACCIDENTAL_RATES_HZ = (0.001, 0.1, 10.0)  # noise coincidences per second, swept
COST_LINE = 0.0  # the line is already paid for; the case file gives no per-round cost
TAKE_RATES = (0.10, 0.20, 0.30)  # startup fee as a share of the firm's gross gain

# Measurement angles (radians, in the X-Z plane) for input bit 0 and 1.
ALICE = (0.0, math.pi / 4)
BOB = (math.pi / 8, -math.pi / 8)
TSIRELSON = math.cos(math.pi / 8) ** 2


# ---- A. Classical, no communication ------------------------------------------------------
def classical_strategies(p_x1: float = 0.5, p_y1: float = 0.5) -> list[dict]:
    """Win probability of all 16 deterministic strategies a=f(x), b=g(y)."""
    weights = {
        (x, y): (p_x1 if x else 1 - p_x1) * (p_y1 if y else 1 - p_y1)
        for x in (0, 1)
        for y in (0, 1)
    }
    out = []
    for a0, a1, b0, b1 in itertools.product((0, 1), repeat=4):
        win = sum(
            w for (x, y), w in weights.items() if ((a0, a1)[x] ^ (b0, b1)[y]) == (x & y)
        )
        out.append({"a": (a0, a1), "b": (b0, b1), "win": win})
    return out


def classical_max(p_x1: float = 0.5, p_y1: float = 0.5) -> float:
    # Shared randomness is a mixture of deterministic strategies, so it cannot beat the best one.
    return max(s["win"] for s in classical_strategies(p_x1, p_y1))


# ---- B. Entangled, no communication ------------------------------------------------------
def chsh_circuit(x: int, y: int, measure: bool = True) -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)  # |00> + |11>, shared before the inputs arrive
    qc.ry(-2 * ALICE[x], 0)  # desk A picks its basis from x only
    qc.ry(-2 * BOB[y], 1)  # desk B picks its basis from y only
    if measure:
        qc.measure_all()
    return qc


def exact_win(x: int, y: int) -> float:
    probs = Statevector(chsh_circuit(x, y, measure=False)).probabilities_dict()
    return sum(p for bits, p in probs.items() if (int(bits[0]) ^ int(bits[1])) == (x & y))


def visibility_to_win(v):
    """Werner state: a fraction v of the ideal pair, the rest white noise."""
    return 0.5 + np.asarray(v) / (2 * math.sqrt(2))


def win_to_visibility(p):
    return (np.asarray(p) - 0.5) * 2 * math.sqrt(2)


def simulate_rounds(n: int, visibility: float, seed: int) -> dict:
    """Play n rounds with a random (x, y) each round on Aer; noise sets the pair quality."""
    noise = NoiseModel()
    if visibility < 1:
        noise.add_all_qubit_quantum_error(depolarizing_error(1 - visibility, 2), ["cx"])
    backend = AerSimulator(noise_model=noise, seed_simulator=seed)
    rng = np.random.default_rng(seed)
    xs, ys = rng.integers(0, 2, n), rng.integers(0, 2, n)
    wins = 0
    a_one = {}  # P(a=1 | x, y): must not depend on y if nothing is signalled
    for x, y in itertools.product((0, 1), repeat=2):
        shots = int(np.sum((xs == x) & (ys == y)))
        counts = run_counts(chsh_circuit(x, y), backend, shots=shots)
        for bits, c in counts.items():
            a, b = int(bits[-1]), int(bits[0])  # qubit 0 is the rightmost character
            wins += c * ((a ^ b) == (x & y))
        a_one[f"x={x},y={y}"] = sum(c for bits, c in counts.items() if bits[-1] == "1") / shots
    return {"rounds": n, "wins": int(wins), "win_rate": wins / n, "p_a1_given_xy": a_one}


def simulate_classical(n: int, seed: int) -> dict:
    """Best classical strategy: both desks always answer 0."""
    rng = np.random.default_rng(seed + 1)
    xs, ys = rng.integers(0, 2, n), rng.integers(0, 2, n)
    wins = int(np.sum((xs & ys) == 0))
    return {"rounds": n, "wins": wins, "win_rate": wins / n}


def quantum_max_biased(p_x1: float, p_y1: float, visibility: float = 1.0) -> float:
    """Best entangled win rate when the inputs are biased (angles re-optimised)."""
    w = np.array(
        [
            [(1 - p_x1) * (1 - p_y1), (1 - p_x1) * p_y1],
            [p_x1 * (1 - p_y1), p_x1 * p_y1],
        ]
    )
    sign = np.array([[1, 1], [1, -1]])

    def neg_bias(t):
        a, b = (0.0, t[0]), (t[1], t[2])
        corr = np.array([[math.cos(2 * (a[x] - b[y])) for y in (0, 1)] for x in (0, 1)])
        return -float(np.sum(w * sign * corr))

    best = min(
        optimize.minimize(neg_bias, start, method="Nelder-Mead").fun
        for start in itertools.product((-0.6, 0.0, 0.6), repeat=3)
    )
    return 0.5 + visibility * (-best) / 2


# ---- Statistics and money ----------------------------------------------------------------
def binom_summary(k: int, n: int) -> dict:
    ci = stats.binomtest(k, n).proportion_ci(0.95, method="exact")
    return {
        "k": k,
        "n": n,
        "rate": k / n,
        "ci95": [ci.low, ci.high],
        "p_value_above_75pct": stats.binomtest(k, n, 0.75, alternative="greater").pvalue,
        "p_value_differs_from_75pct": stats.binomtest(k, n, 0.75).pvalue,
    }


def ev_per_round(p_win, cost: float):
    return PAYOFF * (2 * np.asarray(p_win) - 1) - cost


def unit_economics() -> dict:
    """Firm and startup P&L if the $50M is the firm's gross trading gain."""
    gain_q = PAYOFF * (2 * P_QUANTUM_CLAIM - 1)  # $64 per round
    gain_c = PAYOFF * (2 * 0.75 - 1)  # $50 per round
    n_q, n_c = ANNUAL_CLAIM / gain_q, ANNUAL_CLAIM / gain_c
    classical_same_volume = n_q * (gain_c - COST_CLASSICAL)
    max_fee = ANNUAL_CLAIM - classical_same_volume
    rows = []
    for t in TAKE_RATES:
        fee = t * ANNUAL_CLAIM
        rows.append(
            {
                "take_rate": t,
                "fee": fee,
                "firm_profit": ANNUAL_CLAIM - fee,
                "firm_profit_per_trade": (ANNUAL_CLAIM - fee) / n_q,
                "startup_revenue_per_trade": fee / n_q,
                "startup_profit_per_trade": fee / n_q - COST_QUANTUM,
                "startup_profit": fee - n_q * COST_QUANTUM,
            }
        )
    return {
        "quantum_trades_for_50M": n_q,
        "classical_trades_for_50M": n_c,
        "quantum_trades_per_trading_day": n_q / 252,
        "classical_profit_at_1M_trades": ANNUAL_CLAIM - n_c * COST_CLASSICAL,
        "classical_profit_at_quantum_volume": classical_same_volume,
        "line_profit_at_quantum_volume": n_q * (PAYOFF - COST_LINE),
        "max_fee_firm_would_pay": max_fee,
        "max_take_rate": max_fee / ANNUAL_CLAIM,
        "by_take_rate": rows,
    }


def fibre_model(length_km, accidental_hz: float):
    """Pair rate and win rate if the 40 km link were simply made longer.

    Signal coincidences fall with fibre loss; noise coincidences stay constant. Quality is
    calibrated so the model reproduces 82% at 40 km. A constant noise floor is the kind
    assumption: real accidentals fall more slowly than this model's noise-to-signal ratio implies.
    """
    length_km = np.asarray(length_km, dtype=float)
    rate = PAIR_RATE_HZ * 10 ** (-FIBRE_DB_PER_KM * (length_km - TEST_LINK_KM) / 10)
    v40 = float(win_to_visibility(P_QUANTUM_CLAIM))
    v_source = v40 * (PAIR_RATE_HZ + accidental_hz) / PAIR_RATE_HZ
    vis = v_source * rate / (rate + accidental_hz)
    return rate, visibility_to_win(vis)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    res: dict = {"seed": SEED}

    # 1. Classical ceiling, exactly.
    strategies = classical_strategies()
    c_max = classical_max()
    res["classical_no_comm"] = {
        "max_win": c_max,
        "n_strategies": len(strategies),
        "n_optimal": sum(abs(s["win"] - c_max) < 1e-12 for s in strategies),
        "all_win_rates": sorted({round(s["win"], 4) for s in strategies}),
        "simulated_1000": simulate_classical(N_TRIALS, SEED),
    }

    # 2. Quantum: exact, then sampled at ideal and at the measured quality.
    exact = float(np.mean([exact_win(x, y) for x in (0, 1) for y in (0, 1)]))
    v_claim = float(win_to_visibility(P_QUANTUM_CLAIM))
    res["quantum"] = {
        "exact_ideal_win": exact,
        "tsirelson_bound": TSIRELSON,
        "visibility_implied_by_82pct": v_claim,
        "visibility_needed_to_beat_classical": 1 / math.sqrt(2),
        "simulated_ideal_1000": simulate_rounds(N_TRIALS, 1.0, SEED),
        "simulated_at_claimed_quality_1000": simulate_rounds(N_TRIALS, v_claim, SEED),
        "simulated_at_claimed_quality_200000": simulate_rounds(200_000, v_claim, SEED),
    }

    # 3. Are the startup's two numbers distinguishable from 75%?
    q_stat = binom_summary(round(P_QUANTUM_CLAIM * N_TRIALS), N_TRIALS)
    c_stat = binom_summary(round(P_CLASSICAL_CLAIM * N_TRIALS), N_TRIALS)
    q_stat["visibility_ci95"] = [float(win_to_visibility(p)) for p in q_stat["ci95"]]
    res["startup_claims"] = {"quantum": q_stat, "classical": c_stat}

    # 4. Dollars per round.
    ev = {
        "classical_no_comm_75": float(ev_per_round(c_max, COST_CLASSICAL)),
        "quantum_measured_82": float(ev_per_round(P_QUANTUM_CLAIM, COST_QUANTUM)),
        "quantum_low_ci": float(ev_per_round(q_stat["ci95"][0], COST_QUANTUM)),
        "quantum_ideal": float(ev_per_round(TSIRELSON, COST_QUANTUM)),
        "classical_with_line_100": float(ev_per_round(1.0, COST_LINE)),
    }
    edge_vs_no_comm = ev["quantum_measured_82"] - ev["classical_no_comm_75"]
    edge_vs_line = ev["quantum_measured_82"] - ev["classical_with_line_100"]
    res["economics"] = {
        "net_usd_per_round": ev,
        "quantum_edge_vs_classical_no_comm": edge_vs_no_comm,
        "quantum_edge_vs_classical_with_line": edge_vs_line,
        "line_cost_per_round_at_which_quantum_wins": -edge_vs_line,
        "breakeven_quantum_win_rate": 0.75 + (COST_QUANTUM - COST_CLASSICAL) / (2 * PAYOFF),
        "rounds_per_year_for_50M_if_gross": ANNUAL_CLAIM / ev["quantum_measured_82"],
        "rounds_per_year_for_50M_if_incremental": ANNUAL_CLAIM / edge_vs_no_comm,
        "link_seconds_per_year_for_50M_incremental": ANNUAL_CLAIM / edge_vs_no_comm / PAIR_RATE_HZ,
    }

    res["unit_economics"] = unit_economics()

    # 5a. Distance.
    dist = {}
    for acc in ACCIDENTAL_RATES_HZ:
        f = lambda L, acc=acc: float(fibre_model(L, acc)[1]) - res["economics"][  # noqa: E731
            "breakeven_quantum_win_rate"
        ]
        dist[f"accidentals_{acc}_hz"] = {
            "edge_gone_at_km": float(optimize.brentq(f, TEST_LINK_KM, 2000)),
            "win_rate_at_ny_london": float(fibre_model(NY_LONDON_KM, acc)[1]),
        }
    rate_ny = float(fibre_model(NY_LONDON_KM, 0)[0])
    res["distance"] = {
        "loss_db_40km": FIBRE_DB_PER_KM * TEST_LINK_KM,
        "loss_db_ny_london": FIBRE_DB_PER_KM * NY_LONDON_KM,
        "log10_pair_rate_hz_ny_london": math.log10(PAIR_RATE_HZ)
        - FIBRE_DB_PER_KM * (NY_LONDON_KM - TEST_LINK_KM) / 10,
        "pair_rate_hz_ny_london": rate_ny,
        "km_where_rate_is_one_pair_per_hour": TEST_LINK_KM
        + 10 / FIBRE_DB_PER_KM * math.log10(PAIR_RATE_HZ * 3600),
        "by_noise_level": dist,
    }

    # 5b. Latency: when does the no-communication rule actually bind?
    light_ms = NY_LONDON_KM / C_KM_S * 1e3
    line_ms = FIBRE_ROUTE_KM * FIBRE_INDEX / C_KM_S * 1e3
    res["latency"] = {
        "light_one_way_ms": light_ms,
        "assumed_line_one_way_ms": line_ms,
        "light_one_way_ms_test_link": TEST_LINK_KM / C_KM_S * 1e3,
    }

    # 6. Sensitivity to the input statistics.
    bias = np.round(np.linspace(0.05, 0.95, 91), 4)
    c_b = np.array([classical_max(s, s) for s in bias])
    q_b_ideal = np.array([quantum_max_biased(s, s, 1.0) for s in bias])
    q_b_meas = np.array([quantum_max_biased(s, s, v_claim) for s in bias])
    # If the pair does not pay for itself the desks ignore it and play classically: edge 0.
    edge_meas = np.maximum(
        ev_per_round(q_b_meas, COST_QUANTUM) - ev_per_round(c_b, COST_CLASSICAL), 0
    )
    edge_ideal = np.maximum(
        ev_per_round(q_b_ideal, COST_QUANTUM) - ev_per_round(c_b, COST_CLASSICAL), 0
    )
    pos = bias[edge_meas > 0]
    res["input_bias"] = {
        "p_input_is_1": bias.tolist(),
        "classical_max": c_b.tolist(),
        "quantum_ideal": q_b_ideal.tolist(),
        "quantum_measured_quality": q_b_meas.tolist(),
        "edge_usd_measured_quality": edge_meas.tolist(),
        "edge_positive_range": [float(pos.min()), float(pos.max())] if len(pos) else None,
        "check_uniform_matches_tsirelson": quantum_max_biased(0.5, 0.5),
    }

    (OUT / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    write_table(res)
    make_figure(res, bias, edge_meas, edge_ideal)
    print((OUT / "results.md").read_text(encoding="utf-8"))


def write_table(res: dict) -> None:
    ev = res["economics"]["net_usd_per_round"]
    q = res["quantum"]
    c = res["classical_no_comm"]
    rows = [
        ("A. Classical, no communication (exact, 16 strategies)", c["max_win"],
         ev["classical_no_comm_75"]),
        ("B. Entangled, no communication, at measured quality", P_QUANTUM_CLAIM,
         ev["quantum_measured_82"]),
        ("B'. Entangled, perfect hardware (physical ceiling)", q["exact_ideal_win"],
         ev["quantum_ideal"]),
        ("C. Classical over the desks' existing line", 1.0, ev["classical_with_line_100"]),
    ]
    lines = ["| Alternative | Win rate | Net $ per round |", "| --- | --- | --- |"]
    lines += [f"| {n} | {p:.1%} | {d:,.2f} |" for n, p, d in rows]
    lines += [
        "",
        f"Simulated 1,000 rounds (seed {res['seed']}): classical "
        f"{c['simulated_1000']['win_rate']:.1%}, entangled ideal "
        f"{q['simulated_ideal_1000']['win_rate']:.1%}, entangled at measured quality "
        f"{q['simulated_at_claimed_quality_1000']['win_rate']:.1%}.",
    ]
    u = res["unit_economics"]
    lines += [
        "",
        f"Unit economics if $50M is the firm's gross gain: quantum needs "
        f"{u['quantum_trades_for_50M']:,.0f} trades, classical {u['classical_trades_for_50M']:,.0f}.",
        "",
        "| Take rate | Fee to startup | Firm profit | Firm $/trade | Startup $/trade | Startup profit |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines += [
        f"| {r['take_rate']:.0%} | {r['fee']:,.0f} | {r['firm_profit']:,.0f} | "
        f"{r['firm_profit_per_trade']:.2f} | {r['startup_profit_per_trade']:.2f} | "
        f"{r['startup_profit']:,.0f} |"
        for r in u["by_take_rate"]
    ]
    lines += [
        "",
        f"Classical at the same {u['quantum_trades_for_50M']:,.0f} trades earns "
        f"{u['classical_profit_at_quantum_volume']:,.0f}, so the most the firm would pay is "
        f"{u['max_fee_firm_would_pay']:,.0f} ({u['max_take_rate']:.1%}).",
    ]
    (OUT / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_figure(res: dict, bias, edge_meas, edge_ideal) -> None:
    ink, ink2, muted, grid, axis = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
    blue, orange, aqua = "#2a78d6", "#eb6834", "#1baf7a"
    plt.rcParams.update(
        {
            "font.family": ["Segoe UI", "DejaVu Sans"],
            "font.size": 9.5,
            "axes.edgecolor": axis,
            "axes.labelcolor": ink2,
            "xtick.color": muted,
            "ytick.color": muted,
            "xtick.labelcolor": ink2,
            "ytick.labelcolor": ink2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": grid,
            "grid.linewidth": 0.6,
            "axes.axisbelow": True,
            "figure.facecolor": "#fcfcfb",
            "axes.facecolor": "#fcfcfb",
            "axes.titlesize": 10.5,
            "axes.titleweight": "bold",
            "axes.titlecolor": ink,
            "axes.titlelocation": "left",
        }
    )
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 8.6))
    fig.suptitle(
        "The entangled strategy beats a silent classical desk, but not a desk with a phone line",
        x=0.012, ha="left", fontsize=13.5, fontweight="bold", color=ink,
    )
    ev = res["economics"]["net_usd_per_round"]
    claims = res["startup_claims"]

    # (a) win rates
    ax = axs[0, 0]
    labels = [
        "C. Classical over\nexisting line",
        "B'. Entangled,\nperfect hardware",
        "B. Entangled,\nmeasured quality",
        "A. Classical,\nno communication",
    ]
    vals = [1.0, res["quantum"]["exact_ideal_win"], P_QUANTUM_CLAIM, 0.75]
    cols = [aqua, orange, orange, blue]
    bars = ax.barh(labels, vals, color=cols, height=0.55)
    bars[1].set_alpha(0.45)
    for y, v in zip(range(4), vals):
        ax.text(v + 0.006, y, f"{v:.1%}", va="center", color=ink, fontsize=9.5)
    for y, key in ((2, "quantum"), (3, "classical")):
        s = claims[key]
        ax.errorbar(
            s["rate"], y - 0.36, xerr=[[s["rate"] - s["ci95"][0]], [s["ci95"][1] - s["rate"]]],
            fmt="o", color=ink, ms=4, lw=1.2, capsize=2.5,
        )
    ax.text(0.80, 2.64, "dots: startup's 1,000-trial\nresults, 95% interval", color=ink2,
            fontsize=8, va="center")
    ax.axvline(0.75, color=muted, lw=1, ls=(0, (4, 3)))
    ax.set_xlim(0.5, 1.07)
    ax.set_ylim(-0.5, 3.75)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("Rounds won")
    ax.set_title("1. Win rate on the startup's own game")
    ax.grid(axis="y", visible=False)

    # (b) $ per round vs decision deadline
    ax = axs[0, 1]
    line_ms = res["latency"]["assumed_line_one_way_ms"]
    light_ms = res["latency"]["light_one_way_ms"]
    t = np.array([0.0, line_ms, line_ms, 60.0])
    ax.plot(t, [ev["classical_no_comm_75"]] * 2 + [ev["classical_with_line_100"]] * 2,
            color=aqua, lw=2)
    ax.plot([0, 60], [ev["quantum_measured_82"]] * 2, color=orange, lw=2)
    ax.plot([0, 60], [ev["classical_no_comm_75"]] * 2, color=blue, lw=2, ls=(0, (1, 1.5)))
    ax.axvline(light_ms, color=muted, lw=1, ls=(0, (4, 3)))
    ax.text(light_ms - 0.8, 104, f"light-speed limit\n{light_ms:.1f} ms", color=ink2, fontsize=8,
            ha="right", va="top")
    ax.text(59.5, ev["classical_with_line_100"] - 3, "C. Classical over existing line",
            color=ink, ha="right", va="top", fontsize=9)
    ax.text(59.5, ev["quantum_measured_82"] + 1.5,
            "B. Entangled (only if a NY–London quantum link existed)", color=ink, ha="right",
            va="bottom", fontsize=9)
    ax.text(59.5, ev["classical_no_comm_75"] - 2, "A. Classical, no communication", color=ink,
            ha="right", va="top", fontsize=9)
    ax.axvspan(0, line_ms, color=orange, alpha=0.07, lw=0)
    ax.text(1.0, 36, f"only window where\nB can lead: under\n~{line_ms:.0f} ms",
            color=ink2, fontsize=8, ha="left", va="center")
    ax.set_xlim(0, 60)
    ax.set_ylim(25, 106)
    ax.set_xlabel("Time each desk has to act after its signal arrives (ms), New York–London")
    ax.set_ylabel("Net $ per round")
    ax.set_title("2. Value per round depends on the decision deadline")

    # (c) win rate vs fibre length
    ax = axs[1, 0]
    L = np.logspace(math.log10(40), math.log10(NY_LONDON_KM), 400)
    styles = [(0, (1, 1.5)), "-", (0, (5, 2))]
    for acc, ls in zip(ACCIDENTAL_RATES_HZ, styles):
        ax.plot(L, fibre_model(L, acc)[1], color=orange, lw=2, ls=ls,
                label=f"B. Entangled, noise floor {acc:g} pairs/s")
    ax.axhline(0.75, color=blue, lw=2, label="A. Classical, no communication")
    ax.plot([TEST_LINK_KM], [P_QUANTUM_CLAIM], "o", color=ink, ms=6, zorder=5)
    ax.annotate("measured:\n40 km, 82%", (TEST_LINK_KM, P_QUANTUM_CLAIM), xytext=(46, 0.865),
                color=ink, fontsize=8.5, va="center")
    ax.axvline(NY_LONDON_KM, color=muted, lw=1, ls=(0, (4, 3)))
    ax.text(NY_LONDON_KM * 0.93, 0.865, "New York–London\n5,570 km", color=ink2, fontsize=8.5,
            ha="right", va="center")
    ax.set_xscale("log")
    ax.set_xticks([40, 100, 200, 500, 1000, 2000, 5000])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_ylim(0.48, 0.9)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("Fibre length (km, log scale)")
    ax.set_ylabel("Rounds won")
    ax.legend(frameon=False, fontsize=8.5, loc=(0.50, 0.22), labelcolor=ink2)
    ax.set_title("3. Stretching the 40 km link: the edge is gone within a few hundred km")

    # (d) edge vs input bias
    ax = axs[1, 1]
    ax.axhline(0, color=axis, lw=1)
    ax.plot(bias, edge_ideal, color=orange, lw=2, alpha=0.45, label="perfect hardware")
    ax.plot(bias, edge_meas, color=orange, lw=2, label="measured quality (82%)")
    ax.plot([0.5], [res["economics"]["quantum_edge_vs_classical_no_comm"]], "o", color=ink, ms=6,
            zorder=5)
    ax.annotate("startup's game:\n50/50 inputs, +$13.92", (0.5, 13.92), xytext=(0.03, 16.5),
                color=ink, fontsize=8.5, va="center")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_xlabel("Probability that each desk's signal is 1")
    ax.set_ylabel("Entangled minus classical, $ per round")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", labelcolor=ink2)
    ax.set_title("4. The edge over silent classical desks needs near-50/50 signals")

    fig.text(
        0.012, 0.008,
        r"Payoff +\$100 / −\$100 per round; cost \$0.08 (quantum) and \$0.001 (classical) per round, "
        f"from the case file. Fibre loss 0.2 dB/km and line latency are my assumptions. Seed {SEED}.",
        color=muted, fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.025, 1, 0.955), h_pad=2.2, w_pad=2.0)
    fig.savefig(OUT / "chsh_decision.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    main()
