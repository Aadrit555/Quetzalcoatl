"""Unit tests for all 5 QDS attack simulations and threat classifications."""

from backend.qds.protocol import QDSSigningSession
from backend.detection.statistics import QuantumStatisticalEngine
from backend.detection.thresholds import QDSThresholdEngine
from backend.detection.classifier import QDSThreatClassifier

from backend.attacks.forgery import ForgeryAttackSimulator
from backend.attacks.impersonation import ImpersonationAttackSimulator
from backend.attacks.replay import ReplayAttackSimulator
from backend.attacks.channel_attack import ChannelAttackSimulator
from backend.attacks.unauthorized import UnauthorizedVerificationSimulator

def test_forgery_attack_detection():
    session = QDSSigningSession(token_count=200, channel_noise=0.03)
    thresholds = QDSThresholdEngine(verification_threshold=0.10, abort_threshold=0.20)
    classifier = QDSThreatClassifier(thresholds)

    # Execute Forgery Attack
    attack_res = ForgeryAttackSimulator.execute_intercept_resend_forgery(session)
    raw_verify = attack_res["verification_result"]

    # Intercept-resend forgery induces ~33% mismatch
    assert raw_verify["error_rate"] > 0.20

    stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
        total_measurements=raw_verify["total_measurements"],
        mismatches=raw_verify["mismatches"],
        expected_noise_p0=0.03,
        verification_threshold=0.10
    )
    context = {"is_valid_identity": True, "is_authorized_verifier": True}
    decision = classifier.classify_event(stats, context)

    assert decision["threat_type"] == "FORGERY"
    assert decision["action"] == "BLOCK"
    assert stats["binomial_p_value"] < 1e-6

def test_impersonation_attack_detection():
    session = QDSSigningSession(token_count=100)
    thresholds = QDSThresholdEngine()
    classifier = QDSThreatClassifier(thresholds)

    attack_res = ImpersonationAttackSimulator.execute_impersonation(session)
    raw_verify = attack_res["verification_result"]
    stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
        total_measurements=raw_verify["total_measurements"],
        mismatches=raw_verify["mismatches"],
        expected_noise_p0=0.03
    )

    decision = classifier.classify_event(stats, attack_res["session_context"])
    assert decision["threat_type"] == "IMPERSONATION"
    assert decision["action"] == "BLOCK"

def test_replay_attack_detection():
    session = QDSSigningSession(token_count=100)
    thresholds = QDSThresholdEngine()
    classifier = QDSThreatClassifier(thresholds)

    attack_res = ReplayAttackSimulator.execute_replay(session)
    raw_verify = attack_res["verification_result"]
    stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
        total_measurements=raw_verify["total_measurements"],
        mismatches=raw_verify["mismatches"],
        expected_noise_p0=0.03
    )

    decision = classifier.classify_event(stats, attack_res["session_context"])
    assert decision["threat_type"] == "REPLAY"
    assert decision["action"] == "BLOCK"

def test_channel_manipulation_detection():
    session = QDSSigningSession(token_count=300, channel_noise=0.03)
    thresholds = QDSThresholdEngine(verification_threshold=0.10, abort_threshold=0.20)
    classifier = QDSThreatClassifier(thresholds)

    # Injected disturbance 23% (depolarizing mismatch ~15.3%, exactly at midpoint between sv=10% and sa=20%)
    attack_res = ChannelAttackSimulator.execute_channel_disturbance(session, disturbance_level=0.23)
    raw_verify = attack_res["verification_result"]
    stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
        total_measurements=raw_verify["total_measurements"],
        mismatches=raw_verify["mismatches"],
        expected_noise_p0=0.03
    )

    decision = classifier.classify_event(stats, attack_res["session_context"])
    assert decision["threat_type"] == "CHANNEL_MANIPULATION"
    assert decision["action"] == "ALERT"

def test_unauthorized_verification_detection():
    session = QDSSigningSession(token_count=100)
    thresholds = QDSThresholdEngine()
    classifier = QDSThreatClassifier(thresholds)

    attack_res = UnauthorizedVerificationSimulator.execute_unauthorized_attempt(session)
    raw_verify = attack_res["verification_result"]
    stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
        total_measurements=raw_verify["total_measurements"],
        mismatches=raw_verify["mismatches"],
        expected_noise_p0=0.03
    )

    decision = classifier.classify_event(stats, attack_res["session_context"])
    assert decision["threat_type"] == "UNAUTHORIZED_VERIFICATION"
    assert decision["action"] == "BLOCK"
