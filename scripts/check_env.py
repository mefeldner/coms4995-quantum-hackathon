"""Pre-flight check: run before the hackathon to confirm every toolkit really works.

    uv run python scripts/check_env.py

Each check does a tiny real computation, not just an import, because on Windows
Smart App Control can block a native DLL that only loads on first use.
"""

from __future__ import annotations

import sys
import time
import traceback


def qiskit_sim():
    from qiskit import QuantumCircuit

    from qhack import run_counts

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    counts = run_counts(qc, "aer", shots=200)
    assert set(counts) <= {"00", "11"}
    return f"Bell counts {counts}"


def qiskit_noisy():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp

    from qhack import expectation_values

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    (zz,) = expectation_values(qc, SparsePauliOp("ZZ"), "noisy")
    assert 0.7 < zz < 1.0
    return f"noisy <ZZ> = {zz:.3f}"


def vqe():
    from qiskit.circuit.library import efficient_su2
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_algorithms import VQE, NumPyMinimumEigensolver
    from qiskit_algorithms.optimizers import COBYLA

    h = SparsePauliOp.from_list([("ZZ", 1.0), ("XI", 0.5), ("IX", 0.5)])
    exact = NumPyMinimumEigensolver().compute_minimum_eigenvalue(h).eigenvalue.real
    res = VQE(StatevectorEstimator(), efficient_su2(2, reps=1), COBYLA(maxiter=200))
    got = res.compute_minimum_eigenvalue(h).eigenvalue.real
    assert got < exact + 0.1
    return f"VQE {got:.4f} vs exact {exact:.4f}"


def qaoa_maxcut():
    import networkx as nx
    from qiskit.primitives import StatevectorSampler
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    from qiskit_optimization.applications import Maxcut

    g = nx.cycle_graph(4)
    nx.set_edge_attributes(g, 1.0, "weight")
    qp = Maxcut(g).to_quadratic_program()
    qaoa = QAOA(StatevectorSampler(seed=1), COBYLA(maxiter=50), reps=1)
    result = MinimumEigenOptimizer(qaoa).solve(qp)
    assert result.fval == 4.0
    return f"MaxCut on C4 = {result.fval:.0f}"


def chemistry_qiskit_nature():
    from qiskit_nature.second_q.mappers import JordanWignerMapper
    from qiskit_nature.second_q.operators import FermionicOp

    op = FermionicOp({"+_0 -_1": 1.0, "+_1 -_0": 1.0}, num_spin_orbitals=2)
    qubit_op = JordanWignerMapper().map(op)
    return f"Jordan-Wigner hop -> {len(qubit_op)} Pauli terms"


def chemistry_pennylane():
    import pennylane as qml
    from pennylane import numpy as pnp

    geometry = pnp.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.4]], requires_grad=False)
    h, n = qml.qchem.molecular_hamiltonian(["H", "H"], geometry)
    e0 = float(min(qml.eigvals(h)).real)
    assert n == 4 and -1.2 < e0 < -1.1
    return f"H2 ground energy {e0:.4f} Ha on {n} qubits (no PySCF needed)"


def pennylane_grad():
    import pennylane as qml
    from pennylane import numpy as pnp

    dev = qml.device("lightning.qubit", wires=1)

    @qml.qnode(dev, diff_method="adjoint")
    def f(x):
        qml.RX(x, wires=0)
        return qml.expval(qml.PauliZ(0))

    g = float(qml.grad(f)(pnp.array(0.3, requires_grad=True)))
    assert abs(g + 0.2955) < 1e-3
    return f"lightning adjoint gradient {g:.4f}"


def qec_stim_pymatching():
    import pymatching
    import stim

    circuit = stim.Circuit.generated(
        "surface_code:rotated_memory_z",
        distance=3,
        rounds=3,
        after_clifford_depolarization=0.005,
    )
    dem = circuit.detector_error_model(decompose_errors=True)
    matcher = pymatching.Matching.from_detector_error_model(dem)
    dets, obs = circuit.compile_detector_sampler().sample(2000, separate_observables=True)
    errors = int((matcher.decode_batch(dets) != obs).any(axis=1).sum())
    assert errors < 200
    return f"d=3 surface code, MWPM logical errors {errors}/2000"


