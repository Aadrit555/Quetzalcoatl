"""
Mathematical & Statistical Inference Engine for QDS Threat Detection
Strictly Non-ML: Uses exact Binomial tests, Wilson score confidence intervals,
and Hoeffding bounds on forgery probability.
"""

import math
from typing import Dict, Any, Tuple, List, Optional
from scipy.stats import binom

class QuantumStatisticalEngine:
    """
    Computes rigorous statistical metrics from quantum measurement mismatch counts.
    Distinguishes benign physical channel noise from adversarial perturbations.
    """

    @staticmethod
    def binomial_p_value(total_measurements: int, mismatches: int, expected_noise_p0: float) -> float:
        """
        Calculates exact one-tailed Binomial test p-value:
        P(X >= M | N, p0) = sum_{k=M}^N binom(N, k) * p0^k * (1 - p0)^(N - k)
        Null Hypothesis H0: Mismatches arise purely from legitimate channel noise p0.
        """
        if total_measurements <= 0:
            return 1.0
        if mismatches <= 0:
            return 1.0
        if mismatches > total_measurements:
            mismatches = total_measurements

        # Survival function sf = 1 - cdf(M - 1)
        p_val = float(binom.sf(mismatches - 1, total_measurements, expected_noise_p0))
        return max(0.0, min(1.0, p_val))

    @staticmethod
    def wilson_score_interval(
        total_measurements: int,
        mismatches: int,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        Computes the Wilson Score confidence interval for the true error rate p.
        Robust for small sample sizes and error rates near 0.
        """
        if total_measurements <= 0:
            return 0.0, 1.0

        n = float(total_measurements)
        p_hat = float(mismatches) / n

        # Standard normal quantile z (1.96 for 95% confidence)
        if abs(confidence_level - 0.95) < 1e-4:
            z = 1.95996
        elif abs(confidence_level - 0.99) < 1e-4:
            z = 2.57583
        elif abs(confidence_level - 0.90) < 1e-4:
            z = 1.64485
        else:
            from scipy.stats import norm
            z = float(norm.ppf(1.0 - (1.0 - confidence_level) / 2.0))

        denominator = 1.0 + (z**2 / n)
        center = (p_hat + (z**2 / (2.0 * n))) / denominator
        spread = (z / denominator) * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z**2 / (4.0 * n**2)))

        lower = max(0.0, center - spread)
        upper = min(1.0, center + spread)
        return round(lower, 4), round(upper, 4)

    @staticmethod
    def hoeffding_forgery_bound(
        total_measurements: int,
        verification_threshold: float,
        attacker_expected_error: float = 0.3333
    ) -> float:
        """
        Computes Hoeffding's inequality upper bound on forgery escaping detection:
        P(e_observed <= s_v | p_attack) <= exp(-2 * N * (p_attack - s_v)^2)
        Valid whenever verification_threshold < attacker_expected_error.
        """
        if total_measurements <= 0:
            return 1.0

        epsilon = attacker_expected_error - verification_threshold
        if epsilon <= 0:
            return 1.0  # Threshold too high; no theoretical guarantee

        bound = math.exp(-2.0 * total_measurements * (epsilon ** 2))
        return min(1.0, bound)

    @staticmethod
    def calculate_z_score(
        total_measurements: int,
        mismatches: int,
        expected_noise_p0: float
    ) -> float:
        """Computes standardized deviation Z = (p_hat - p0) / sqrt(p0 * (1 - p0) / N)."""
        if total_measurements <= 0:
            return 0.0
        n = float(total_measurements)
        p_hat = mismatches / n
        std_err = math.sqrt(expected_noise_p0 * (1.0 - expected_noise_p0) / n)
        if std_err < 1e-12:
            return 0.0
        return round((p_hat - expected_noise_p0) / std_err, 2)

    @staticmethod
    def kullback_leibler_divergence(p_observed: float, p_null: float = 0.03) -> float:
        """
        Computes Bernoulli relative entropy (Kullback-Leibler divergence) D_KL(Q || P)
        between empirical error distribution Q ~ Ber(q) and null noise distribution P ~ Ber(p):
        D_KL(Q || P) = q * ln(q / p) + (1 - q) * ln((1 - q) / (1 - p))
        Measures information deviation in nats.
        """
        q = max(1e-7, min(1.0 - 1e-7, float(p_observed)))
        p = max(1e-7, min(1.0 - 1e-7, float(p_null)))

        term1 = q * math.log(q / p)
        term2 = (1.0 - q) * math.log((1.0 - q) / (1.0 - p))
        d_kl = term1 + term2
        return max(0.0, round(d_kl, 5))

    @classmethod
    def wald_sprt(
        cls,
        mismatch_indicators: Optional[List[int]] = None,
        total_measurements: int = 200,
        mismatches: int = 6,
        p0: float = 0.03,
        p1: float = 0.20,
        alpha: float = 0.001,
        beta: float = 0.01
    ) -> Dict[str, Any]:
        """
        Wald's Sequential Probability Ratio Test (SPRT).
        Enables early-stopping decision on whether quantum measurement stream
        originates from benign channel noise H0 (p = p0) or active attack H1 (p = p1).

        Decision boundaries:
          A = ln((1 - beta) / alpha)  (Upper boundary -> Reject H0: Attack Confirmed)
          B = ln(beta / (1 - alpha))  (Lower boundary -> Accept H0: Nominal Noise)
        """
        if mismatch_indicators is None:
            if total_measurements <= 0:
                indicators: List[int] = []
            else:
                indicators = [0] * total_measurements
                if mismatches > 0:
                    step = max(1.0, total_measurements / mismatches)
                    for m_idx in range(min(mismatches, total_measurements)):
                        target_pos = min(total_measurements - 1, int(m_idx * step))
                        indicators[target_pos] = 1
        else:
            indicators = mismatch_indicators
            total_measurements = len(indicators)
            mismatches = sum(indicators)

        if total_measurements == 0:
            return {
                "decision": "INSUFFICIENT_DATA",
                "stopped_at_qubit": 0,
                "total_qubits": 0,
                "qubits_saved": 0,
                "qubits_saved_pct": "0.0%",
                "log_likelihood_ratio": 0.0,
                "upper_bound_A": 0.0,
                "lower_bound_B": 0.0
            }

        p0 = max(1e-5, min(0.49, p0))
        p1 = max(p0 + 1e-4, min(0.99, p1))
        alpha = max(1e-6, min(0.1, alpha))
        beta = max(1e-6, min(0.1, beta))

        A = math.log((1.0 - beta) / alpha)
        B = math.log(beta / (1.0 - alpha))

        log_ratio_1 = math.log(p1 / p0)
        log_ratio_0 = math.log((1.0 - p1) / (1.0 - p0))

        cumulative_llr = 0.0
        stopped_at = total_measurements
        decision = "CONTINUE_TESTING"
        trajectory = []

        for idx, bit in enumerate(indicators, start=1):
            term = log_ratio_1 if bit == 1 else log_ratio_0
            cumulative_llr += term

            if idx <= 50 or idx % 5 == 0 or idx == total_measurements:
                trajectory.append({"qubit": idx, "llr": round(cumulative_llr, 3)})

            if cumulative_llr >= A:
                decision = "REJECT_H0_ATTACK_CONFIRMED"
                stopped_at = idx
                break
            elif cumulative_llr <= B:
                decision = "ACCEPT_H0_SAFE"
                stopped_at = idx
                break

        if decision == "CONTINUE_TESTING":
            decision = "ACCEPT_H0_SAFE" if cumulative_llr < 0 else "REJECT_H0_ATTACK_CONFIRMED"

        qubits_saved = total_measurements - stopped_at
        qubits_saved_pct = (qubits_saved / total_measurements) * 100.0

        return {
            "decision": decision,
            "stopped_at_qubit": stopped_at,
            "total_qubits": total_measurements,
            "qubits_saved": qubits_saved,
            "qubits_saved_pct": f"{qubits_saved_pct:.1f}%",
            "log_likelihood_ratio": round(cumulative_llr, 3),
            "upper_bound_A": round(A, 3),
            "lower_bound_B": round(B, 3),
            "trajectory_sample": trajectory
        }

    @classmethod
    def evaluate_measurement_statistics(
        cls,
        total_measurements: int,
        mismatches: int,
        expected_noise_p0: float = 0.03,
        verification_threshold: float = 0.10,
        alpha_significance: float = 0.001,
        mismatch_indicators: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete statistical evaluation pipeline for QDS measurement results.
        Returns all mathematical indicators, confidence bounds, KL divergence, and SPRT early stopping.
        """
        error_rate = mismatches / max(1, total_measurements)
        p_val = cls.binomial_p_value(total_measurements, mismatches, expected_noise_p0)
        ci_low, ci_high = cls.wilson_score_interval(total_measurements, mismatches, 0.95)
        forgery_bound = cls.hoeffding_forgery_bound(total_measurements, verification_threshold)
        z_score = cls.calculate_z_score(total_measurements, mismatches, expected_noise_p0)
        kl_div = cls.kullback_leibler_divergence(error_rate, expected_noise_p0)
        sprt_res = cls.wald_sprt(
            mismatch_indicators=mismatch_indicators,
            total_measurements=total_measurements,
            mismatches=mismatches,
            p0=expected_noise_p0,
            p1=verification_threshold * 2.0,
            alpha=alpha_significance
        )

        is_statistically_significant = (p_val < alpha_significance)

        return {
            "total_measurements": total_measurements,
            "mismatches": mismatches,
            "error_rate": round(error_rate, 4),
            "error_rate_pct": f"{error_rate * 100:.2f}%",
            "expected_noise_rate": round(expected_noise_p0, 4),
            "binomial_p_value": p_val,
            "binomial_p_value_formatted": f"{p_val:.3e}" if p_val < 0.001 else f"{p_val:.4f}",
            "alpha_significance": alpha_significance,
            "is_statistically_significant_anomaly": is_statistically_significant,
            "wilson_ci_95": [ci_low, ci_high],
            "hoeffding_forgery_probability_bound": forgery_bound,
            "hoeffding_forgery_bound_formatted": f"{forgery_bound:.3e}" if forgery_bound < 0.001 else f"{forgery_bound:.4f}",
            "z_score_deviation": z_score,
            "kullback_leibler_divergence_nats": kl_div,
            "sprt_early_stopping": sprt_res
        }


