import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

from qhack import expectation_values, get_backend, run_counts


def bell(measure: bool = True) -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    if measure:
        qc.measure_all()
    return qc


def test_bell_counts_ideal():
    counts = run_counts(bell(), "aer", shots=2000)
    assert set(counts) == {"00", "11"}
    assert sum(counts.values()) == 2000
    assert abs(counts["00"] - 1000) < 150


def test_bell_expectation_ideal():
    zz, xx, zi = expectation_values(
        bell(measure=False),
        [SparsePauliOp("ZZ"), SparsePauliOp("XX"), SparsePauliOp("ZI")],
        "aer",
    )
    assert zz == pytest.approx(1.0, abs=0.1)
    assert xx == pytest.approx(1.0, abs=0.1)
    assert zi == pytest.approx(0.0, abs=0.1)


@pytest.mark.slow
def test_bell_counts_noisy():
    counts = run_counts(bell(), "noisy", shots=2000)
    correlated = counts.get("00", 0) + counts.get("11", 0)
    assert 0.8 < correlated / 2000 < 1.0  # noise visible, but mostly Bell


@pytest.mark.slow
def test_bell_expectation_noisy():
    zz, xx = expectation_values(
        bell(measure=False), [SparsePauliOp("ZZ"), SparsePauliOp("XX")], "noisy"
    )
    assert 0.7 < zz < 1.0
    assert 0.7 < xx < 1.0


def test_unknown_backend():
    with pytest.raises(ValueError):
        get_backend("nope")
