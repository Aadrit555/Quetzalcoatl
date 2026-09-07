"""
Feature Extractor for Digital Signature Requests
Extracts 8 core security signals and normalizes them into continuous risk scores [0.0, 1.0].
"""

import time
import hashlib
import datetime
from typing import Dict, Any, Tuple, List
from backend.config import MAX_ALLOWED_TIMESTAMP_DRIFT_SEC
from backend.crypto.entropy import SignatureEntropyAnalyzer
from backend.crypto.cert_manager import CertificateManager

class FeatureExtractor:
    """Extracts and normalizes multi-dimensional security features from signing requests."""

    def __init__(self, cert_manager: CertificateManager):
        self.cert_manager = cert_manager
        self.signer_recent_timestamps: Dict[str, List[float]] = {}
        self.seen_nonces: set = set()

    def extract_features(
        self,
        request: Dict[str, Any],
        graph_eval: Dict[str, Any],
        raw_sig_bytes: bytes
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Extracts 8 continuous features in [0.0, 1.0] from request metadata and cryptographic payload.
        Returns (feature_dict, explanation_reasons).
        """
        now = time.time()
        explanations = []
        features = {}

        # 1. Timestamp Drift / Replay Signal
        req_timestamp = request.get("timestamp")
        nonce = request.get("nonce", "")
        drift_score = 0.0

        if nonce:
            if nonce in self.seen_nonces:
                drift_score = 1.0
                explanations.append(f"REPLAY ATTACK: Nonce '{nonce}' has been reused!")
            else:
                self.seen_nonces.add(nonce)

        if req_timestamp:
            try:
                # Accept ISO string or unix epoch
                if isinstance(req_timestamp, (int, float)):
                    req_time_sec = float(req_timestamp)
                else:
                    req_time_sec = datetime.datetime.fromisoformat(req_timestamp.replace('Z', '+00:00')).timestamp()

                drift = abs(now - req_time_sec)
                if drift > MAX_ALLOWED_TIMESTAMP_DRIFT_SEC:
                    # Scale from 0.4 up to 1.0 for large drift
                    drift_score = max(drift_score, min(1.0, 0.4 + (drift / 600.0)))
                    explanations.append(f"Timestamp drift exceeds threshold: {drift:.1f}s skew (max {MAX_ALLOWED_TIMESTAMP_DRIFT_SEC}s)")
            except Exception:
                drift_score = 0.8
                explanations.append("Malformed or unparseable timestamp format")

        features["timestamp_drift"] = round(min(1.0, drift_score), 3)

        # 2. Signer Velocity & Burst Activity
        signer_id = request.get("signer_id", "anonymous")
        timestamps = self.signer_recent_timestamps.setdefault(signer_id, [])
        # Keep timestamps from last 60 seconds
        timestamps = [t for t in timestamps if now - t < 60.0]
        timestamps.append(now)
        self.signer_recent_timestamps[signer_id] = timestamps

        velocity_score = 0.0
        # If more than 10 signings in 60s from single user, flag velocity
        if len(timestamps) > 15:
            velocity_score = 0.95
            explanations.append(f"High-frequency automated signing burst: {len(timestamps)} requests in last 60s")
        elif len(timestamps) > 5:
            velocity_score = 0.45
            explanations.append(f"Elevated signing velocity: {len(timestamps)} requests in last 60s")

        features["signer_velocity"] = round(velocity_score, 3)

        # 3. Device & IP Reputation (from Behavior Graph)
        graph_score = graph_eval.get("graph_anomaly_score", 0.0)
        for flag in graph_eval.get("flags", []):
            explanations.append(f"Graph Security Flag: {flag}")
        features["device_ip_reputation"] = round(min(1.0, graph_score), 3)

        # 4. Certificate Chain Integrity
        cert_pem = request.get("certificate_pem", "")
        cert_risk = 0.0
        if cert_pem:
            cert_val = self.cert_manager.validate_certificate_pem(cert_pem)
            cert_risk = cert_val.get("risk_contribution", 0.0) / 10.0
            for flag in cert_val.get("flags", []):
                explanations.append(f"Certificate Authority Flag: {flag}")
        else:
            cert_risk = 0.5
            explanations.append("No X.509 certificate provided with signature request")

        features["certificate_chain"] = round(min(1.0, cert_risk), 3)

        # 5. Hash Mismatch / Integrity Failure
        payload_data = request.get("payload_data", "").encode('utf-8')
        claimed_hash = request.get("payload_hash", "").lower()
        actual_hash = hashlib.sha256(payload_data).hexdigest().lower()

        hash_score = 0.0
        if claimed_hash and actual_hash != claimed_hash:
            hash_score = 1.0
            explanations.append(f"CRITICAL INTEGRITY FAILURE: Claimed hash {claimed_hash[:12]} does not match actual payload hash {actual_hash[:12]}")

        features["hash_mismatch"] = round(hash_score, 3)

        # 6. Signature Entropy & Structural Randomness
        algo = request.get("algorithm", "RSA-PSS")
        entropy_eval = SignatureEntropyAnalyzer.analyze_signature(raw_sig_bytes, algo)
        entropy_score = entropy_eval["anomaly_score"]
        for flag in entropy_eval.get("flags", []):
            explanations.append(f"Signature Structure Flag: {flag}")

        features["signature_entropy"] = round(entropy_score, 3)

        # 7. Key Usage Anomaly (sharing across identities)
        key_score = 0.0
        if any("STOLEN KEY" in flag for flag in graph_eval.get("flags", [])):
            key_score = 1.0
        features["key_usage_anomaly"] = round(key_score, 3)

        # 8. Algorithm Downgrade Risk
        downgrade_score = 0.0
        expected_policy = request.get("expected_security_policy", "STANDARD")
        if expected_policy == "POST_QUANTUM_REQUIRED" and not algo.startswith("ML-DSA") and not algo.startswith("SLH-DSA"):
            downgrade_score = 0.85
            explanations.append(f"Algorithm Downgrade Violation: Policy requires NIST PQC (ML-DSA), but received classical {algo}")
        elif "1024" in algo or "SHA1" in algo or "MD5" in algo:
            downgrade_score = 0.95
            explanations.append(f"Deprecated Weak Cryptographic Primitive: {algo}")

        features["algo_downgrade_risk"] = round(downgrade_score, 3)

        return features, explanations

