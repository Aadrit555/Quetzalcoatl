"""
Signature Entropy & Structural Randomness Analyzer
Detects signature malleability, zero-fill padding attacks, and synthetic key forgeries.
"""

import math
from typing import Dict, Any, Tuple
from collections import Counter

class SignatureEntropyAnalyzer:
    """
    Computes information-theoretic entropy and structural distribution
    of cryptographic signatures to detect tampering, malleability, or synthetic keys.
    """
    
    @staticmethod
    def calculate_shannon_entropy(data: bytes) -> float:
        """Computes Shannon entropy in bits per byte (0.0 to 8.0)."""
        if not data:
            return 0.0
        
        counts = Counter(data)
        total = len(data)
        entropy = 0.0
        
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
            
        return entropy

    @classmethod
    def analyze_signature(cls, sig_bytes: bytes, expected_algo: str) -> Dict[str, Any]:
        """
        Analyzes the signature byte stream and returns an anomaly score and metrics.
        - Valid signatures (RSA, ECDSA, ML-DSA) exhibit high entropy (~7.6 - 8.0).
        - Forged, zero-padded, or replayed corrupt signatures exhibit low entropy or high repetition.
        """
        length = len(sig_bytes)
        if length == 0:
            return {
                "entropy": 0.0,
                "length": 0,
                "anomaly_score": 1.0,
                "reason": "Empty signature payload"
            }

        entropy = cls.calculate_shannon_entropy(sig_bytes)
        
        # Check repetitive byte sequences / zero blocks
        zero_count = sig_bytes.count(b'\x00')
        zero_ratio = zero_count / length
        ff_count = sig_bytes.count(b'\xff')
        ff_ratio = ff_count / length

        anomaly_score = 0.0
        flags = []

        # Expected entropy for true cryptographic output of 256-512 bytes is typically >= 6.8
        if entropy < 5.8:
            anomaly_score += 0.8
            flags.append(f"Severely degraded entropy ({entropy:.2f} < 5.8 bits/byte)")
        elif entropy < 6.6:
            anomaly_score += 0.35
            flags.append(f"Abnormally low entropy ({entropy:.2f} < 6.6 bits/byte)")

        # Zero padding attack or null-byte filling
        if zero_ratio > 0.20:
            anomaly_score += 0.5
            flags.append(f"Excessive null bytes ({zero_ratio*100:.1f}%)")

        if ff_ratio > 0.20:
            anomaly_score += 0.5
            flags.append(f"Excessive 0xFF fill bytes ({ff_ratio*100:.1f}%)")

        # Clamp anomaly score to [0.0, 1.0]
        anomaly_score = min(1.0, anomaly_score)

        return {
            "entropy": round(entropy, 3),
            "length": length,
            "zero_ratio": round(zero_ratio, 3),
            "anomaly_score": round(anomaly_score, 3),
            "flags": flags,
           # "is_anomalous": anomaly_score > 0.3
            "is_anomalous":anomaly_score > 0.3
        }
