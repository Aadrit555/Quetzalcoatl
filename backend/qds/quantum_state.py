"""
Single-Qubit Quantum State Engine
Implements exact statevectors, Pauli operators, Pauli eigenstates (Z, X, Y),
density matrices, Bloch sphere coordinates, and projective measurements.
"""

import math
import cmath
import random
import numpy as np
from typing import Dict, Any, Tuple, Optional

# Standard Unitary Pauli & Clifford Operators in C^(2x2)
PAULI_I = np.array([[1.0 + 0.0j, 0.0 + 0.0j],
                    [0.0 + 0.0j, 1.0 + 0.0j]], dtype=np.complex128)

PAULI_X = np.array([[0.0 + 0.0j, 1.0 + 0.0j],
                    [1.0 + 0.0j, 0.0 + 0.0j]], dtype=np.complex128)

PAULI_Y = np.array([[0.0 + 0.0j, 0.0 - 1.0j],
                    [0.0 + 1.0j, 0.0 + 0.0j]], dtype=np.complex128)

PAULI_Z = np.array([[1.0 + 0.0j, 0.0 + 0.0j],
                    [0.0 + 0.0j, -1.0 + 0.0j]], dtype=np.complex128)

HADAMARD = (1.0 / math.sqrt(2.0)) * np.array([[1.0 + 0.0j, 1.0 + 0.0j],
                                              [1.0 + 0.0j, -1.0 + 0.0j]], dtype=np.complex128)

PHASE_S = np.array([[1.0 + 0.0j, 0.0 + 0.0j],
                    [0.0 + 0.0j, 0.0 + 1.0j]], dtype=np.complex128)

# Canonical Single-Qubit Basis Vectors
STATE_0 = np.array([1.0 + 0.0j, 0.0 + 0.0j], dtype=np.complex128)
STATE_1 = np.array([0.0 + 0.0j, 1.0 + 0.0j], dtype=np.complex128)
STATE_PLUS = (1.0 / math.sqrt(2.0)) * np.array([1.0 + 0.0j, 1.0 + 0.0j], dtype=np.complex128)
STATE_MINUS = (1.0 / math.sqrt(2.0)) * np.array([1.0 + 0.0j, -1.0 + 0.0j], dtype=np.complex128)
STATE_PLUS_I = (1.0 / math.sqrt(2.0)) * np.array([1.0 + 0.0j, 0.0 + 1.0j], dtype=np.complex128)
STATE_MINUS_I = (1.0 / math.sqrt(2.0)) * np.array([1.0 + 0.0j, 0.0 - 1.0j], dtype=np.complex128)


