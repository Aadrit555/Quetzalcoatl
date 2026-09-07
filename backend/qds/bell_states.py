"""
Two-Qubit Composite States & Bell-State Measurement (BSM) Engine
Implements the 4 maximally entangled Bell states (EPR pairs) and complete BSM projectors in C^4.
"""

import math
import random
import numpy as np
from typing import Dict, Any, Tuple, List
from backend.qds.quantum_state import QubitState, STATE_0, STATE_1

# Canonical 4-dimensional Bell Statevectors
INV_SQRT2 = 1.0 / math.sqrt(2.0)

BELL_PHI_PLUS = INV_SQRT2 * np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128)
BELL_PHI_MINUS = INV_SQRT2 * np.array([1.0, 0.0, 0.0, -1.0], dtype=np.complex128)
BELL_PSI_PLUS = INV_SQRT2 * np.array([0.0, 1.0, 1.0, 0.0], dtype=np.complex128)
BELL_PSI_MINUS = INV_SQRT2 * np.array([0.0, 1.0, -1.0, 0.0], dtype=np.complex128)

# Bell Projector Operators Pi_m = |Bell_m><Bell_m|
PROJECTOR_PHI_PLUS = np.outer(BELL_PHI_PLUS, np.conj(BELL_PHI_PLUS))
PROJECTOR_PHI_MINUS = np.outer(BELL_PHI_MINUS, np.conj(BELL_PHI_MINUS))
PROJECTOR_PSI_PLUS = np.outer(BELL_PSI_PLUS, np.conj(BELL_PSI_PLUS))
PROJECTOR_PSI_MINUS = np.outer(BELL_PSI_MINUS, np.conj(BELL_PSI_MINUS))

BELL_PROJECTORS = {
    "Phi+": PROJECTOR_PHI_PLUS,
    "Phi-": PROJECTOR_PHI_MINUS,
    "Psi+": PROJECTOR_PSI_PLUS,
    "Psi-": PROJECTOR_PSI_MINUS
}

# Mapping Bell outcome to Alice's classical broadcast bits (b1, b2)
# Standard teleportation convention:
# |Phi+> => (0, 0) => Bob applies I
# |Phi-> => (0, 1) => Bob applies Z
# |Psi+> => (1, 0) => Bob applies X
# |Psi-> => (1, 1) => Bob applies ZX (-iY)
BELL_TO_CLASSICAL_BITS = {
    "Phi+": (0, 0),
    "Phi-": (0, 1),
    "Psi+": (1, 0),
    "Psi-": (1, 1)
}


class BellStateEngine:
    """Provides methods for Bell pair generation and Bell-State Measurements."""

    @staticmethod
    def create_bell_pair(name: str = "Phi+") -> np.ndarray:
        """Returns the 4-element complex statevector for the requested Bell state."""
        if name == "Phi+":
            return BELL_PHI_PLUS.copy()
        elif name == "Phi-":
            return BELL_PHI_MINUS.copy()
        elif name == "Psi+":
            return BELL_PSI_PLUS.copy()
        elif name == "Psi-":
            return BELL_PSI_MINUS.copy()
        else:
            raise ValueError(f"Unknown Bell state: {name}. Must be Phi+, Phi-, Psi+, or Psi-.")

    @staticmethod
    def perform_bsm(two_qubit_state: np.ndarray) -> Tuple[str, Tuple[int, int], float]:
        """
        Performs a projective Bell-State Measurement on a 2-qubit statevector in C^4.
        Returns:
            bell_name: 'Phi+', 'Phi-', 'Psi+', or 'Psi-'
            classical_bits: (b1, b2) in {0,1}^2
            probability: measurement outcome probability
        """
        if len(two_qubit_state) != 4:
            raise ValueError("Input statevector must have dimension 4 for 2 qubits.")

        norm = np.linalg.norm(two_qubit_state)
        normalized_state = two_qubit_state / norm

        # Compute probabilities: P_m = <psi|Pi_m|psi>
        probabilities = {}
        for name, proj in BELL_PROJECTORS.items():
            prob = float(np.real(np.dot(np.conj(normalized_state), np.dot(proj, normalized_state))))
            probabilities[name] = max(0.0, min(1.0, prob))

        # Sample Bell outcome according to Born rule
        names = list(probabilities.keys())
        probs = [probabilities[n] for n in names]
        total_p = sum(probs)
        if total_p < 1e-12:
            probs = [0.25, 0.25, 0.25, 0.25]
        else:
            probs = [p / total_p for p in probs]

        sampled_name = random.choices(names, weights=probs, k=1)[0]
        classical_bits = BELL_TO_CLASSICAL_BITS[sampled_name]

        return sampled_name, classical_bits, probabilities[sampled_name]

