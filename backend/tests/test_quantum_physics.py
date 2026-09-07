"""Unit tests for Quantum Physics, Pauli Operators, Bell States, and Teleportation."""

import math
import numpy as np
import pytest

from backend.qds.quantum_state import (
    QubitState, PAULI_X, PAULI_Y, PAULI_Z, HADAMARD,
    STATE_0, STATE_1, STATE_PLUS, STATE_MINUS, STATE_PLUS_I, STATE_MINUS_I
)
from backend.qds.bell_states import (
    BellStateEngine, BELL_PHI_PLUS, BELL_PHI_MINUS, BELL_PSI_PLUS, BELL_PSI_MINUS
)
from backend.qds.teleportation import TeleportationSimulator

def test_pauli_eigenstates_orthogonality():
    # Z-basis
    q0 = QubitState.from_pauli_eigenstate("Z", 0)
    q1 = QubitState.from_pauli_eigenstate("Z", 1)
    assert abs(np.dot(np.conj(q0.statevector), q1.statevector)) < 1e-12

    # X-basis
    qp = QubitState.from_pauli_eigenstate("X", 0)
    qm = QubitState.from_pauli_eigenstate("X", 1)
    assert abs(np.dot(np.conj(qp.statevector), qm.statevector)) < 1e-12

    # Y-basis
    qpi = QubitState.from_pauli_eigenstate("Y", 0)
    qmi = QubitState.from_pauli_eigenstate("Y", 1)
    assert abs(np.dot(np.conj(qpi.statevector), qmi.statevector)) < 1e-12

def test_projective_measurements():
    # Measuring |+> in Z-basis yields 50/50 probability
    qp = QubitState.from_pauli_eigenstate("X", 0)
    outcomes = [qp.measure_projective("Z")[0] for _ in range(200)]
    ratio = sum(outcomes) / 200.0
    assert 0.35 < ratio < 0.65

    # Measuring |+> in X-basis yields outcome 0 with 100% probability
    outcomes_x = [qp.measure_projective("X")[0] for _ in range(50)]
    assert all(o == 0 for o in outcomes_x)

    # Measuring |1> in Z-basis yields outcome 1 with 100% probability
    q1 = QubitState.from_pauli_eigenstate("Z", 1)
    outcomes_z = [q1.measure_projective("Z")[0] for _ in range(50)]
    assert all(o == 1 for o in outcomes_z)

def test_bell_states_orthonormality():
    bell_states = [BELL_PHI_PLUS, BELL_PHI_MINUS, BELL_PSI_PLUS, BELL_PSI_MINUS]
    for i in range(4):
        # Normalization
        assert abs(np.linalg.norm(bell_states[i]) - 1.0) < 1e-12
        for j in range(4):
            overlap = np.dot(np.conj(bell_states[i]), bell_states[j])
            if i == j:
                assert abs(overlap - 1.0) < 1e-12
            else:
                assert abs(overlap) < 1e-12

def test_teleportation_noiseless_fidelity():
    # Test teleportation of various arbitrary states
    test_states = [
        QubitState.from_pauli_eigenstate("Z", 0),
        QubitState.from_pauli_eigenstate("Z", 1),
        QubitState.from_pauli_eigenstate("X", 0),
        QubitState.from_pauli_eigenstate("X", 1),
        QubitState.from_pauli_eigenstate("Y", 0),
        QubitState.from_pauli_eigenstate("Y", 1),
        QubitState.from_bloch_angles(math.pi / 3.0, math.pi / 4.0)
    ]

    for state in test_states:
        res = TeleportationSimulator.teleport_qubit(state, channel_noise_p=0.0)
        # In noiseless quantum channel, teleportation fidelity must be exactly 1.0
        assert res["fidelity"] == 1.0
        assert res["pauli_correction"] in ["I", "Z", "X", "XZ"]

def test_teleportation_noisy_channel():
    state = QubitState.from_pauli_eigenstate("X", 0)
    res = TeleportationSimulator.teleport_qubit(state, channel_noise_p=0.20, channel_noise_type="depolarizing")
    # Under 20% depolarizing noise, fidelity degrades below 1.0
    assert res["fidelity"] < 1.0