class QubitState:
    """
    Represents an exact pure or mixed quantum state in C^2.
    Provides mathematically rigorous density matrix and statevector transformations.
    """

    def __init__(self, statevector: Optional[np.ndarray] = None, density_matrix: Optional[np.ndarray] = None):
        if statevector is not None:
            norm = np.linalg.norm(statevector)
            if norm < 1e-12:
                raise ValueError("Statevector norm cannot be zero.")
            self.statevector = (statevector / norm).astype(np.complex128)
            # Density matrix rho = |psi><psi|
            self.density_matrix = np.outer(self.statevector, np.conj(self.statevector))
        elif density_matrix is not None:
            # Normalize density matrix: Tr(rho) = 1
            tr = np.trace(density_matrix)
            if abs(tr) < 1e-12:
                raise ValueError("Density matrix trace cannot be zero.")
            self.density_matrix = (density_matrix / tr).astype(np.complex128)
            self.statevector = None
        else:
            # Default to ground state |0>
            self.statevector = STATE_0.copy()
            self.density_matrix = np.outer(self.statevector, np.conj(self.statevector))

    @classmethod
    def from_pauli_eigenstate(cls, basis: str, value: int) -> 'QubitState':
        """
        Creates a pure quantum state corresponding to a Pauli eigenstate.
        - basis 'Z': value 0 => |0>, value 1 => |1>
        - basis 'X': value 0 => |+>, value 1 => |->
        - basis 'Y': value 0 => |+i>, value 1 => |-i>
        """
        b = basis.upper()
        if b == "Z":
            vec = STATE_0 if value == 0 else STATE_1
        elif b == "X":
            vec = STATE_PLUS if value == 0 else STATE_MINUS
        elif b == "Y":
            vec = STATE_PLUS_I if value == 0 else STATE_MINUS_I
        else:
            raise ValueError(f"Unknown basis: {basis}. Expected 'Z', 'X', or 'Y'.")
        return cls(statevector=vec)

    @classmethod
    def from_bloch_angles(cls, theta: float, phi: float) -> 'QubitState':
        """
        Creates a statevector from Bloch sphere polar angle theta in [0, pi]
        and azimuthal angle phi in [0, 2*pi]:
        |psi> = cos(theta/2)|0> + e^(i*phi) sin(theta/2)|1>
        """
        alpha = math.cos(theta / 2.0)
        beta = cmath.exp(1.0j * phi) * math.sin(theta / 2.0)
        vec = np.array([alpha, beta], dtype=np.complex128)
        return cls(statevector=vec)

    def apply_unitary(self, U: np.ndarray) -> 'QubitState':
        """Applies single-qubit unitary operator U in C^(2x2)."""
        if self.statevector is not None:
            new_vec = np.dot(U, self.statevector)
            return QubitState(statevector=new_vec)
        else:
            new_rho = np.dot(U, np.dot(self.density_matrix, np.conj(U).T))
            return QubitState(density_matrix=new_rho)

    def apply_pauli_x(self) -> 'QubitState':
        return self.apply_unitary(PAULI_X)

    def apply_pauli_y(self) -> 'QubitState':
        return self.apply_unitary(PAULI_Y)

    def apply_pauli_z(self) -> 'QubitState':
        return self.apply_unitary(PAULI_Z)

    def apply_hadamard(self) -> 'QubitState':
        return self.apply_unitary(HADAMARD)

    def apply_depolarizing_channel(self, p: float) -> 'QubitState':
        """
        Simulates depolarizing quantum channel:
        E(rho) = (1 - p)*rho + (p/3)*(X rho X + Y rho Y + Z rho Z)
        """
        p = max(0.0, min(1.0, float(p)))
        if p == 0.0:
            return self

        rho = self.density_matrix
        rho_x = np.dot(PAULI_X, np.dot(rho, PAULI_X))
        rho_y = np.dot(PAULI_Y, np.dot(rho, PAULI_Y))
        rho_z = np.dot(PAULI_Z, np.dot(rho, PAULI_Z))

        depolarized_rho = (1.0 - p) * rho + (p / 3.0) * (rho_x + rho_y + rho_z)
        return QubitState(density_matrix=depolarized_rho)

    def apply_phase_flip_channel(self, p: float) -> 'QubitState':
        """E(rho) = (1 - p)*rho + p * Z rho Z"""
        p = max(0.0, min(1.0, float(p)))
        rho = self.density_matrix
        rho_z = np.dot(PAULI_Z, np.dot(rho, PAULI_Z))
        return QubitState(density_matrix=(1.0 - p) * rho + p * rho_z)

    def get_bloch_coordinates(self) -> Tuple[float, float, float]:
        """
        Calculates the Bloch vector components:
        x = Tr(rho * X), y = Tr(rho * Y), z = Tr(rho * Z)
        """
        x = float(np.real(np.trace(np.dot(self.density_matrix, PAULI_X))))
        y = float(np.real(np.trace(np.dot(self.density_matrix, PAULI_Y))))
        z = float(np.real(np.trace(np.dot(self.density_matrix, PAULI_Z))))
        return round(x, 4), round(y, 4), round(z, 4)

    def measure_projective(self, basis: str = "Z") -> Tuple[int, float, 'QubitState']:
        """
        Performs a projective measurement in the specified basis ('Z', 'X', or 'Y').
        Returns:
            outcome: 0 or 1
            probability: probability of the sampled outcome
            collapsed_state: post-measurement collapsed QubitState
        """
        b = basis.upper()
        if b == "Z":
            vec_0, vec_1 = STATE_0, STATE_1
        elif b == "X":
            vec_0, vec_1 = STATE_PLUS, STATE_MINUS
        elif b == "Y":
            vec_0, vec_1 = STATE_PLUS_I, STATE_MINUS_I
        else:
            raise ValueError(f"Unknown measurement basis: {basis}")

        # Projectors: P_0 = |e_0><e_0|, P_1 = |e_1><e_1|
        P_0 = np.outer(vec_0, np.conj(vec_0))
        P_1 = np.outer(vec_1, np.conj(vec_1))

        prob_0 = float(np.real(np.trace(np.dot(self.density_matrix, P_0))))
        prob_0 = max(0.0, min(1.0, prob_0))
        prob_1 = 1.0 - prob_0

        # Sample outcome according to Born's rule
        outcome = 0 if random.random() < prob_0 else 1
        collapsed_vec = vec_0 if outcome == 0 else vec_1
        prob = prob_0 if outcome == 0 else prob_1

        return outcome, prob, QubitState(statevector=collapsed_vec)

    def calculate_fidelity(self, target_state: 'QubitState') -> float:
        """
        Calculates quantum state fidelity F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2.
        For pure states |psi> and |phi>: F = |<psi|phi>|^2.
        """
        if self.statevector is not None and target_state.statevector is not None:
            overlap = np.dot(np.conj(self.statevector), target_state.statevector)
            return float(np.abs(overlap) ** 2)
        elif target_state.statevector is not None:
            # When target state is pure |phi>, F(rho, |phi>) = <phi|rho|phi>
            phi = target_state.statevector
            fidelity = float(np.real(np.dot(np.conj(phi), np.dot(self.density_matrix, phi))))
            return max(0.0, min(1.0, fidelity))
        else:
            from scipy.linalg import sqrtm
            rho = self.density_matrix
            sigma = target_state.density_matrix
            sqrt_rho = sqrtm(rho)
            inner = np.dot(sqrt_rho, np.dot(sigma, sqrt_rho))
            fidelity = float(np.real(np.trace(sqrtm(inner)))) ** 2
            return max(0.0, min(1.0, fidelity))

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable representation of the quantum state."""
        bx, by, bz = self.get_bloch_coordinates()
        data = {
            "bloch": {"x": bx, "y": by, "z": bz},
            "purity": round(float(np.real(np.trace(np.dot(self.density_matrix, self.density_matrix)))), 4)
        }
        if self.statevector is not None:
            data["amplitudes"] = {
                "alpha_real": round(float(self.statevector[0].real), 4),
                "alpha_imag": round(float(self.statevector[0].imag), 4),
                "beta_real": round(float(self.statevector[1].real), 4),
                "beta_imag": round(float(self.statevector[1].imag), 4)
            }
        return data
