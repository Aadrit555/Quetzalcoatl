"""
Global Configuration & Protocol Parameters for Quantum Digital Signatures (QDS)
Teleportation-Based QDS Operational Cyber Threat Detection Framework
"""

from typing import Dict, Any

# QDS Protocol Parameters
DEFAULT_TOKEN_COUNT = 200        # Number of quantum tokens per signed message bit
DEFAULT_CHANNEL_NOISE = 0.03     # 3% baseline quantum bit error rate (fiber attenuation / dark counts)

# Statistical Thresholds for Threat Detection
# sv: Verification Threshold (below sv => ACCEPT)
# sa: Abort / Dispute Threshold (above sa => REJECT / FORGERY)
# [sv, sa): Suspicious / Channel Manipulation Zone (ALERT)
DEFAULT_VERIFICATION_THRESHOLD = 0.10   # sv = 10%
DEFAULT_ABORT_THRESHOLD = 0.20          # sa = 20%

# Statistical Hypothesis Testing Significance Level
DEFAULT_ALPHA_SIGNIFICANCE = 0.001       # alpha = 0.1% for Binomial test rejection

# Session Security Parameters
MAX_ALLOWED_SESSION_AGE_SEC = 300       # 5 minutes maximum valid session lifetime
REPLAY_NONCE_CACHE_SIZE = 10000

# Pauli Bases
BASES = ["Z", "X", "Y"]

# Canonical Pauli Eigenstates
EIGENSTATES = {
    "Z": ["|0>", "|1>"],
    "X": ["|+>", "|->"],
    "Y": ["|+i>", "|-i>"]
}

# Standard Bell States
BELL_STATES = ["Phi+", "Phi-", "Psi+", "Psi-"]
