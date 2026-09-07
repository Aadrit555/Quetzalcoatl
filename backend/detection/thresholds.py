"""
Configurable Dual-Threshold Engine for QDS Threat Detection
Implements verification threshold sv, abort threshold sa,
and computes theoretical False Acceptance Rate (FAR) and False Rejection Rate (FRR).
"""

from typing import Dict, Any
from scipy.stats import binom
from backend.config import DEFAULT_VERIFICATION_THRESHOLD, DEFAULT_ABORT_THRESHOLD

class QDSThresholdEngine:
    """
    Manages dual-threshold policy (sv, sa) and calculates operational security tradeoffs.
    """

    def __init__(
        self,
        verification_threshold: float = DEFAULT_VERIFICATION_THRESHOLD,
        abort_threshold: float = DEFAULT_ABORT_THRESHOLD
    ):
        if not (0.0 <= verification_threshold < abort_threshold <= 1.0):
            raise ValueError(f"Invalid thresholds: must satisfy 0 <= sv < sa <= 1 (got sv={verification_threshold}, sa={abort_threshold}).")
        self.sv = verification_threshold
        self.sa = abort_threshold

    def evaluate_error_rate(self, error_rate: float) -> str:
        """
        Categorizes error rate:
        - error_rate <= sv => PASS_VERIFICATION
        - sv < error_rate < sa => SUSPICIOUS_CHANNEL
        - error_rate >= sa => ABORT_FORGERY
        """
        if error_rate <= self.sv:
            return "PASS_VERIFICATION"
        elif error_rate < self.sa:
            return "SUSPICIOUS_CHANNEL"
        else:
            return "ABORT_FORGERY"

    def calculate_tradeoffs(
        self,
        token_count: int = 200,
        baseline_noise_p0: float = 0.03,
        attack_noise_p1: float = 0.3333
    ) -> Dict[str, Any]:
        """
        Calculates theoretical False Rejection Rate (FRR) and False Acceptance Rate (FAR)
        for the configured threshold sv.
        - FRR = P(Mismatches > floor(sv * N) | p0)
        - FAR = P(Mismatches <= floor(sv * N) | p1)
        """
        k_cutoff = int(self.sv * token_count)

        # FRR: legitimate channel rejected
        frr = float(binom.sf(k_cutoff, token_count, baseline_noise_p0))

        # FAR: attack accepted as legitimate
        far = float(binom.cdf(k_cutoff, token_count, attack_noise_p1))

        return {
            "sv_verification_threshold": self.sv,
            "sa_abort_threshold": self.sa,
            "token_count": token_count,
            "k_cutoff_mismatches": k_cutoff,
            "false_rejection_rate": frr,
            "false_rejection_rate_pct": f"{frr * 100:.4f}%",
            "false_acceptance_rate": far,
            "false_acceptance_rate_pct": f"{far * 100:.6e}%" if far < 1e-4 else f"{far * 100:.4f}%",
            "explanation": (
                f"With sv={self.sv*100:.1f}%, a signature is accepted if mismatches <= {k_cutoff}. "
                f"Under {baseline_noise_p0*100:.1f}% physical channel noise, FRR is {frr*100:.3f}%. "
                f"Under an active intercept-resend forgery (~{attack_noise_p1*100:.1f}% error), FAR is {far*100:.6e}%."
            )
        }

