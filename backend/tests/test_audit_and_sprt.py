"""
Unit Tests for Advanced QDS Modules:
- Wald's SPRT (Sequential Probability Ratio Test) early-stopping detection
- Kullback-Leibler (KL) relative entropy divergence
- Forensic tamper detection and Merkle proof integrity breach
- Multi-Party QDS dispute arbitration and non-repudiation (Alice -> Bob & Charlie)
"""

import pytest
from backend.detection.statistics import QuantumStatisticalEngine
from backend.audit.tamper_demo import ForensicTamperDetector
from backend.qds.multi_verifier import MultiPartyQDSSession

def test_wald_sprt_early_stopping_attack():
    """Verify that an attack stream triggers early stopping and saves qubits."""
    total_tokens = 200
    mismatches = 70  # ~35% error rate (forgery)
    res = QuantumStatisticalEngine.wald_sprt(
        total_measurements=total_tokens,
        mismatches=mismatches,
        p0=0.03,
        p1=0.20,
        alpha=0.001,
        beta=0.01
    )
    assert res["decision"] == "REJECT_H0_ATTACK_CONFIRMED"
    assert res["stopped_at_qubit"] < total_tokens
    assert res["qubits_saved"] > 50
    assert float(res["qubits_saved_pct"].replace("%", "")) > 25.0

def test_wald_sprt_early_stopping_legitimate():
    """Verify that a legitimate low-noise stream accepts H0 early."""
    total_tokens = 200
    mismatches = 3  # 1.5% error rate
    res = QuantumStatisticalEngine.wald_sprt(
        total_measurements=total_tokens,
        mismatches=mismatches,
        p0=0.03,
        p1=0.20,
        alpha=0.001,
        beta=0.01
    )
    assert res["decision"] == "ACCEPT_H0_SAFE"
    assert res["stopped_at_qubit"] < total_tokens
    assert res["qubits_saved"] > 0

def test_kullback_leibler_divergence():
    """Verify KL divergence properties."""
    # Zero divergence when distributions match
    div_identical = QuantumStatisticalEngine.kullback_leibler_divergence(0.03, 0.03)
    assert div_identical < 1e-4

    # High divergence under attack
    div_forgery = QuantumStatisticalEngine.kullback_leibler_divergence(0.34, 0.03)
    assert div_forgery > 0.30  # Substantial information distance

    # Moderate divergence under channel disturbance
    div_channel = QuantumStatisticalEngine.kullback_leibler_divergence(0.14, 0.03)
    assert 0.05 < div_channel < div_forgery

def test_forensic_tamper_detection_demo():
    """Verify that any modification of an anchored record causes proof and root failure."""
    demo = ForensicTamperDetector.execute_tamper_demonstration(target_index=2)
    assert demo["pre_tamper_verification"]["ledger_valid"] is True
    assert demo["pre_tamper_verification"]["inclusion_proof_valid"] is True
    assert demo["pre_tamper_verification"]["verdict"] == "VERIFIED_AUTHENTIC"

    # Post-tamper must fail
    assert demo["post_tamper_verification"]["ledger_valid"] is False
    assert demo["post_tamper_verification"]["inclusion_proof_valid"] is False
    assert demo["post_tamper_verification"]["root_matches_anchor"] is False
    assert demo["post_tamper_verification"]["verdict"] == "CRITICAL_EVIDENCE_INTEGRITY_BREACH"

def test_multi_party_legitimate_transfer():
    """Verify that legitimate Alice -> Bob -> Charlie session passes non-repudiation."""
    session = MultiPartyQDSSession(token_count=100, channel_noise=0.02)
    result = session.run_complete_dispute_protocol(repudiation_attack=False)

    assert result["overall_outcome"] == "TRANSFER_CONFIRMED"
    assert result["bob_verification"]["is_accepted"] is True
    assert result["charlie_arbitration"]["is_accepted"] is True
    assert result["charlie_arbitration"]["arbitration_status"] == "NON_REPUDIABLE_VALID"
    assert result["charlie_arbitration"]["is_within_gap"] is True

def test_multi_party_repudiation_attack_blocked():
    """Verify that if Alice attempts to repudiate, Charlie detects dispute gap violation."""
    session = MultiPartyQDSSession(token_count=100, channel_noise=0.02)
    result = session.run_complete_dispute_protocol(repudiation_attack=True)

    assert result["overall_outcome"] == "DISPUTE_RAISED"
    assert result["charlie_arbitration"]["arbitration_status"] == "REPUDIATION_ATTACK_DETECTED"
    assert result["charlie_arbitration"]["is_accepted"] is False
    assert result["charlie_arbitration"]["is_within_gap"] is False

