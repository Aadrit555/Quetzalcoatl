"""
Quantum-Inspired Simulated Annealing Engine (SQA)
Solves QUBO / Ising optimization using simulated quantum fluctuations (transverse field tunneling)
and thermal annealing to isolate optimal threat clusters in sub-5ms latency.
"""

import math
import random
import numpy as np
from typing import Dict, List, Tuple, Any
from backend.quantum.qubo_model import ThreatQUBOModel

class QuantumInspiredAnnealer:
    """
    Executes Quantum-Inspired Annealing to minimize QUBO / Ising Hamiltonian energy.
    Simulates quantum tunneling effect (transverse field Gamma) to escape local minima
    without requiring physical quantum hardware.
    """

    def __init__(
        self,
        num_sweeps: int = 150,
        initial_temperature: float = 5.0,
        final_temperature: float = 0.05,
        initial_gamma: float = 3.0,
        random_seed: int = 42
    ):
        self.num_sweeps = num_sweeps
        self.initial_temperature = initial_temperature
        self.final_temperature = final_temperature
        self.initial_gamma = initial_gamma
        self.random_seed = random_seed
        self.qubo_model = ThreatQUBOModel()

    def solve(
        self,
        signal_intensities: Dict[str, float],
        custom_weights: Dict[str, float] = None,
        custom_synergies: Dict[Tuple[str, str], float] = None
    ) -> Dict[str, Any]:
        """
        Runs quantum-inspired annealing over the multi-signal QUBO matrix.
        Returns:
            optimal_binary_state: best found binary vector in {0, 1}^n
            optimal_spins: mapped Ising spins in {-1, +1}^n
            min_energy: minimum Hamiltonian energy found
            risk_score: calibrated risk score between 0.0 and 100.0
            energy_trajectory: list of energy values across sweeps for visualization
            explainability: detailed breakdown of signals and cross-signal synergies
        """
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)

        # Build QUBO matrix
        Q = self.qubo_model.build_qubo_matrix(
            signal_intensities=signal_intensities,
            custom_weights=custom_weights,
            custom_synergies=custom_synergies
        )

        n = len(self.qubo_model.signals)

        # Initialize state: start with heuristic based on high signals
        current_state = np.zeros(n, dtype=np.int32)
        for i, sig in enumerate(self.qubo_model.signals):
            if signal_intensities.get(sig, 0.0) > 0.4:
                current_state[i] = 1

        best_state = current_state.copy()
        current_energy = self.qubo_model.evaluate_energy(current_state, Q)
        best_energy = current_energy

        energy_trajectory: List[float] = [round(current_energy, 4)]
        gamma_trajectory: List[float] = [round(self.initial_gamma, 4)]

        # Cooling factor
        decay = (self.final_temperature / self.initial_temperature) ** (1.0 / max(1, self.num_sweeps))
        temp = self.initial_temperature
        gamma = self.initial_gamma

        # Quantum-inspired annealing loop
        for step in range(self.num_sweeps):
            # Transverse field linearly decreases (simulating quantum tunneling freeze-out)
            gamma = self.initial_gamma * (1.0 - (step / self.num_sweeps))

            # Metropolis sweep with transverse quantum tunneling acceptance
            for _ in range(n):
                # Pick a random spin to flip
                flip_idx = random.randint(0, n - 1)
                candidate_state = current_state.copy()
                candidate_state[flip_idx] = 1 - candidate_state[flip_idx]

                candidate_energy = self.qubo_model.evaluate_energy(candidate_state, Q)
                delta_energy = candidate_energy - current_energy

                # Acceptance criterion:
                # If energy decreases (delta_energy < 0), accept immediately.
                # If energy increases, accept with probability combining thermal excitation
                # AND quantum tunneling through the transverse field Gamma:
                # P_accept = exp(-delta_energy / temp) + P_tunnel(gamma)
                if delta_energy < 0:
                    current_state = candidate_state
                    current_energy = candidate_energy
                else:
                    thermal_prob = math.exp(-delta_energy / max(1e-4, temp))
                    # Quantum tunneling term through energy barrier
                    tunneling_prob = 0.5 * math.exp(-math.sqrt(max(0.01, delta_energy)) / max(1e-4, gamma + 0.1))
                    accept_prob = min(1.0, thermal_prob + tunneling_prob)

                    if random.random() < accept_prob:
                        current_state = candidate_state
                        current_energy = candidate_energy

                # Track global best
                if current_energy < best_energy:
                    best_energy = current_energy
                    best_state = current_state.copy()

            temp *= decay
            if step % 5 == 0 or step == self.num_sweeps - 1:
                energy_trajectory.append(round(current_energy, 4))
                gamma_trajectory.append(round(gamma, 4))

        # Check all single-bit neighbors of best_state for local minimum guarantee
        for i in range(n):
            cand = best_state.copy()
            cand[i] = 1 - cand[i]
            cand_e = self.qubo_model.evaluate_energy(cand, Q)
            if cand_e < best_energy:
                best_energy = cand_e
                best_state = cand

        # Explainability & feature synergy
        explainability = self.qubo_model.calculate_explainability(
            optimal_state=best_state,
            signal_intensities=signal_intensities,
            Q=Q
        )

        # Convert to Ising spins (-1, +1)
        optimal_spins = [1 if x == 1 else -1 for x in best_state]

        # Calculate calibrated risk score (0.0 to 100.0)
        # Combine baseline raw maximum signal with QUBO threat energy
        max_raw_signal = max(signal_intensities.values()) if signal_intensities else 0.0
        threat_energy = explainability["total_qubo_threat_energy"]

        # Risk score calculation:
        # Base from max raw signal (up to 40 points)
        # QUBO threat energy (up to 60 points)
        base_risk = max_raw_signal * 40.0
        energy_risk = min(60.0, threat_energy * 3.5)
        raw_total_risk = base_risk + energy_risk

        # If critical signals are near 1.0, guarantee high threat score (BLOCK)
        if signal_intensities.get("hash_mismatch", 0.0) > 0.8:
            raw_total_risk = max(raw_total_risk, 88.0)
        if signal_intensities.get("certificate_chain", 0.0) > 0.8:
            raw_total_risk = max(raw_total_risk, 85.0)
        if signal_intensities.get("timestamp_drift", 0.0) > 0.85:
            raw_total_risk = max(raw_total_risk, 84.0)
        if signal_intensities.get("device_ip_reputation", 0.0) > 0.8:
            raw_total_risk = max(raw_total_risk, 82.0)
        if signal_intensities.get("key_usage_anomaly", 0.0) > 0.8:
            raw_total_risk = max(raw_total_risk, 85.0)

        risk_score = round(min(100.0, max(0.0, raw_total_risk)), 1)

        return {
            "optimal_binary_state": best_state.tolist(),
            "optimal_spins": optimal_spins,
            "min_qubo_energy": round(best_energy, 4),
            "risk_score": risk_score,
            "energy_trajectory": energy_trajectory,
            "gamma_trajectory": gamma_trajectory,
            "signals": self.qubo_model.signals,
            "explainability": explainability,
            "qubo_matrix": Q.round(3).tolist()
        }
