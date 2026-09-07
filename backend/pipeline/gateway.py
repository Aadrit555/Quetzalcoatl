"""
SIH Security Gateway Pipeline
Ingests, cryptographically verifies, scores via Quantum-Inspired Annealing,
enforces Zero-Trust policy decisions, and commits to the Merkle Audit Ledger.
"""

import time
import uuid
import base64
import hashlib
import datetime
from typing import Dict, Any, List, Optional

from backend.config import RISK_THRESHOLD_ALLOW, RISK_THRESHOLD_BLOCK
from backend.crypto.classical import ClassicalVerifier
from backend.crypto.pqc import PQCVerifier
from backend.crypto.cert_manager import CertificateManager
from backend.graph.behavior_graph import SignerBehaviorGraph
from backend.quantum.annealer import QuantumInspiredAnnealer
from backend.audit.merkle_ledger import MerkleAuditLedger
from backend.pipeline.feature_extractor import FeatureExtractor

class SecurityGateway:
    """
    Central API Gateway & SIEM Threat Detection Engine.
    Implements the Quantum-Inspired Cyber Threat Detection for Digital Signature Security.
    """

    def __init__(self):
        self.cert_manager = CertificateManager()
        self.behavior_graph = SignerBehaviorGraph()
        self.annealer = QuantumInspiredAnnealer(num_sweeps=150)
        self.merkle_ledger = MerkleAuditLedger()
        self.feature_extractor = FeatureExtractor(self.cert_manager)

        # Pre-seed some demo keys and certificates
        self._seed_demo_data()

    def _seed_demo_data(self):
        """Generates real cryptographic credentials for demonstrations."""
        # Legitimate Gov Root & Officer Key
        self.gov_priv, self.gov_cert, self.gov_serial = self.cert_manager.create_self_signed_cert(
            common_name="National E-Governance Root CA 2026",
            is_ca=True
        )
        self.officer_priv, self.officer_cert, self.officer_serial = self.cert_manager.create_self_signed_cert(
            common_name="Dr. Rajesh Kumar (Digital Identity Authority)",
            issuer_name="National E-Governance Root CA 2026"
        )
        # Compromised / Revoked Cert
        self.revoked_priv, self.revoked_cert, self.revoked_serial = self.cert_manager.create_self_signed_cert(
            common_name="Former Contractor Key (Compromised)",
            issuer_name="National E-Governance Root CA 2026"
        )
        self.cert_manager.revoke_certificate(self.revoked_serial, reason="Suspected Private Key Leak via DarkWeb")

        # PQC ML-DSA Keypair
        self.pqc_sk, self.pqc_pk = PQCVerifier.generate_mldsa_mock_keypair("ML-DSA-44")

    def process_signing_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the end-to-end detection pipeline:
        1. Parse request envelope
        2. Evaluate Signer Behavior Graph (impossible travel, novel device)
        3. Cryptographic Verification (Classical / PQC / Hybrid)
        4. Extract 8 security features
        5. Solve QUBO Hamiltonian via Quantum-Inspired Annealing
        6. Determine Policy Action (ALLOW, REVIEW, BLOCK)
        7. Commit event to Tamper-Evident Merkle Hash Chain
        """
        start_time = time.perf_counter()
        event_id = request.get("event_id", f"sig-{uuid.uuid4().hex[:12]}")
        signer_id = request.get("signer_id", "unknown-signer")
        algorithm = request.get("algorithm", "RSA-PSS")
        payload_data = request.get("payload_data", "")
        payload_bytes = payload_data.encode('utf-8') if isinstance(payload_data, str) else payload_data
        claimed_hash = request.get("payload_hash", hashlib.sha256(payload_bytes).hexdigest())

        # Decode signature
        raw_sig_b64 = request.get("signature_b64", "")
        try:
            raw_sig_bytes = base64.b64decode(raw_sig_b64)
        except Exception:
            raw_sig_bytes = b""

        # 1. Behavior Graph Analysis
        device_fp = request.get("device_fingerprint", "dev-unknown")
        ip_addr = request.get("ip_address", "127.0.0.1")
        geo = request.get("geo_location", {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi", "country": "IN"})
        cert_serial = request.get("cert_serial", "unknown-serial")
        ca_name = request.get("ca_name", "National-Root-CA")

        graph_eval = self.behavior_graph.record_and_evaluate(
            signer_id=signer_id,
            device_fingerprint=device_fp,
            ip_address=ip_addr,
            geo_location=geo,
            cert_serial=cert_serial,
            ca_name=ca_name
        )

        # 2. Cryptographic Verification
        crypto_result = {"valid": False, "details": "Unverified"}
        pub_key_pem = request.get("public_key_pem", "")

        if algorithm.startswith("ML-DSA") or algorithm.startswith("SLH-DSA"):
            pqc_pk_b64 = request.get("pqc_public_key_b64", "")
            crypto_result = PQCVerifier.verify_mldsa(
                pk_b64=pqc_pk_b64,
                sig_b64=raw_sig_b64,
                message=payload_bytes,
                variant=algorithm if algorithm.startswith("ML-DSA") else "ML-DSA-44"
            )
        elif pub_key_pem and raw_sig_bytes:
            crypto_result = ClassicalVerifier.verify_signature(
                public_key_pem=pub_key_pem.encode('utf-8') if isinstance(pub_key_pem, str) else pub_key_pem,
                signature=raw_sig_bytes,
                data=payload_bytes,
                algorithm=algorithm
            )
        else:
            crypto_result = {"valid": False, "details": "Missing public key or signature bytes"}

        # 3. Extract Features
        features, explanations = self.feature_extractor.extract_features(
            request=request,
            graph_eval=graph_eval,
            raw_sig_bytes=raw_sig_bytes
        )

        # If cryptographic verification outright failed, reinforce hash_mismatch / signature_entropy
        if not crypto_result.get("valid", False):
            features["hash_mismatch"] = max(features["hash_mismatch"], 0.9)
            features["signature_entropy"] = max(features["signature_entropy"], 0.75)
            explanations.append(f"Cryptographic Verification Failed: {crypto_result.get('details', 'Invalid signature')}")

        # 4. Quantum-Inspired Annealing Threat Correlation
        qubo_result = self.annealer.solve(signal_intensities=features)
        risk_score = qubo_result["risk_score"]
        qubo_energy = qubo_result["min_qubo_energy"]
        active_threats = qubo_result["explainability"]["active_threat_features"]

        # 5. Policy Engine Decision
        if risk_score >= RISK_THRESHOLD_BLOCK:
            action = "BLOCK"
            action_desc = "High-Risk Threat Detected: Signature request rejected at API Gateway"
        elif risk_score >= RISK_THRESHOLD_ALLOW:
            action = "REVIEW"
            action_desc = "Moderate Risk / Anomaly Detected: Flagged for SOC Analyst Review"
        else:
            action = "ALLOW"
            action_desc = "Cryptographically Verified & Low Risk: Forwarded to application backend"

        # 6. Commit to Merkle Audit Ledger
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_record = self.merkle_ledger.append_event(
            event_id=event_id,
            signer_id=signer_id,
            action=action,
            risk_score=risk_score,
            qubo_energy=qubo_energy,
            payload_hash=claimed_hash,
            signals_triggered=active_threats,
            timestamp=now_iso
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "event_id": event_id,
            "timestamp": now_iso,
            "action": action,
            "action_desc": action_desc,
            "risk_score": risk_score,
            "decision_thresholds": {
                "allow_below": RISK_THRESHOLD_ALLOW,
                "block_above": RISK_THRESHOLD_BLOCK
            },
            "crypto_verification": crypto_result,
            "qubo_optimization": {
                "min_energy": qubo_energy,
                "optimal_spins": qubo_result["optimal_spins"],
                "active_threat_signals": active_threats,
                "energy_trajectory": qubo_result["energy_trajectory"],
                "gamma_trajectory": qubo_result["gamma_trajectory"],
                "qubo_matrix": qubo_result["qubo_matrix"],
                "signals": qubo_result["signals"]
            },
            "signal_features": features,
            "explainability": {
                "reasons": explanations,
                "feature_contributions": qubo_result["explainability"]["feature_contributions"],
                "synergies_detected": qubo_result["explainability"]["synergies_detected"]
            },
            "graph_behavior": {
                "impossible_travel": graph_eval.get("is_impossible_travel", False),
                "distance_km": graph_eval.get("distance_km", 0),
                "velocity_kmh": graph_eval.get("velocity_kmh", 0),
                "flags": graph_eval.get("flags", [])
            },
            "audit_proof": {
                "leaf_index": audit_record["index"],
                "leaf_hash": audit_record["leaf_hash"],
                "merkle_root": audit_record["merkle_root"],
                "total_records": audit_record["total_records"]
            },
            "performance": {
                "latency_ms": elapsed_ms,
                "solver_type": "Quantum-Inspired Simulated Annealing (Transverse Field SQA)"
            }
        }

    def generate_scenario_request(self, scenario_id: str) -> Dict[str, Any]:
        """
        Generates realistic synthetic attack and legitimate requests for live demonstration.
        """
        now = time.time()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if scenario_id == "legitimate_esign":
            # Scenario 1: Clean E-Governance Approval (Low Risk -> ALLOW)
            doc = "APPROVAL_ORDER_REF_2026_9812: Grant of Public Infrastructure Clearance"
            doc_bytes = doc.encode('utf-8')
            sig = ClassicalVerifier.sign_data(self.officer_priv, doc_bytes, "RSA-PSS")
            
            return {
                "event_id": f"legit-{uuid.uuid4().hex[:8]}",
                "signer_id": "dr.rajesh.kumar@gov.in",
                "algorithm": "RSA-PSS",
                "payload_data": doc,
                "payload_hash": hashlib.sha256(doc_bytes).hexdigest(),
                "signature_b64": base64.b64encode(sig).decode('ascii'),
                "public_key_pem": self.officer_cert.decode('utf-8'),
                "certificate_pem": self.officer_cert.decode('utf-8'),
                "cert_serial": self.officer_serial,
                "ca_name": "National E-Governance Root CA 2026",
                "device_fingerprint": "gov-laptop-delhi-sec01",
                "ip_address": "164.100.24.12",  # NIC Government IP
                "geo_location": {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi", "country": "IN"},
                "timestamp": now_iso,
                "nonce": f"nonce-{uuid.uuid4().hex[:12]}",
                "scenario_title": "Legitimate Citizen E-Sign Approval",
                "scenario_desc": "Valid RSA-PSS signature from trusted NIC IP, valid certificate, normal velocity."
            }

        elif scenario_id == "replay_attack":
            # Scenario 2: Replay Attack (Old timestamp + Reused Nonce + Rogue Proxy -> BLOCK)
            # Baseline treasury location in New Delhi
            self.behavior_graph.signer_last_location["treasury.officer@finance.gov.in"] = {
                "lat": 28.6139, "lon": 77.2090, "city": "New Delhi", "country": "IN",
                "ip": "164.100.24.50", "timestamp": now - 3600.0
            }

            doc = "TREASURY_DISBURSEMENT_AUTH: Transfer 5,000,000 INR to Vendor Account 4019"
            doc_bytes = doc.encode('utf-8')
            sig = ClassicalVerifier.sign_data(self.officer_priv, doc_bytes, "RSA-PSS")
            
            replayed_nonce = "fixed-replay-nonce-9999"
            # Pre-register nonce in feature extractor
            self.feature_extractor.seen_nonces.add(replayed_nonce)
            past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=45)).isoformat()

            return {
                "event_id": f"replay-{uuid.uuid4().hex[:8]}",
                "signer_id": "treasury.officer@finance.gov.in",
                "algorithm": "RSA-PSS",
                "payload_data": doc,
                "payload_hash": hashlib.sha256(doc_bytes).hexdigest(),
                "signature_b64": base64.b64encode(sig).decode('ascii'),
                "public_key_pem": self.officer_cert.decode('utf-8'),
                "certificate_pem": self.officer_cert.decode('utf-8'),
                "cert_serial": self.officer_serial,
                "ca_name": "National E-Governance Root CA 2026",
                "device_fingerprint": "unfamiliar-cloud-proxy-99",
                "ip_address": "194.26.29.11",
                "geo_location": {"lat": 50.4501, "lon": 30.5234, "city": "Kyiv", "country": "UA"},
                "timestamp": past_time,
                "nonce": replayed_nonce,
                "scenario_title": "Replay Attack (Reused Nonce & Stale Timestamp)",
                "scenario_desc": "Previously intercepted valid disbursement signature replayed from remote proxy."
            }

        elif scenario_id == "impossible_travel":
            # Scenario 3: Stolen Private Key with Impossible Travel
            # First prime last location in Mumbai
            self.behavior_graph.signer_last_location["director.admin@gov.in"] = {
                "lat": 19.0760, "lon": 72.8777, "city": "Mumbai", "country": "IN",
                "ip": "49.36.12.80", "timestamp": now - 300.0  # 5 minutes ago!
            }

            doc = "SECRET_DEFENSE_CLEARANCE: Procurement Authorization Document #710"
            doc_bytes = doc.encode('utf-8')
            sig = ClassicalVerifier.sign_data(self.officer_priv, doc_bytes, "RSA-PSS")

            return {
                "event_id": f"travel-{uuid.uuid4().hex[:8]}",
                "signer_id": "director.admin@gov.in",
                "algorithm": "RSA-PSS",
                "payload_data": doc,
                "payload_hash": hashlib.sha256(doc_bytes).hexdigest(),
                "signature_b64": base64.b64encode(sig).decode('ascii'),
                "public_key_pem": self.officer_cert.decode('utf-8'),
                "certificate_pem": self.officer_cert.decode('utf-8'),
                "cert_serial": self.officer_serial,
                "ca_name": "National E-Governance Root CA 2026",
                "device_fingerprint": "kali-linux-adversary-box",
                "ip_address": "185.220.101.5",  # Known Tor exit node range
                "geo_location": {"lat": 55.7558, "lon": 37.6173, "city": "Moscow", "country": "RU"},
                "timestamp": now_iso,
                "nonce": f"nonce-{uuid.uuid4().hex[:12]}",
                "scenario_title": "Stolen Key / Impossible Travel Anomaly",
                "scenario_desc": "Signer authenticated from Mumbai 5 mins ago; new signing request arrives from Moscow (4,500+ km away)."
            }

        elif scenario_id == "revoked_certificate":
            # Scenario 4: Compromised & Revoked Certificate
            doc = "PERSONNEL_PROMOTION_ORDER: Batch 2026 Confirmation"
            doc_bytes = doc.encode('utf-8')
            sig = ClassicalVerifier.sign_data(self.revoked_priv, doc_bytes, "RSA-PSS")

            return {
                "event_id": f"revoked-{uuid.uuid4().hex[:8]}",
                "signer_id": "contractor.ex@partner.org",
                "algorithm": "RSA-PSS",
                "payload_data": doc,
                "payload_hash": hashlib.sha256(doc_bytes).hexdigest(),
                "signature_b64": base64.b64encode(sig).decode('ascii'),
                "public_key_pem": self.revoked_cert.decode('utf-8'),
                "certificate_pem": self.revoked_cert.decode('utf-8'),
                "cert_serial": self.revoked_serial,
                "ca_name": "National E-Governance Root CA 2026",
                "device_fingerprint": "contractor-home-pc",
                "ip_address": "115.112.44.8",
                "geo_location": {"lat": 12.9716, "lon": 77.5946, "city": "Bengaluru", "country": "IN"},
                "timestamp": now_iso,
                "nonce": f"nonce-{uuid.uuid4().hex[:12]}",
                "scenario_title": "Revoked X.509 Certificate via Stolen Key",
                "scenario_desc": "Signer attempts approval with a certificate revoked on CRL due to darkweb key leak."
            }

        elif scenario_id == "pqc_lattice_tamper":
            # Scenario 5: NIST FIPS 204 (ML-DSA) Post-Quantum Signature with Bit-Flip Tampering
            doc = "CRITICAL_GRID_CONTROL: Substation 400kV SCADA Firmware Update v4.1"
            doc_bytes = doc.encode('utf-8')
            # Legitimate signature
            real_sig_b64 = PQCVerifier.sign_mldsa(self.pqc_sk, doc_bytes, "ML-DSA-44")
            
            # Attacker alters 8 bytes in lattice commitment
            raw_sig = bytearray(base64.b64decode(real_sig_b64))
            for i in range(10, 18):
                raw_sig[i] ^= 0xAA  # Bit-flip attack / malleable perturbation
            tampered_sig_b64 = base64.b64encode(bytes(raw_sig)).decode('ascii')

            return {
                "event_id": f"pqc-tamper-{uuid.uuid4().hex[:8]}",
                "signer_id": "grid.scada.root@powergrid.in",
                "algorithm": "ML-DSA-44",
                "payload_data": doc,
                "payload_hash": hashlib.sha256(doc_bytes).hexdigest(),
                "signature_b64": tampered_sig_b64,
                "pqc_public_key_b64": self.pqc_pk,
                "certificate_pem": self.officer_cert.decode('utf-8'),
                "cert_serial": self.officer_serial,
                "ca_name": "National Critical Infrastructure CA",
                "device_fingerprint": "scada-mgmt-terminal-04",
                "ip_address": "10.200.4.19",
                "geo_location": {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi", "country": "IN"},
                "timestamp": now_iso,
                "nonce": f"nonce-{uuid.uuid4().hex[:12]}",
                "scenario_title": "Post-Quantum (ML-DSA) Lattice Malleability Attack",
                "scenario_desc": "NIST FIPS 204 ML-DSA lattice signature intercepted and perturbed with bit-flips."
            }

        elif scenario_id == "pqc_valid":
            # Scenario 6: Valid NIST FIPS 204 (ML-DSA) Post-Quantum Signature (Clean)
            doc = "CRITICAL_GRID_CONTROL: Substation 400kV SCADA Firmware Update v4.1"
            doc_bytes = doc.encode('utf-8')
            clean_sig_b64 = PQCVerifier.sign_mldsa(self.pqc_sk, doc_bytes, "ML-DSA-44")

            return {
                "event_id": f"pqc-valid-{uuid.uuid4().hex[:8]}",
                "signer_id": "grid.scada.root@powergrid.in",
                "algorithm": "ML-DSA-44",
                "payload_data": doc,
                "payload_hash": hashlib.sha256(doc_bytes).hexdigest(),
                "signature_b64": clean_sig_b64,
                "pqc_public_key_b64": self.pqc_pk,
                "certificate_pem": self.officer_cert.decode('utf-8'),
                "cert_serial": self.officer_serial,
                "ca_name": "National Critical Infrastructure CA",
                "device_fingerprint": "scada-mgmt-terminal-04",
                "ip_address": "10.200.4.19",
                "geo_location": {"lat": 28.6139, "lon": 77.2090, "city": "New Delhi", "country": "IN"},
                "timestamp": now_iso,
                "nonce": f"nonce-{uuid.uuid4().hex[:12]}",
                "scenario_title": "Valid Post-Quantum (NIST ML-DSA) Signing",
                "scenario_desc": "Authentic NIST FIPS 204 ML-DSA lattice signature protecting national critical infrastructure."
            }

        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

    def list_scenarios(self) -> List[Dict[str, str]]:
        """Returns catalog of pre-built demonstration scenarios."""
        return [
            {
                "id": "legitimate_esign",
                "title": "Legitimate Citizen E-Sign Approval",
                "type": "NORMAL",
                "expected": "ALLOW",
                "description": "Standard citizen/officer approval with valid RSA-PSS, trusted IP, low velocity."
            },
            {
                "id": "pqc_valid",
                "title": "Valid Post-Quantum ML-DSA Signing",
                "type": "NORMAL_PQC",
                "expected": "ALLOW",
                "description": "NIST FIPS 204 ML-DSA lattice digital signature for next-gen quantum resistance."
            },
            {
                "id": "replay_attack",
                "title": "Replay Attack (Reused Nonce & Time Skew)",
                "type": "ATTACK",
                "expected": "BLOCK",
                "description": "Captured valid treasury authorization replayed with 45m time skew and duplicate nonce."
            },
            {
                "id": "impossible_travel",
                "title": "Stolen Key / Impossible Geo-Velocity",
                "type": "ATTACK",
                "expected": "BLOCK",
                "description": "Director key authenticated from Mumbai, then signs defense document from Moscow 5 mins later."
            },
            {
                "id": "revoked_certificate",
                "title": "Compromised Certificate on Revocation List",
                "type": "ATTACK",
                "expected": "BLOCK",
                "description": "Signature generated using an X.509 private key flagged as leaked on darkweb."
            },
            {
                "id": "pqc_lattice_tamper",
                "title": "PQC Lattice Bit-Flip Tampering Attack",
                "type": "ATTACK",
                "expected": "BLOCK",
                "description": "ML-DSA post-quantum signature intercepted in transit with corrupted lattice commitments."
            }
        ]
