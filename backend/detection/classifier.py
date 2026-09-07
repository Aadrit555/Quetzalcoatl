"""
Rule-Based Explainable QDS Threat Classifier
Strictly Non-ML: Combines quantum statistical evidence with protocol-layer session states
to classify threats and assign security decisions (ACCEPT / ALERT / BLOCK).
"""

from typing import Dict, Any, List
from backend.detection.statistics import QuantumStatisticalEngine
from backend.detection.thresholds import QDSThresholdEngine

class QDSThreatClassifier:
    """
    Classifies cybersecurity threats against the QDS protocol using explicit
    mathematical evidence and protocol state verification.
    """

    def __init__(self, threshold_engine: QDSThresholdEngine):
        self.thresholds = threshold_engine

    def classify_event(
        self,
        stats: Dict[str, Any],
        session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates statistical and protocol indicators to classify threat type.
        """
        error_rate = stats["error_rate"]
        p_val = stats["binomial_p_value"]
        is_stat_sig = stats["is_statistically_significant_anomaly"]
        sv = self.thresholds.sv
        sa = self.thresholds.sa

        # Protocol layer context
        is_authorized_verifier = session_context.get("is_authorized_verifier", True)
        is_valid_identity = session_context.get("is_valid_identity", True)
        is_nonce_reused = session_context.get("is_nonce_reused", False)
        is_session_expired = session_context.get("is_session_expired", False)
        is_entanglement_depleted = session_context.get("is_entanglement_depleted", False)

        threat_type = "SAFE"
        action = "ACCEPT"
        reasons: List[str] = []
        evidence_checklist: List[Dict[str, Any]] = []

        # 1. Check Protocol / Authorization Breaches first (Classical Zero-Trust Boundary)
        if not is_authorized_verifier:
            threat_type = "UNAUTHORIZED_VERIFICATION"
            action = "BLOCK"
            reasons.append(
                f"Unauthorized verifier '{session_context.get('requesting_party', 'unknown')}' "
                f"attempted to access quantum signature tokens without entitlement credentials."
            )
            evidence_checklist.append({"indicator": "Verifier Authorization", "status": "FAIL", "detail": "Missing access role"})

        elif is_nonce_reused or is_session_expired or is_entanglement_depleted:
            threat_type = "REPLAY"
            action = "BLOCK"
            if is_nonce_reused:
                reasons.append(f"REPLAY ATTACK: Session nonce '{session_context.get('nonce', '')}' has been previously consumed.")
            if is_session_expired:
                reasons.append(f"REPLAY ATTACK: Session timestamp exceeds maximum lifetime (> 300s).")
            if is_entanglement_depleted:
                reasons.append("REPLAY ATTACK: Target Bell pairs were previously collapsed by an earlier verification session.")
            evidence_checklist.append({"indicator": "Protocol Session Freshness", "status": "FAIL", "detail": "Replay / Stale token"})

        elif not is_valid_identity:
            threat_type = "IMPERSONATION"
            action = "BLOCK"
            reasons.append(
                f"IMPERSONATION ATTACK: Signer claimed identity '{session_context.get('claimed_signer', '')}' "
                f"does not match pre-shared entanglement registry credentials."
            )
            evidence_checklist.append({"indicator": "Identity Authentication", "status": "FAIL", "detail": "Invalid signer binding"})

        # 2. Check Quantum Statistical Disturbance (Quantum Physical-Layer Evidence)
        else:
            if error_rate >= sa:
                threat_type = "FORGERY"
                action = "BLOCK"
                reasons.append(
                    f"FORGERY DETECTED: Observed mismatch rate ({error_rate*100:.1f}%) exceeds the abort threshold sa ({sa*100:.1f}%)."
                )
                reasons.append(
                    f"Statistical test rejects null hypothesis H0 (benign channel noise) with exact Binomial p-value = {p_val:.3e}."
                )
                reasons.append(
                    "State disturbance is consistent with an adversary attempting to forge non-orthogonal quantum states without private basis knowledge."
                )
                evidence_checklist.append({"indicator": "Quantum Verification Threshold", "status": "FAIL", "detail": f"e={error_rate*100:.1f}% >= sa={sa*100:.1f}%"})
                evidence_checklist.append({"indicator": "Binomial Hypothesis Test", "status": "FAIL", "detail": f"p-val={p_val:.3e} < alpha"})

            elif error_rate >= sv:
                threat_type = "CHANNEL_MANIPULATION"
                action = "ALERT"
                reasons.append(
                    f"QUANTUM CHANNEL MANIPULATION: Error rate ({error_rate*100:.1f}%) exceeds verification threshold sv ({sv*100:.1f}%), but remains below abort threshold sa ({sa*100:.1f}%)."
                )
                reasons.append(
                    f"Statistically significant quantum state disturbance detected (p-value = {p_val:.3e})."
                )
                reasons.append(
                    "Indicates active channel perturbation, eavesdropping probe (e.g. beam-splitting or weak intercept), or severe fiber decoherence."
                )
                evidence_checklist.append({"indicator": "Quantum Verification Threshold", "status": "WARN", "detail": f"sv < e < sa"})
                evidence_checklist.append({"indicator": "Channel Perturbation", "status": "ALERT", "detail": f"Decoherence detected"})

            elif error_rate > stats["expected_noise_rate"] * 1.5:
                threat_type = "NORMAL_NOISE"
                action = "ACCEPT"
                reasons.append(
                    f"Signature accepted. Minor physical noise observed ({error_rate*100:.1f}%), within acceptable tolerance (sv = {sv*100:.1f}%)."
                )
                evidence_checklist.append({"indicator": "Verification Status", "status": "PASS", "detail": f"e={error_rate*100:.1f}% <= sv"})

            else:
                threat_type = "SAFE"
                action = "ACCEPT"
                reasons.append(
                    f"Signature cryptographically verified. Mismatch rate ({error_rate*100:.1f}%) is well within expected channel noise baseline ({stats['expected_noise_rate']*100:.1f}%)."
                )
                evidence_checklist.append({"indicator": "Quantum Verification Status", "status": "PASS", "detail": "All checks authentic"})

        return {
            "threat_type": threat_type,
            "action": action,
            "reasons": reasons,
            "evidence_checklist": evidence_checklist,
            "error_rate": error_rate,
            "threshold_sv": sv,
            "threshold_sa": sa,
            "statistical_significance": is_stat_sig
        }
