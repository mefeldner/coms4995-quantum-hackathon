"""One place to choose where circuits run.

    get_backend("aer")          ideal local simulator (default, fast)
    get_backend("noisy")        local simulator with a real IBM device's noise model
    get_backend("ibm")          least-busy real IBM QPU (needs QISKIT_IBM_TOKEN)
    get_backend("ibm_fez")      a specific real IBM QPU by name

Everything else in the repo takes a backend object, so switching from simulator
to hardware is a one-word change.
"""

from __future__ import annotations

import os


def get_backend(name: str = "aer", *, min_qubits: int = 2):
    name = name.lower()

    if name == "aer":
        from qiskit_aer import AerSimulator

        return AerSimulator()

    if name == "noisy":
        from qiskit_aer import AerSimulator
        from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

        return AerSimulator.from_backend(FakeSherbrooke())

    if name.startswith("ibm"):
        service = _ibm_service()
        if name == "ibm":
            return service.least_busy(
                operational=True, simulator=False, min_num_qubits=min_qubits
            )
        return service.backend(name)

    raise ValueError(f"Unknown backend {name!r}. Use 'aer', 'noisy', 'ibm', or 'ibm_<device>'.")


def _ibm_service():
    from dotenv import load_dotenv
    from qiskit_ibm_runtime import QiskitRuntimeService

    load_dotenv()
    token = os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        raise RuntimeError(
            "QISKIT_IBM_TOKEN is not set. Copy .env.example to .env and add your "
            "IBM Quantum Platform API key."
        )
    kwargs = {"channel": "ibm_quantum_platform", "token": token}
    if instance := os.environ.get("QISKIT_IBM_INSTANCE"):
        kwargs["instance"] = instance
    return QiskitRuntimeService(**kwargs)
