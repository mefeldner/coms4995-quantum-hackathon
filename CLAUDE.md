# Hackathon workspace

In-class hackathon for COMS 4995W (Lab-to-Market: Quantum & AI), Thursday Nov 19, 2026.
Problems release 1:00 PM, submission due 3:30 PM. Four computational challenges are given;
solve one. Individual submission. AI tools are explicitly allowed, and the stated goal is to
show how effectively AI can be used to build a solution to a quantum computing problem.

## Time budget (2.5 hours)

- 1:00-1:15 read all four problems in `problems/`, pick one. Prefer the one where a correct,
  verifiable result is reachable fastest with the installed toolkits.
- 1:15-2:45 build in `solution/`. Get a small end-to-end version working first, then scale.
- 2:45-3:15 verify against a classical/exact baseline, make plots, fill in `solution/WRITEUP.md`.
- 3:15-3:30 submit. Do not start new work after 3:15.

## Commands (Windows, Smart App Control is enforcing)

Always run tools as Python modules. The `.exe` launchers uv generates are blocked.

- `uv run python scripts/check_env.py` - pre-flight check of every toolkit
- `uv run python -m pytest -m "not slow"` - quick tests
- `uv run python -m jupyterlab` - notebooks
- `uv run python -m nbconvert --to notebook --execute <nb>` - run a notebook headless
- `uv run python -m ruff check --fix`

Adding a package (`uv add <pkg>`) can fail at import time if Smart App Control blocks its
DLLs. Check right after adding; if blocked, pin a slightly older release. Never disable Smart
App Control. numpy is capped below 2.5 for this reason.

## What is installed and verified

Qiskit 2.x + Aer + IBM Runtime, qiskit-algorithms (VQE/QAOA), qiskit-optimization,
qiskit-nature, qiskit-machine-learning, PennyLane + lightning, OpenFermion, Stim + PyMatching,
quimb (tensor networks/DMRG), PyTorch (CPU), scikit-learn, SciPy, pandas, networkx.

PySCF has no Windows build. For molecular Hamiltonians use `pennylane.qchem`, which works
without it (see `chemistry_pennylane` in `scripts/check_env.py`).

`scripts/check_env.py` holds a small working example for each toolkit. Copy from it.

## Conventions

- `from qhack import get_backend, run_counts, expectation_values`; backends are `"aer"`,
  `"noisy"`, `"ibm"`. Develop on `"aer"`.
- Every quantum result gets a classical or exact baseline next to it, and a fixed seed.
- Keep problem sizes small enough to simulate in seconds while iterating.
- Commit working checkpoints often; push before 3:15.
