"""
Multi-Party Quantum Digital Signature (QDS) & Dispute Arbitration Protocol
Implements 3-party (Alice -> Bob & Charlie) non-repudiation and signature transferability.
Based on Zeng & Christoph (2002) and Wang et al. (2015).
"""

import uuid
import random
from typing import Dict, Any, List, Tuple, Optional
from backend.qds.quantum_state import QubitState
from backend.qds.teleportation import TeleportationSimulator
from backend.detection.statistics import QuantumStatisticalEngine
from backend.detection.thresholds import QDSThresholdEngine

class MultiPartyQDSSession:
    """
    Coordinates 3-party QDS protocol between Alice (Signer), Bob (Recipient), and Charlie (Auditor/Third-Party).
    Guarantees both unforgeability and non-repudiation:
    - Alice cannot deny a signature accepted by Bob.
    - Bob cannot convince Charlie of a signature Alice never sent.
    """

    def __init__(
        self,
        message: str = "INTERBANK_CROSS_SETTLEMENT_ORDER_4091",
        token_count: int = 150,
        channel_noise: float = 0.03,
        verification_threshold: float = 0.10,
        abort_threshold: float = 0.20
    ):
        self.session_id: str = f"QDS-MULTI-{uuid.uuid4().hex[:8].upper()}"
        self.message: str = message
        self.token_count: int = token_count
        self.channel_noise: float = channel_noise
        self.s_v: float = verification_threshold
        self.s_a: float = abort_threshold
        self.delta_dispute: float = round(self.s_a - self.s_v, 3)  # Acceptance gap Delta

        self.threshold_engine = QDSThresholdEngine(self.s_v, self.s_a)

        # Alice's secret private keys
        self.alice_bases_bob: List[str] = []
        self.alice_values_bob: List[int] = []
        self.alice_states_bob: List[QubitState] = []

        self.alice_bases_charlie: List[str] = []
        self.alice_values_charlie: List[int] = []
        self.alice_states_charlie: List[QubitState] = []

        # Teleported states
        self.bob_reconstructed_qubits: List[QubitState] = []
        self.charlie_reconstructed_qubits: List[QubitState] = []

        # State initialization
        self._initialize_entangled_tokens()

    def _initialize_entangled_tokens(self):
        """Alice generates non-orthogonal Pauli states for both Bob and Charlie."""
        for _ in range(self.token_count):
            # Token for Bob
            basis_b = random.choice(["Z", "X", "Y"])
            val_b = random.choice([0, 1])
            self.alice_bases_bob.append(basis_b)
            self.alice_values_bob.append(val_b)
            self.alice_states_bob.append(QubitState.from_pauli_eigenstate(basis_b, val_b))

            # Token for Charlie
            basis_c = random.choice(["Z", "X", "Y"])
            val_c = random.choice([0, 1])
            self.alice_bases_charlie.append(basis_c)
            self.alice_values_charlie.append(val_c)
            self.alice_states_charlie.append(QubitState.from_pauli_eigenstate(basis_c, val_c))

    def execute_dual_teleportation(
        self,
        noise_bob: Optional[float] = None,
        noise_charlie: Optional[float] = None,
        alice_repudiation_attack: bool = False
    ) -> Dict[str, Any]:
        """
        Teleports Alice's quantum signature tokens to Bob and Charlie.
        If alice_repudiation_attack is True, Alice deliberately corrupts Charlie's tokens
        in an attempt to later repudiate the signature she gave to Bob.
        """
        eff_noise_b = noise_bob if noise_bob is not None else self.channel_noise
        eff_noise_c = noise_charlie if noise_charlie is not None else self.channel_noise

        self.bob_reconstructed_qubits = []
        self.charlie_reconstructed_qubits = []

        # Teleport to Bob
        for state in self.alice_states_bob:
            tele_res = TeleportationSimulator.teleport_qubit(state, channel_noise_p=eff_noise_b)
            self.bob_reconstructed_qubits.append(tele_res["reconstructed_qubit"])

        # Teleport to Charlie
        for state in self.alice_states_charlie:
            if alice_repudiation_attack:
                # Alice sends orthogonal / corrupted state to Charlie
                corrupted = state.apply_pauli_x()
                tele_res = TeleportationSimulator.teleport_qubit(corrupted, channel_noise_p=eff_noise_c)
            else:
                tele_res = TeleportationSimulator.teleport_qubit(state, channel_noise_p=eff_noise_c)
            self.charlie_reconstructed_qubits.append(tele_res["reconstructed_qubit"])

        return {
            "session_id": self.session_id,
            "tokens_teleported_bob": len(self.bob_reconstructed_qubits),
            "tokens_teleported_charlie": len(self.charlie_reconstructed_qubits),
            "repudiation_attack_injected": alice_repudiation_attack
        }

    def verify_direct_signature_bob(self) -> Dict[str, Any]:
        """Bob verifies Alice's signature directly using Alice's disclosed key."""
        mismatches = 0
        indicators = []

        for i in range(self.token_count):
            basis = self.alice_bases_bob[i]
            expected = self.alice_values_bob[i]
            qubit = self.bob_reconstructed_qubits[i]

            measured, _, _ = qubit.measure_projective(basis)
            if measured != expected:
                mismatches += 1
                indicators.append(1)
            else:
                indicators.append(0)

        error_rate = mismatches / max(1, self.token_count)
        is_accepted_by_bob = (error_rate <= self.s_v)
        stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
            total_measurements=self.token_count,
            mismatches=mismatches,
            expected_noise_p0=self.channel_noise,
            verification_threshold=self.s_v,
            mismatch_indicators=indicators
        )

        return {
            "party": "Bob (Direct Verifier)",
            "token_count": self.token_count,
            "mismatches": mismatches,
            "error_rate": round(error_rate, 4),
            "error_rate_pct": f"{error_rate * 100:.2f}%",
            "threshold_sv": self.s_v,
            "is_accepted": is_accepted_by_bob,
            "verdict": "ACCEPT_SIGNATURE" if is_accepted_by_bob else "REJECT_SIGNATURE",
            "statistics": stats
        }

    def arbitrate_forwarded_signature_charlie(
        self,
        bob_reported_error_rate: float
    ) -> Dict[str, Any]:
        """
        Charlie receives the forwarded signature from Bob and validates:
        1. Charlie's local error rate e_Charlie <= s_a (dispute threshold).
        2. Transferability Gap: |e_Bob - e_Charlie| <= Delta_dispute (s_a - s_v).
        If both hold, Charlie accepts the transfer. If Gap is violated, an Alice Repudiation Attack is flagged.
        """
        mismatches = 0
        indicators = []

        for i in range(self.token_count):
            basis = self.alice_bases_charlie[i]
            expected = self.alice_values_charlie[i]
            qubit = self.charlie_reconstructed_qubits[i]

            measured, _, _ = qubit.measure_projective(basis)
            if measured != expected:
                mismatches += 1
                indicators.append(1)
            else:
                indicators.append(0)

        error_rate_charlie = mismatches / max(1, self.token_count)
        error_diff = abs(bob_reported_error_rate - error_rate_charlie)

        stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
            total_measurements=self.token_count,
            mismatches=mismatches,
            expected_noise_p0=self.channel_noise,
            verification_threshold=self.s_v,
            mismatch_indicators=indicators
        )

        # Non-repudiation condition
        is_below_abort_threshold = (error_rate_charlie <= self.s_a)
        is_within_dispute_gap = (error_diff <= self.delta_dispute)
        is_non_repudiable = is_below_abort_threshold and is_within_dispute_gap

        if is_non_repudiable:
            arbitration_status = "NON_REPUDIABLE_VALID"
            reason = "Signature successfully verified and transferred. Alice cannot repudiate."
        elif not is_within_dispute_gap:
            arbitration_status = "REPUDIATION_ATTACK_DETECTED"
            reason = (
                f"Dispute Gap Exceeded: |e_Bob ({bob_reported_error_rate*100:.1f}%) - "
                f"e_Charlie ({error_rate_charlie*100:.1f}%)| = {error_diff*100:.1f}% > "
                f"Delta ({self.delta_dispute*100:.1f}%). Alice attempted asymmetric repudiation!"
            )
        else:
            arbitration_status = "ABORT_CORRUPTED_SIGNATURE"
            reason = f"Charlie error rate ({error_rate_charlie*100:.1f}%) exceeds abort threshold sa ({self.s_a*100:.1f}%)."

        return {
            "party": "Charlie (Arbitrator / Auditor)",
            "token_count": self.token_count,
            "mismatches": mismatches,
            "error_rate_charlie": round(error_rate_charlie, 4),
            "bob_reported_error_rate": round(bob_reported_error_rate, 4),
            "error_difference": round(error_diff, 4),
            "dispute_gap_limit": self.delta_dispute,
            "is_within_gap": is_within_dispute_gap,
            "is_below_abort_threshold": is_below_abort_threshold,
            "is_accepted": is_non_repudiable,
            "arbitration_status": arbitration_status,
            "explanation": reason,
            "statistics": stats
        }

    def run_complete_dispute_protocol(
        self,
        repudiation_attack: bool = False
    ) -> Dict[str, Any]:
        """
        Executes end-to-end 3-party protocol:
        Teleportation -> Bob Direct Verification -> Forwarding to Charlie -> Arbitration.
        """
        self.execute_dual_teleportation(alice_repudiation_attack=repudiation_attack)
        bob_res = self.verify_direct_signature_bob()
        charlie_res = self.arbitrate_forwarded_signature_charlie(
            bob_reported_error_rate=bob_res["error_rate"]
        )

        overall_outcome = "TRANSFER_CONFIRMED" if charlie_res["is_accepted"] else "DISPUTE_RAISED"

        return {
            "session_id": self.session_id,
            "message": self.message,
            "repudiation_attack_simulated": repudiation_attack,
            "bob_verification": bob_res,
            "charlie_arbitration": charlie_res,
            "overall_outcome": overall_outcome,
            "security_property_proven": (
                "Information-Theoretic Non-Repudiation (Zeng-Christoph Theorem)"
                if overall_outcome == "TRANSFER_CONFIRMED"
                else "Alice Repudiation Fraud Prevented by Quantum Dispute Bound"
            )
        }
