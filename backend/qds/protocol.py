"""
Teleportation-Based Quantum Digital Signature (QDS) Protocol Coordinator
Implements the multi-party signing session, state distribution, and projective verification.
"""

import time
import uuid
import random
import hashlib
from typing import Dict, Any, List, Tuple, Optional

from backend.config import DEFAULT_TOKEN_COUNT, DEFAULT_CHANNEL_NOISE, BASES
from backend.qds.quantum_state import QubitState
from backend.qds.teleportation import TeleportationSimulator

class QDSSigningSession:
    """
    Manages an active QDS signing session between Alice (Signer) and Bob (Verifier).
    Maintains session state, quantum states, teleportation logs, and verification records.
    """

    def __init__(
        self,
        message: str = "APPROVE_INFRASTRUCTURE_CLEARANCE",
        signer_id: str = "alice.signer@gov.in",
        verifier_id: str = "bob.verifier@finance.gov.in",
        token_count: int = DEFAULT_TOKEN_COUNT,
        channel_noise: float = DEFAULT_CHANNEL_NOISE,
        session_id: Optional[str] = None
    ):
        self.session_id = session_id or f"QDS-{uuid.uuid4().hex[:8].upper()}"
        self.created_at = time.time()
        self.message = message
        self.message_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()
        self.signer_id = signer_id
        self.verifier_id = verifier_id
        self.token_count = token_count
        self.channel_noise = channel_noise
        self.nonce = f"nonce-{uuid.uuid4().hex[:12]}"
        
        # Alice's secret key: List of dicts [{"index": k, "basis": "Z", "value": 0}, ...]
        self.alice_secret_key: List[Dict[str, Any]] = []
        # Alice's prepared quantum states: List of QubitState objects
        self.alice_quantum_states: List[QubitState] = []
        # Teleportation logs: classical bits, Bell outcomes, and Bob's received qubits
        self.teleportation_records: List[Dict[str, Any]] = []
        self.bob_received_qubits: List[QubitState] = []

        # Generate Alice's signing states upon initialization
        self._prepare_quantum_signing_states()

    def _prepare_quantum_signing_states(self):
        """Alice samples random Pauli bases (Z, X, Y) and binary values to create N quantum tokens."""
        self.alice_secret_key = []
        self.alice_quantum_states = []

        for k in range(self.token_count):
            basis = random.choice(BASES)  # Uniformly random among Z, X, Y
            val = random.randint(0, 1)    # 0 or 1
            state = QubitState.from_pauli_eigenstate(basis, val)
            
            self.alice_secret_key.append({
                "index": k,
                "basis": basis,
                "value": val
            })
            self.alice_quantum_states.append(state)

    def execute_teleportation(self, noise_override: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Teleports Alice's N quantum states to Bob across the quantum/classical link.
        Bob applies Pauli correction to reconstruct the quantum tokens.
        """
        noise = self.channel_noise if noise_override is None else noise_override
        self.teleportation_records = []
        self.bob_received_qubits = []

        for k, state in enumerate(self.alice_quantum_states):
            teleport_res = TeleportationSimulator.teleport_qubit(
                input_state=state,
                channel_noise_p=noise
            )
            self.teleportation_records.append({
                "index": k,
                "bell_outcome": teleport_res["bell_outcome"],
                "classical_bits": teleport_res["classical_bits"],
                "pauli_correction": teleport_res["pauli_correction"],
                "fidelity": teleport_res["fidelity"]
            })
            self.bob_received_qubits.append(teleport_res["reconstructed_qubit"])

        return self.teleportation_records

    def verify(
        self,
        claimed_key: Optional[List[Dict[str, Any]]] = None,
        bob_qubits_override: Optional[List[QubitState]] = None
    ) -> Dict[str, Any]:
        """
        Bob performs projective measurements on his received qubits in the announced bases.
        Calculates match/mismatch statistics and error rate.
        """
        key_to_verify = claimed_key if claimed_key is not None else self.alice_secret_key
        qubits_to_measure = bob_qubits_override if bob_qubits_override is not None else self.bob_received_qubits

        if not qubits_to_measure:
            # Auto-run teleportation if not yet executed
            self.execute_teleportation()
            qubits_to_measure = self.bob_received_qubits

        matches = 0
        mismatches = 0
        basis_stats = {"Z": {"match": 0, "mismatch": 0},
                       "X": {"match": 0, "mismatch": 0},
                       "Y": {"match": 0, "mismatch": 0}}

        detailed_outcomes = []

        for k in range(min(len(key_to_verify), len(qubits_to_measure))):
            expected_basis = key_to_verify[k]["basis"]
            expected_val = key_to_verify[k]["value"]

            # Bob measures in the basis specified by the disclosed key
            measured_val, prob, _ = qubits_to_measure[k].measure_projective(expected_basis)

            is_match = (measured_val == expected_val)
            if is_match:
                matches += 1
                basis_stats[expected_basis]["match"] += 1
            else:
                mismatches += 1
                basis_stats[expected_basis]["mismatch"] += 1

            if k < 20:  # Sample preview of first 20 tokens for UI inspection
                detailed_outcomes.append({
                    "token_index": k,
                    "basis": expected_basis,
                    "expected_val": expected_val,
                    "measured_val": measured_val,
                    "match": is_match
                })

        total = matches + mismatches
        error_rate = mismatches / max(1, total)

        return {
            "session_id": self.session_id,
            "total_measurements": total,
            "matches": matches,
            "mismatches": mismatches,
            "error_rate": round(error_rate, 4),
            "basis_stats": basis_stats,
            "preview_outcomes": detailed_outcomes
        }

