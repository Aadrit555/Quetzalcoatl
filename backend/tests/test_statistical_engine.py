"""Unit tests for the Mathematical & Statistical Detection Engine."""

import pytest
from backend.detection.statistics import QuantumStatisticalEngine
from backend.detection.thresholds import QDSThresholdEngine

def test_binomial_p_value_null_hypothesis():
    # When mismatches are consistent with noise (e.g. 6 out of 200 with p0 = 0.03)
    p_val_clean = QuantumStatisticalEngine.binomial_p_value(200, 6, expected_noise_p0=0.03)
    assert p_val_clean > 0.10  # Null hypothesis cannot be rejected

    # When mismatches are heavily elevated (e.g. 60 out of 200)
    p_val_attack = QuantumStatisticalEngine.binomial_p_value(200, 60, expected_noise_p0=0.03)
    assert p_val_attack < 1e-15  # Null hypothesis overwhelmingly rejected

def test_wilson_score_interval():
    low, high = QuantumStatisticalEngine.wilson_score_interval(100, 10, confidence_level=0.95)
    assert 0.0 < low < 0.10
    assert 0.10 < high < 0.25
    assert low < high

def test_hoeffding_forgery_bound():
    # If sv = 0.10 and expected attack error = 0.3333, with N = 200
    bound = QuantumStatisticalEngine.hoeffding_forgery_bound(
        total_measurements=200,
        verification_threshold=0.10,
        attacker_expected_error=0.3333
    )
    # exp(-2 * 200 * (0.2333)^2) = exp(-400 * 0.0544) = exp(-21.78) ~ 3.4e-10
    assert bound < 1e-8

def test_threshold_tradeoffs_far_frr():
    engine = QDSThresholdEngine(verification_threshold=0.10, abort_threshold=0.20)
    tradeoffs = engine.calculate_tradeoffs(token_count=200, baseline_noise_p0=0.03, attack_noise_p1=0.3333)

    # FRR should be very small
    assert tradeoffs["false_rejection_rate"] < 0.01
    # FAR under intercept-resend attack should be virtually zero
    assert tradeoffs["false_acceptance_rate"] < 1e-6

