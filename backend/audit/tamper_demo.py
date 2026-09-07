"""
Forensic Tamper Detection & Integrity Verification Demonstration for QDS Audit Trail.
Demonstrates mathematical failure when an attacker or malicious insider attempts to modify
local audit records after Merkle root anchoring.
"""

import copy
import json
import time
from typing import Dict, Any, List, Tuple
from backend.audit.merkle_ledger import MerkleAuditLedger

class ForensicTamperDetector:
    """
    Forensic engine that audits a QDS Merkle hash-chain ledger against an anchored Merkle root.
    Identifies exact records that have suffered bit-level or structural tampering.
    """

    @staticmethod
    def create_baseline_ledger() -> Tuple[MerkleAuditLedger, str]:
        """
        Populates a fresh Merkle ledger with representative QDS events and returns
        the ledger along with the anchored Merkle root.
        """
        ledger = MerkleAuditLedger()

        # Event 0: Legitimate signing session
        ledger.append_qds_event(
            session_id="SESSION-2026-LEGIT-001",
            signer_id="alice.signer@gov.in",
            verifier_id="bob.verifier@finance.gov.in",
            message="TREASURY_TRANSFER_ORDER_001",
            token_count=200,
            mismatches=6,
            error_rate=0.030,
            threat_type="SAFE",
            action="ACCEPT",
            p_value=0.552,
            timestamp="2026-09-07T12:00:00Z"
        )

        # Event 1: Moderate channel manipulation alert
        ledger.append_qds_event(
            session_id="SESSION-2026-CHAN-002",
            signer_id="alice.signer@gov.in",
            verifier_id="bob.verifier@finance.gov.in",
            message="DEFENSE_TELEMETRY_PACKET_99",
            token_count=200,
            mismatches=29,
            error_rate=0.145,
            threat_type="CHANNEL_MANIPULATION",
            action="ALERT",
            p_value=1.42e-12,
            timestamp="2026-09-07T12:05:00Z"
        )

        # Event 2: Critical quantum intercept-resend forgery
        ledger.append_qds_event(
            session_id="SESSION-2026-FORGE-003",
            signer_id="alice.signer@gov.in",
            verifier_id="bob.verifier@finance.gov.in",
            message="FORGED_AIR_DEFENSE_AUTHORIZATION",
            token_count=200,
            mismatches=68,
            error_rate=0.340,
            threat_type="FORGERY",
            action="BLOCK",
            p_value=1.89e-45,
            timestamp="2026-09-07T12:10:00Z"
        )

        anchored_root = ledger.root_hash
        return ledger, anchored_root

    @classmethod
    def audit_ledger_integrity(
        cls,
        ledger_entries: List[Dict[str, Any]],
        anchored_merkle_root: str
    ) -> Dict[str, Any]:
        """
        Forensically verifies the integrity of an audit ledger:
        1. Recalculates canonical SHA-256 leaf hashes for each record.
        2. Validates hash-chain linkage (previous_hash pointer).
        3. Rebuilds Merkle tree and compares recalculated root to anchored root.
        """
        if not ledger_entries:
            return {"status": "EMPTY", "is_valid": True, "tampered_indices": []}

        recalculated_leaves = []
        tampered_indices = []
        hash_chain_violations = []

        expected_prev_hash = "0" * 64

        for idx, entry in enumerate(ledger_entries):
            # Check hash-chain pointer
            if entry.get("previous_hash") != expected_prev_hash:
                hash_chain_violations.append({
                    "record_index": idx,
                    "expected_previous_hash": expected_prev_hash,
                    "found_previous_hash": entry.get("previous_hash"),
                    "reason": "Broken hash-chain linkage"
                })

            # Recompute canonical leaf hash
            canonical_copy = {
                "index": entry["index"],
                "session_id": entry["session_id"],
                "signer_id": entry["signer_id"],
                "verifier_id": entry["verifier_id"],
                "message_hash": entry["message_hash"],
                "token_count": int(entry["token_count"]),
                "mismatches": int(entry["mismatches"]),
                "error_rate": float(entry["error_rate"]),
                "threat_type": entry["threat_type"],
                "action": entry["action"],
                "binomial_p_value": float(entry["binomial_p_value"]),
                "timestamp": entry["timestamp"],
                "previous_hash": entry["previous_hash"]
            }
            serialized = json.dumps(canonical_copy, sort_keys=True)
            recomputed_hash = MerkleAuditLedger.sha256_hex(serialized)
            recalculated_leaves.append(recomputed_hash)

            expected_prev_hash = recomputed_hash

        # Reconstruct Merkle root from recalculated leaves
        current_level = recalculated_leaves[:]
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = MerkleAuditLedger.hash_pair(left, right)
                next_level.append(parent)
            current_level = next_level

        recalculated_root = current_level[0] if current_level else ""
        root_matches = (recalculated_root == anchored_merkle_root)

        is_tamper_free = root_matches and (len(hash_chain_violations) == 0)

        return {
            "is_valid": is_tamper_free,
            "root_matches_anchor": root_matches,
            "anchored_merkle_root": anchored_merkle_root,
            "recalculated_merkle_root": recalculated_root,
            "hash_chain_violations": hash_chain_violations,
            "total_records_checked": len(ledger_entries),
            "forensic_verdict": "VERIFIED_AUTHENTIC" if is_tamper_free else "CRITICAL_EVIDENCE_INTEGRITY_BREACH"
        }

    @classmethod
    def execute_tamper_demonstration(cls, target_index: int = 2) -> Dict[str, Any]:
        """
        Executes an end-to-end tamper demonstration:
        1. Generates authentic ledger and anchors Merkle root.
        2. Clones the ledger and injects malicious edits into target record.
        3. Attempts forensic verification and Merkle inclusion proof.
        4. Returns side-by-side comparison for SOC display.
        """
        ledger, anchored_root = cls.create_baseline_ledger()
        original_record = copy.deepcopy(ledger.entries[target_index])
        original_leaf_hash = ledger.leaf_hashes[target_index]
        inclusion_proof = ledger.get_inclusion_proof(target_index)

        # Pre-tampering verification: should pass
        pre_audit = cls.audit_ledger_integrity(ledger.entries, anchored_root)
        pre_proof_valid = MerkleAuditLedger.verify_inclusion_proof(
            original_leaf_hash,
            inclusion_proof["proof_path"],
            anchored_root
        )

        # Inject malicious insider alteration:
        # Cover up a Forgery by changing threat_type to SAFE and mismatches from 68 to 2!
        tampered_entries = copy.deepcopy(ledger.entries)
        tampered_entries[target_index]["threat_type"] = "SAFE"
        tampered_entries[target_index]["action"] = "ACCEPT"
        tampered_entries[target_index]["mismatches"] = 2
        tampered_entries[target_index]["error_rate"] = 0.010
        tampered_entries[target_index]["binomial_p_value"] = 0.999

        # Post-tampering forensic audit
        post_audit = cls.audit_ledger_integrity(tampered_entries, anchored_root)

        # Recompute altered record's leaf hash
        tampered_serialized = json.dumps(tampered_entries[target_index], sort_keys=True)
        tampered_leaf_hash = MerkleAuditLedger.sha256_hex(tampered_serialized)

        # Attempt to verify the tampered leaf using the original inclusion proof
        tampered_proof_valid = MerkleAuditLedger.verify_inclusion_proof(
            tampered_leaf_hash,
            inclusion_proof["proof_path"],
            anchored_root
        )

        return {
            "demo_name": "Cryptographic Non-Repudiation & Tamper Evidence Verification",
            "target_record_index": target_index,
            "anchored_merkle_root": anchored_root,
            "original_record": {
                "session_id": original_record["session_id"],
                "threat_type": original_record["threat_type"],
                "action": original_record["action"],
                "mismatches": original_record["mismatches"],
                "error_rate": original_record["error_rate"],
                "leaf_hash": original_leaf_hash
            },
            "tampered_record": {
                "session_id": tampered_entries[target_index]["session_id"],
                "threat_type": tampered_entries[target_index]["threat_type"],
                "action": tampered_entries[target_index]["action"],
                "mismatches": tampered_entries[target_index]["mismatches"],
                "error_rate": tampered_entries[target_index]["error_rate"],
                "recalculated_leaf_hash": tampered_leaf_hash
            },
            "pre_tamper_verification": {
                "ledger_valid": pre_audit["is_valid"],
                "inclusion_proof_valid": pre_proof_valid,
                "verdict": pre_audit["forensic_verdict"]
            },
            "post_tamper_verification": {
                "ledger_valid": post_audit["is_valid"],
                "inclusion_proof_valid": tampered_proof_valid,
                "root_matches_anchor": post_audit["root_matches_anchor"],
                "recalculated_root": post_audit["recalculated_merkle_root"],
                "verdict": post_audit["forensic_verdict"]
            },
            "forensic_analysis": (
                f"Adversary modified session index {target_index} (mismatches 68->2, FORGERY->SAFE). "
                f"Recalculated leaf hash ({tampered_leaf_hash[:16]}...) does not match original ({original_leaf_hash[:16]}...). "
                f"Reconstructed Merkle root ({post_audit['recalculated_merkle_root'][:16]}...) diverges from anchored root "
                f"({anchored_root[:16]}...). Merkle inclusion proof evaluated to FALSE: TAMPERING DETECTED."
            )
        }


if __name__ == "__main__":
    demo = ForensicTamperDetector.execute_tamper_demonstration()
    print("=" * 80)
    print("QUETZALCOATL FORENSIC TAMPER DETECTION DEMO")
    print("=" * 80)
    print(f"Target Record: #{demo['target_record_index']}")
    print(f"Anchored Merkle Root: {demo['anchored_merkle_root']}")
    print("-" * 80)
    print("Original Leaf Hash: ", demo["original_record"]["leaf_hash"])
    print("Tampered Leaf Hash: ", demo["tampered_record"]["recalculated_leaf_hash"])
    print("-" * 80)
    print("Pre-Tamper Verification: ", demo["pre_tamper_verification"]["verdict"])
    print("Post-Tamper Verification:", demo["post_tamper_verification"]["verdict"])
    print(f"Proof Valid:             {demo['post_tamper_verification']['inclusion_proof_valid']}")
    print("-" * 80)
    print(demo["forensic_analysis"])
    print("=" * 80)

