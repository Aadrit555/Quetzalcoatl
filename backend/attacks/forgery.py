"""
QDS Forgery Attack Simulator
Simulates Eve attempting to forge a signature on a message Alice did not sign.
Eve performs an Intercept-and-Resend attack or injects random quantum states.
Due to quantum non-cloning and conjugate basis complementarity, Eve induces ~33.3% mismatch rate.
"""

import random
from typing import Dict, Any, List
from backend.config import BASES
from backend.qds.quantum_state import QubitState
from backend.qds.protocol import QDSSigningSession

class ForgeryAttackSimulator:
    """
    Executes a realistic quantum forgery attack against a QDS session.
    """

    @staticmethod
    def execute_intercept_resend_forgery(
        session: QDSSigningSession,
        forged_message: str = "FORGED_TREASURY_TRANSFER_INR_50M"
    ) -> Dict[str, Any]:
        """
        Eve intercepts the qubits during teleportation/transit, measures them in a randomly guessed
        basis theta_E in {Z, X, Y}, and resends the collapsed state to Bob.
        """
        eve_qubits: List[QubitState] = []
        eve_measurements = []

        # Alice teleports her true states
        session.execute_teleportation()
        bob_intercepted_qubits = session.bob_received_qubits

        for k in range(len(bob_intercepted_qubits)):
            # Eve does not know Alice's basis; Eve randomly guesses
            eve_guessed_basis = random.choice(BASES)
            val, prob, collapsed_state = bob_intercepted_qubits[k].measure_projective(eve_guessed_basis)

            eve_qubits.append(collapsed_state)
            if k < 10:
                eve_measurements.append({
                    "token_index": k,
                    "eve_guessed_basis": eve_guessed_basis,
                    "eve_measured_val": val
                })

        # Bob receives the states disturbed by Eve's measurements
        verification_result = session.verify(bob_qubits_override=eve_qubits)

        return {
            "attack_type": "FORGERY",
            "scenario": "Intercept-Resend Forgery on Quantum Channel",
            "forged_message": forged_message,
            "verification_result": verification_result,
            "eve_sample_measurements": eve_measurements,
            "theoretical_expected_error": 0.3333 + session.channel_noise,
            "explanation": (
                "Eve does not know Alice's private basis sequence. When Eve measures in a conjugate basis "
                "(which happens with probability 2/3), the quantum state irreversibly collapses into Eve's basis. "
                "When Bob subsequently measures in Alice's basis, Bob obtains a random result (50% error on those tokens), "
                "leading to a predictable overall mismatch rate of ~33.3%."
            )
        }

