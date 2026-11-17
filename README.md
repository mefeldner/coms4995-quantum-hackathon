# Quantum Hackathon Workspace

Workspace for the COMS 4995W (Lab-to-Market: Quantum & AI, Columbia, Fall 2026) hackathon sprint.
The deliverable is a sprint demo with working quantum software, so this repo is set up to get
from idea to a running circuit quickly, on a simulator first and on real hardware when ready.

## Setup

Requires [uv](https://docs.astral.sh/uv/). It installs the pinned Python (3.12) and all
dependencies into `.venv/`:

```
uv sync
uv run python -m pytest
```

On Windows, run tools as `python -m <tool>` as shown here. Smart App Control blocks the
unsigned `.exe` launchers that uv generates (`pytest.exe`, `jupyter.exe`), and it is also why
numpy is capped in `pyproject.toml`.

## Layout

| Path | What it is |
| --- | --- |
| `src/qhack/backends.py` | `get_backend("aer" \| "noisy" \| "ibm" \| "ibm_<device>")` |
| `src/qhack/run.py` | `run_counts(circuit, backend)` and `expectation_values(circuit, observables, backend)` |
| `tests/` | Smoke tests (Bell state on ideal and noisy simulators) |
| `notebooks/` | Exploration and demo notebooks |

## Usage

```python
from qiskit import QuantumCircuit
from qhack import run_counts

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

run_counts(qc, "aer")     # ideal simulator
run_counts(qc, "noisy")   # simulator with a real IBM device's noise model
run_counts(qc, "ibm")     # least-busy real QPU
```

Notebooks: `uv run python -m jupyterlab`, then open `notebooks/00_start_here.ipynb`.

## Real hardware

Copy `.env.example` to `.env` and add an IBM Quantum Platform API key. `.env` is gitignored;
never commit a token.

## Conventions

- Develop against `"aer"`, check against `"noisy"`, and only then spend QPU time.
- Always report a classical baseline next to any quantum result.
- Run `uv run python -m pytest -m "not slow"` for the quick tests, `uv run python -m ruff check`
  to lint.
