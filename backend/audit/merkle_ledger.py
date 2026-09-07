"""
Tamper-Evident Merkle Hash Chain Audit Ledger for QDS
Maintains an immutable append-only ledger of QDS signing sessions and threat detections,
generates Merkle trees, and produces mathematical inclusion proofs for audit non-repudiation.
"""

import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple

class MerkleAuditLedger:
    """
    Cryptographic Merkle tree and hash-chain ledger that records all QDS events.
    Provides inclusion proofs and root integrity verification for forensic auditors.
    """

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []
        self.leaf_hashes: List[str] = []
        self.tree_levels: List[List[str]] = []
        self.root_hash: str = ""
        self.latest_block_hash: str = "0" * 64  # Genesis hash

    @staticmethod
    def sha256_hex(data: str) -> str:
        """Computes SHA-256 hash in hex string."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def hash_pair(left_hex: str, right_hex: str) -> str:
        """Combines and hashes two child nodes in the Merkle tree."""
        combined = left_hex + right_hex
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def append_qds_event(
        self,
        session_id: str,
        signer_id: str,
        verifier_id: str,
        message: str,
        token_count: int,
        mismatches: int,
        error_rate: float,
        threat_type: str,
        action: str,
        p_value: float,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Appends a new QDS event into the tamper-evident hash chain and Merkle tree.
        """
        event_index = len(self.entries)
        prev_hash = self.latest_block_hash

        canonical_record = {
            "index": event_index,
            "session_id": session_id,
            "signer_id": signer_id,
            "verifier_id": verifier_id,
            "message_hash": self.sha256_hex(message),
            "token_count": int(token_count),
            "mismatches": int(mismatches),
            "error_rate": float(error_rate),
            "threat_type": threat_type,
            "action": action,
            "binomial_p_value": float(p_value),
            "timestamp": timestamp,
            "previous_hash": prev_hash
        }

        # Deterministic JSON serialization for canonical hashing
        serialized = json.dumps(canonical_record, sort_keys=True)
        leaf_hash = self.sha256_hex(serialized)
        self.latest_block_hash = leaf_hash

        self.entries.append(canonical_record)
        self.leaf_hashes.append(leaf_hash)

        # Rebuild Merkle tree
        self._rebuild_tree()

        return {
            "index": event_index,
            "leaf_hash": leaf_hash,
            "merkle_root": self.root_hash,
            "previous_hash": prev_hash,
            "total_records": len(self.entries)
        }

    def _rebuild_tree(self):
        """Builds all levels of the binary Merkle tree from the leaf hashes."""
        if not self.leaf_hashes:
            self.root_hash = ""
            self.tree_levels = []
            return

        current_level = self.leaf_hashes[:]
        self.tree_levels = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = self.hash_pair(left, right)
                next_level.append(parent)
            self.tree_levels.append(next_level)
            current_level = next_level

        self.root_hash = self.tree_levels[-1][0]

    def get_inclusion_proof(self, index: int) -> Dict[str, Any]:
        """
        Generates a Merkle inclusion proof for the leaf at specified index.
        Returns sibling hashes and direction ('left' / 'right') up to the root.
        """
        if index < 0 or index >= len(self.leaf_hashes):
            raise IndexError("Audit ledger leaf index out of bounds")

        proof: List[Dict[str, str]] = []
        curr_idx = index

        for level in self.tree_levels[:-1]:
            is_right_child = (curr_idx % 2 == 1)
            sibling_idx = curr_idx - 1 if is_right_child else curr_idx + 1

            if sibling_idx < len(level):
                sibling_hash = level[sibling_idx]
            else:
                sibling_hash = level[curr_idx]

            proof.append({
                "sibling": sibling_hash,
                "position": "left" if is_right_child else "right"
            })
            curr_idx = curr_idx // 2

        return {
            "leaf_index": index,
            "leaf_hash": self.leaf_hashes[index],
            "merkle_root": self.root_hash,
            "proof_path": proof,
            "record": self.entries[index]
        }

    @classmethod
    def verify_inclusion_proof(
        cls,
        leaf_hash: str,
        proof_path: List[Dict[str, str]],
        expected_root: str
    ) -> bool:
        """
        Mathematically verifies that a leaf hash belongs to the Merkle tree with root expected_root.
        Computes upward hashes along the proof path.
        """
        current_hash = leaf_hash
        for step in proof_path:
            sibling = step["sibling"]
            position = step["position"]

            if position == "left":
                current_hash = cls.hash_pair(sibling, current_hash)
            else:
                current_hash = cls.hash_pair(current_hash, sibling)

        return current_hash.lower() == expected_root.lower()
