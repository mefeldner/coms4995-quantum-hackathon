"""Run circuits the same way on a simulator or on hardware.

Both helpers transpile for the target backend first, then use the Qiskit Runtime
V2 primitives. For local backends the primitives run in local testing mode, so
no account is needed.
"""

from __future__ import annotations

from collections.abc import Sequence

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import EstimatorV2 as AerEstimatorV2
from qiskit_ibm_runtime import EstimatorV2, SamplerV2

from qhack.backends import get_backend


def _resolve(backend):
    return get_backend(backend) if isinstance(backend, str) else backend


def run_counts(
    circuit: QuantumCircuit,
    backend="aer",
    *,
    shots: int = 1024,
    optimization_level: int = 1,
) -> dict[str, int]:
    """Sample a circuit that contains measurements; return bitstring counts."""
    backend = _resolve(backend)
    pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend)
    isa = pm.run(circuit)
    result = SamplerV2(mode=backend).run([isa], shots=shots).result()
    return result[0].join_data().get_counts()


def expectation_values(
    circuit: QuantumCircuit,
    observables: SparsePauliOp | Sequence[SparsePauliOp],
    backend="aer",
    *,
    parameter_values=None,
    optimization_level: int = 1,
) -> list[float]:
    """Estimate <observable> for a measurement-free circuit. Returns one value per observable."""
    backend = _resolve(backend)
    if isinstance(observables, SparsePauliOp):
        observables = [observables]
    pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend)
    isa = pm.run(circuit)
    isa_obs = [obs.apply_layout(isa.layout) for obs in observables]
    pub = (isa, isa_obs) if parameter_values is None else (isa, isa_obs, parameter_values)
    result = _estimator(backend).run([pub]).result()
    return [float(v) for v in result[0].data.evs]


def _estimator(backend):
    # Aer's own estimator simulates only the qubits the circuit touches. The generic
    # one measures the whole device, which runs out of memory on a 127-qubit noise model.
    if isinstance(backend, AerSimulator):
        return AerEstimatorV2.from_backend(backend)
    return EstimatorV2(mode=backend)
