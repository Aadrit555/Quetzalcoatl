"""
QUBO & Ising Hamiltonian Model for Threat Correlation
Translates multi-source anomaly signals into a Quadratic Unconstrained Binary Optimization problem.
H(x) = x^T Q x = sum_i Q_ii x_i + sum_{i < j} (Q_ij + Q_ji) x_i x_j
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from backend.config import SIGNAL_NAMES, DEFAULT_LINEAR_WEIGHTS, DEFAULT_COUPLING_SYNERGIES

class ThreatQUBOModel:
    """
    Constructs and evaluates QUBO (Quadratic Unconstrained Binary Optimization) matrices
    and equivalent Ising spin models for multi-signal cyber threat correlation.
    """

    def __init__(self, signals: List[str] = None):
        self.signals = signals or SIGNAL_NAMES
        self.n = len(self.signals)
        self.signal_to_idx = {sig: i for i, sig in enumerate(self.signals)}

    def build_qubo_matrix(
        self,
        signal_intensities: Dict[str, float],
        custom_weights: Dict[str, float] = None,
        custom_synergies: Dict[Tuple[str, str], float] = None
    ) -> np.ndarray:
        """
        Builds an n x n symmetric QUBO matrix Q from observed continuous signal intensities [0.0, 1.0].
        - Diagonal entries Q[i, i]: individual signal threat severity (weighted by signal intensity).
        - Off-diagonal entries Q[i, j]: synergistic interaction between co-occurring threats.
        In threat energy minimization:
        We minimize: E(x) = sum_i (-h_i * intensity_i) * x_i + sum_{i < j} (-J_ij * int_i * int_j) * x_i * x_j
        The ground state (minimum energy) activates the most coherent, mutually reinforcing threat cluster!
        """
        weights = custom_weights or DEFAULT_LINEAR_WEIGHTS
        synergies = custom_synergies or DEFAULT_COUPLING_SYNERGIES

        Q = np.zeros((self.n, self.n), dtype=np.float64)

        # Diagonal entries (Linear risk bias)
        # Negative sign so that higher threat intensity drives the system toward selecting x_i = 1
        for sig, val in signal_intensities.items():
            if sig in self.signal_to_idx:
                idx = self.signal_to_idx[sig]
                w = weights.get(sig, 3.0)
                # If signal intensity is high (> 0.2), negative energy encourages activation
                # If signal is 0 or low, slight penalty (+0.5) discourages activation
                normalized_intensity = max(0.0, min(1.0, float(val)))
                bias = (normalized_intensity * w) - 0.3
                Q[idx, idx] = -bias

        # Off-diagonal entries (Quadratic risk synergy)
        for (sig_a, sig_b), coupling in synergies.items():
            if sig_a in self.signal_to_idx and sig_b in self.signal_to_idx:
                ia = self.signal_to_idx[sig_a]
                ib = self.signal_to_idx[sig_b]
                val_a = max(0.0, min(1.0, float(signal_intensities.get(sig_a, 0.0))))
                val_b = max(0.0, min(1.0, float(signal_intensities.get(sig_b, 0.0))))

                # Synergy is amplified when both threats manifest simultaneously
                synergy_weight = coupling * val_a * val_b
                # Split equally across symmetric off-diagonals
                Q[ia, ib] -= synergy_weight / 2.0
                Q[ib, ia] -= synergy_weight / 2.0

        return Q

    def qubo_to_ising(self, Q: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Converts QUBO matrix Q to Ising model parameters:
        x_i = (s_i + 1) / 2 where s_i in {-1, +1}
        Returns:
            h: linear magnetic fields (1D vector of length n)
            J: quadratic spin-spin interactions (n x n symmetric matrix with zero diagonal)
            offset: constant energy offset
        """
        n = Q.shape[0]
        h = np.zeros(n, dtype=np.float64)
        J = np.zeros((n, n), dtype=np.float64)
        offset = 0.0

        for i in range(n):
            h[i] = 0.5 * Q[i, i] + 0.25 * (np.sum(Q[i, :]) + np.sum(Q[:, i]) - 2 * Q[i, i])
            offset += 0.25 * Q[i, i]

        for i in range(n):
            for j in range(i + 1, n):
                J[i, j] = 0.25 * (Q[i, j] + Q[j, i])
                J[j, i] = J[i, j]
                offset += 0.25 * (Q[i, j] + Q[j, i])

        return h, J, offset

    def evaluate_energy(self, state: np.ndarray, Q: np.ndarray) -> float:
        """Calculates E(x) = x^T Q x for a binary vector x in {0, 1}^n."""
        return float(np.dot(state.T, np.dot(Q, state)))

    def calculate_explainability(
        self,
        optimal_state: np.ndarray,
        signal_intensities: Dict[str, float],
        Q: np.ndarray
    ) -> Dict[str, Any]:
        """
        Calculates individual and synergistic feature contributions to the final risk score.
        Enables human-in-the-loop auditability and explainable AI in the SOC dashboard.
        """
        feature_contributions = {}
        total_threat_energy = 0.0

        # Linear contributions
        for i, sig in enumerate(self.signals):
            if optimal_state[i] == 1:
                # Energy contribution = Q[i, i]
                c = abs(min(0.0, Q[i, i]))
                feature_contributions[sig] = {
                    "activated": True,
                    "intensity": round(signal_intensities.get(sig, 0.0), 3),
                    "linear_energy": round(c, 3),
                    "synergy_energy": 0.0,
                    "total_contribution": round(c, 3)
                }
                total_threat_energy += c
            else:
                feature_contributions[sig] = {
                    "activated": False,
                    "intensity": round(signal_intensities.get(sig, 0.0), 3),
                    "linear_energy": 0.0,
                    "synergy_energy": 0.0,
                    "total_contribution": 0.0
                }

        # Pairwise synergy contributions
        synergies_detected = []
        n = len(self.signals)
        for i in range(n):
            for j in range(i + 1, n):
                if optimal_state[i] == 1 and optimal_state[j] == 1:
                    coupling_term = abs(min(0.0, Q[i, j] + Q[j, i]))
                    if coupling_term > 0.01:
                        sig_a = self.signals[i]
                        sig_b = self.signals[j]
                        feature_contributions[sig_a]["synergy_energy"] += round(coupling_term / 2, 3)
                        feature_contributions[sig_b]["synergy_energy"] += round(coupling_term / 2, 3)
                        feature_contributions[sig_a]["total_contribution"] += round(coupling_term / 2, 3)
                        feature_contributions[sig_b]["total_contribution"] += round(coupling_term / 2, 3)
                        total_threat_energy += coupling_term
                        synergies_detected.append({
                            "pair": [sig_a, sig_b],
                            "amplification": round(coupling_term, 3),
                            "description": f"Synergistic amplification between {sig_a} and {sig_b}"
                        })

        return {
            "active_threat_features": [self.signals[i] for i, val in enumerate(optimal_state) if val == 1],
            "feature_contributions": feature_contributions,
            "synergies_detected": synergies_detected,
            "total_qubo_threat_energy": round(total_threat_energy, 3)
        }

