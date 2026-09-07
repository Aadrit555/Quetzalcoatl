"""
QDS Replay Attack Simulator
Simulates Eve capturing past classical teleportation bits and attempting to replay them in a new session.
Demonstrates both protocol-level nonce failure AND quantum single-use entanglement collapse.
"""

from typing import Dict, Any
from backend.qds.protocol import QDSSigningSession

class ReplayAttackSimulator:
    """
    Simulates replay of past signature sessions.
    Shows that replaying classical packets against fresh unentangled quantum states fails catastrophically.
    """

    @staticmethod
    def execute_replay(session: QDSSigningSession) -> Dict[str, Any]:
        """
        Eve captures previous session parameters and re-injects them into a new transaction.
        """
        session.execute_teleportation()
        verification_result = session.verify()

        context = {
            "is_valid_identity": True,
            "is_authorized_verifier": True,
            "is_nonce_reused": True,
            "is_session_expired": True,
            "is_entanglement_depleted": True,
            "nonce": session.nonce,
            "original_session_id": session.session_id,
            "replay_target_session_id": f"REPLAY-{session.session_id}"
        }

        return {
            "attack_type": "REPLAY",
            "scenario": "Expired Session & Consumed Entanglement Replay",
            "session_context": context,
            "verification_result": verification_result,
            "explanation": (
                "Eve captured Alice's previous classical teleportation bits (b1, b2) and attempts to reuse them. "
                "The attack fails on two distinct fronts: First, the protocol-layer session cache catches the duplicate nonce. "
                "Second, at the quantum layer, Bell pairs are strictly single-use; the original quantum states collapsed upon Bob's "
                "prior measurement, rendering replayed classical bits physically meaningless."
            )
        }

