"""
Quantum Channel Manipulation Simulator
Simulates active eavesdropping disturbance (depolarizing, phase-flip, bit-flip)
on the quantum optical channel connecting Alice and Bob.
"""

from typing import Dict, Any
from backend.qds.protocol import QDSSigningSession

class ChannelAttackSimulator:
    """Simulates physical quantum channel interference and eavesdropping disturbance."""

    @staticmethod
    def execute_channel_disturbance(
        session: QDSSigningSession,
        disturbance_level: float = 0.22,
        noise_type: str = "depolarizing"
    ) -> Dict[str, Any]:
        """
        Injects controlled decoherence / channel disturbance during qubit transit.
        Error rate rises above baseline sv but below full forgery threshold sa.
        """
        # Teleport with elevated channel noise
        session.execute_teleportation(noise_override=disturbance_level)
        verification_result = session.verify()

        context = {
            "is_valid_identity": True,
            "is_authorized_verifier": True,
            "is_nonce_reused": False,
            "is_session_expired": False,
            "channel_disturbance_p": disturbance_level,
            "noise_type": noise_type
        }

        return {
            "attack_type": "CHANNEL_MANIPULATION",
            "scenario": f"Quantum Optical Channel Disturbance ({noise_type.title()} p={disturbance_level*100:.1f}%)",
            "session_context": context,
            "verification_result": verification_result,
            "disturbance_level": disturbance_level,
            "explanation": (
                f"An eavesdropper or severe environmental perturbation introduced {disturbance_level*100:.1f}% "
                f"{noise_type} noise onto the quantum channel. The error rate exceeds the verification threshold "
                f"sv (10%), but remains below the full abort threshold sa (20%), triggering a specialized "
                f"CHANNEL_MANIPULATION alert for link recalibration."
            )
        }