def openfermion_jw():
    from openfermion import FermionOperator, jordan_wigner

    return f"JW terms: {len(jordan_wigner(FermionOperator('1^ 0') + FermionOperator('0^ 1')).terms)}"


def tensor_network():
    import quimb.tensor as qtn

    builder = qtn.SpinHam1D(S=1 / 2)
    builder += 1.0, "Z", "Z"
    builder += -0.5, "X"
    dmrg = qtn.DMRG2(builder.build_mpo(8), bond_dims=[8, 16])
    dmrg.solve(tol=1e-6, verbosity=0)
    return f"DMRG energy, 8-site Ising chain: {dmrg.energy.real:.4f}"


def torch_train():
    import torch

    torch.manual_seed(0)
    x = torch.randn(64, 4)
    y = x.sum(dim=1, keepdim=True)
    model = torch.nn.Linear(4, 1)
    opt = torch.optim.Adam(model.parameters(), lr=0.1)
    for _ in range(100):
        opt.zero_grad()
        loss = torch.nn.functional.mse_loss(model(x), y)
        loss.backward()
        opt.step()
    assert loss.item() < 0.05
    return f"torch {torch.__version__}, fit loss {loss.item():.4f}"


def sklearn_scipy_pandas():
    import numpy as np
    import pandas as pd
    from scipy.optimize import minimize
    from sklearn.linear_model import LogisticRegression

    rng = np.random.default_rng(0)
    x = rng.normal(size=(100, 2))
    acc = LogisticRegression().fit(x, x[:, 0] > 0).score(x, x[:, 0] > 0)
    opt = minimize(lambda v: ((v - 1) ** 2).sum(), [0.0, 0.0])
    pd.DataFrame(x).describe()
    assert acc > 0.9 and opt.success
    return f"sklearn acc {acc:.2f}, scipy minimize ok"


def qml_qiskit():
    from qiskit.circuit.library import zz_feature_map
    from qiskit_machine_learning.kernels import FidelityStatevectorKernel

    k = FidelityStatevectorKernel(feature_map=zz_feature_map(2)).evaluate([[0.1, 0.2], [0.3, 0.4]])
    assert k.shape == (2, 2)
    return f"quantum kernel entry {k[0, 1]:.3f}"


def plotting():
    import matplotlib

    matplotlib.use("Agg")
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.draw("mpl")
    return "matplotlib circuit drawing ok"


CHECKS = [
    ("Qiskit ideal simulator", qiskit_sim),
    ("Qiskit noisy simulator", qiskit_noisy),
    ("VQE (qiskit-algorithms)", vqe),
    ("QAOA MaxCut (qiskit-optimization)", qaoa_maxcut),
    ("Fermion mapping (qiskit-nature)", chemistry_qiskit_nature),
    ("Molecular Hamiltonian (PennyLane)", chemistry_pennylane),
    ("PennyLane gradients", pennylane_grad),
    ("QEC: Stim + PyMatching", qec_stim_pymatching),
    ("OpenFermion", openfermion_jw),
    ("Tensor networks (quimb)", tensor_network),
    ("PyTorch", torch_train),
    ("scikit-learn / SciPy / pandas", sklearn_scipy_pandas),
    ("Quantum kernels (qiskit-ML)", qml_qiskit),
    ("Plotting", plotting),
]


def main() -> int:
    failed = 0
    for name, check in CHECKS:
        start = time.perf_counter()
        try:
            detail = check()
            status = "ok  "
        except Exception as exc:  # noqa: BLE001 - report everything, keep going
            failed += 1
            status = "FAIL"
            detail = f"{type(exc).__name__}: {str(exc).splitlines()[0][:150]}"
            if "-v" in sys.argv:
                traceback.print_exc()
        print(f"[{status}] {name:<36} {time.perf_counter() - start:5.1f}s  {detail}")
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
