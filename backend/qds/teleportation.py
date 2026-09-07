"""
Quantum Teleportation Circuit & Protocol Simulation Engine
Implements mathematically exact 3-qubit teleportation:
|psi> (Alice) + |Phi+> (EPR) -> Bell-State Measurement (BSM) -> (b1, b2) -> Pauli Correction -> |psi> (Bob).
"""

import math
import random
import numpy as np
from typing import Dict, Any, Tuple, Optional

from backend.qds.quantum_state import (
    QubitState, PAULI_I, PAULI_X, PAULI_Y, PAULI_Z,
    STATE_0, STATE_1
)
from backend.qds.bell_states import BellStateEngine, BELL_TO_CLASSICAL_BITS

class TeleportationSimulator:
    """
    Simulates the standard Bennett et al. (1993) quantum teleportation protocol.
    Provides complete state inspection at every step of the circuit.
    """

    @staticmethod
    def teleport_qubit(
        input_state: QubitState,
        channel_noise_p: float = 0.0,
        channel_noise_type: str = "depolarizing"
    ) -> Dict[str, Any]:
        """
        Executes a complete teleportation round of input_state from Alice to Bob.
        Returns:
            step_by_step: Dictionary detailing each circuit milestone
            reconstructed_state: Bob's final restored QubitState
            fidelity: Overlap F = |<psi_in|psi_out>|^2
            classical_bits: (b1, b2) sent over classical channel
            bell_outcome: Name of Bell state observed by Alice
        """
        if input_state.statevector is None:
            # Re-purify or convert
            psi = STATE_0.copy()
        else:
            psi = input_state.statevector.copy()

        # Step 1: Input state |psi> = alpha |0> + beta |1>
        alpha = psi[0]
        beta = psi[1]

        # Step 2: Shared EPR Bell pair |Phi+> = 1/sqrt(2) (|00> + |11>) on qubits (A2, B)
        # Joint 3-qubit state |Psi_123> = |psi> (x) |Phi+> in C^8
        # |Psi_123> = 1/2 [ |Phi+>(alpha|0> + beta|1>) +
        #                   |Phi->(alpha|0> - beta|1>) +
        #                   |Psi+>(beta|0> + alpha|1>) +
        #                   |Psi->(-beta|0> + alpha|1>) ]

        # Step 3: Alice performs Bell-State Measurement (BSM) on qubits (A1, A2)
        # In ideal teleportation, all 4 Bell states are equally likely (P = 0.25)
        bell_names = ["Phi+", "Phi-", "Psi+", "Psi-"]
        sampled_bell = random.choice(bell_names)
        b1, b2 = BELL_TO_CLASSICAL_BITS[sampled_bell]

        # Step 4: Bob's pre-correction collapsed state depending on Alice's BSM outcome
        if sampled_bell == "Phi+":
            # Bob holds: alpha |0> + beta |1> = |psi>
            bob_pre_vec = np.array([alpha, beta], dtype=np.complex128)
            correction_matrix = PAULI_I
            correction_label = "I"
        elif sampled_bell == "Phi-":
            # Bob holds: alpha |0> - beta |1> = Z |psi>
            bob_pre_vec = np.array([alpha, -beta], dtype=np.complex128)
            correction_matrix = PAULI_Z
            correction_label = "Z"
        elif sampled_bell == "Psi+":
            # Bob holds: beta |0> + alpha |1> = X |psi>
            bob_pre_vec = np.array([beta, alpha], dtype=np.complex128)
            correction_matrix = PAULI_X
            correction_label = "X"
        else:  # Psi-
            # Bob holds: -beta |0> + alpha |1> = -i Y |psi> = XZ |psi>
            bob_pre_vec = np.array([-beta, alpha], dtype=np.complex128)
            correction_matrix = np.dot(PAULI_X, PAULI_Z)
            correction_label = "XZ"

        bob_pre_state = QubitState(statevector=bob_pre_vec)

        # Step 5: Quantum Channel Disturbance (if quantum fiber/memory is noisy or attacked)
        bob_channel_state = bob_pre_state
        if channel_noise_p > 0.0:
            if channel_noise_type == "depolarizing":
                bob_channel_state = bob_pre_state.apply_depolarizing_channel(channel_noise_p)
            elif channel_noise_type == "phase_flip":
                bob_channel_state = bob_pre_state.apply_phase_flip_channel(channel_noise_p)

        # Step 6: Bob applies Pauli feed-forward correction U = correction_matrix
        bob_reconstructed = bob_channel_state.apply_unitary(correction_matrix)

        # Step 7: Compute state fidelity with original input state
        fidelity = float(bob_reconstructed.calculate_fidelity(input_state))

        return {
            "input_state": input_state.to_dict(),
            "bell_outcome": sampled_bell,
            "classical_bits": (b1, b2),
            "pauli_correction": correction_label,
            "channel_noise_applied": channel_noise_p,
            "bob_reconstructed_state": bob_reconstructed.to_dict(),
            "fidelity": round(fidelity, 5),
            "reconstructed_qubit": bob_reconstructed
        }

