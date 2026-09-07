<p align="center">
  <img src="assets/cover.png" alt="Quetzalcoatl QDS Logo" width="260" />
</p>

<h1 align="center">QUETZALCOATL</h1>
<p align="center">
  <b>Quantum Digital Signature (QDS) Cyber Threat Detection SOC</b><br>
  <i>Teleportation-Based QDS Operational Security Monitoring & Statistical Threat Analysis</i>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11%2B-blue.svg" alt="Python 3.11+"></a>
  <a href="#"><img src="https://img.shields.io/badge/Physics-Quantum%20Information%20Theoretic-indigo.svg" alt="Physics"></a>
  <a href="#"><img src="https://img.shields.io/badge/Inference-Strictly%20Non--ML%20%2F%20Exact%20Statistics-emerald.svg" alt="Non-ML"></a>
  <a href="#"><img src="https://img.shields.io/badge/Audit-Tamper--Evident%20SHA--256%20Merkle-purple.svg" alt="Merkle Audit"></a>
</p>

An operational cybersecurity framework and interactive Security Operations Center (SOC) designed to monitor, simulate, detect, classify, and mathematically explain cyber threats against **Teleportation-Based Quantum Digital Signatures (QDS)**.

---

## 🌟 Executive Summary & Core Principle

Classical digital signatures (RSA, ECDSA) rely on computational hardness assumptions vulnerable to polynomial-time quantum cryptanalysis via Shor's algorithm ($O((\log N)^3)$). Post-Quantum Cryptography (PQC: lattice-based, hash-based) replaces these with alternative classical mathematical problems, which remain computationally bounded.

**Quantum Digital Signatures (QDS)** achieve **Information-Theoretic Security (ITS)** based on the fundamental postulates of quantum mechanics:
- **Quantum No-Cloning Theorem (Wootters & Zurek, 1982)**: Unknown quantum states cannot be duplicated.
- **State Disturbance upon Measurement**: Measurement of non-orthogonal quantum states irreversibly perturbs the system's density matrix $\rho$.

### The Operational Cybersecurity Gap
In theoretical QDS literature, security is proven asymptotically ($N \to \infty$) or under idealized bounds. In an operational network, physical optical noise, detector dark counts, and multi-vector adversaries exist. Standard QDS systems return only a binary decision ($M/N < s_v$).

**Our Contribution**: An **operational threat-detection and cyber security monitoring layer** around QDS:
```
Quantum Protocol (Teleportation + BSM)
       ↓
Quantum Measurements (Z, X, Y Bases)
       ↓
Measurement Statistics (Matches / Mismatches)
       ↓
Statistical Analysis (Binomial Tests, Wilson CI, Hoeffding Bounds)
       ↓
Dual-Threshold Policy Engine (sv = 10%, sa = 20%)
       ↓
Rule-Based Threat Classification (Strictly Non-ML)
       ↓
Security Decision (ACCEPT / ALERT / BLOCK)
       ↓
Tamper-Evident SHA-256 Merkle Hash Chain Audit
```

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph ProtocolCore ["QDS Protocol Core"]
        Alice["Alice (Signer)"] -->|Secret Key theta_k, v_k| States["Quantum Signing States: |psi_k> in {Z, X, Y}"]
        EPR["Pre-Distributed EPR Pairs: |Phi+>"] --> BSM["Bell-State Measurement (BSM)"]
        States --> BSM
        BSM -->|2 Classical Bits (b1, b2)| BobCorr["Bob Pauli Correction: U = Z^b1 * X^b2"]
        BobCorr --> BobState["Bob Reconstructed Qubits: |psi_B>"]
    end

    subgraph AttackLab ["Attack Simulation Lab"]
        Forge["1. Quantum Forgery (Intercept-Resend)"]
        Chan["2. Channel Manipulation (Depolarizing Noise)"]
        Rep["3. Replay Attack (Stale Classical Bits)"]
        Imp["4. Signer Impersonation (Rogue Registry)"]
        Unauth["5. Unauthorized Verifier (RBAC Violation)"]
    end

    subgraph MeasurementEngine ["Measurement & Statistical Engine"]
        BobState --> Meas["Projective Measurement in Basis theta_k"]
        Meas --> Counts["Match / Mismatch Counter: e = M / N"]
        Counts --> Binom["Exact Binomial Hypothesis Test: P(X >= M | H0)"]
        Counts --> Wilson["Wilson Score 95% Confidence Interval"]
        Counts --> Hoeffding["Hoeffding Bound on Forgery Probability"]
    end

    subgraph DetectionEngine ["Dual-Threshold & Classification Engine"]
        Binom --> Engine{"Threshold Engine"}
        Wilson --> Engine
        Hoeffding --> Engine
        Engine -->|e <= sv (10%)| Pass["ACCEPT (Valid Signature)"]
        Engine -->|sv < e < sa (20%)| Warn["ALERT (Channel Disturbance)"]
        Engine -->|e >= sa| Block["BLOCK (Quantum Forgery)"]
    end

    subgraph AuditLayer ["Tamper-Evident Ledger"]
        Pass --> Merkle["SHA-256 Merkle Hash Chain Ledger"]
        Warn --> Merkle
        Block --> Merkle
    end
```

---

## 🔬 Mathematical Detection Framework (Strictly Non-ML)

1. **Exact Binomial Hypothesis Testing**:
   - **Null Hypothesis ($H_0$)**: Mismatches arise purely from legitimate physical channel noise ($p_0 = 0.03$).
   - Exact one-tailed p-value:
     $$P(X \ge M \mid N, p_0) = \sum_{k=M}^N \binom{N}{k} p_0^k (1 - p_0)^{N-k}$$
   - When $P < 0.001$, $H_0$ is overwhelmingly rejected.

2. **Wilson Score Confidence Interval (95%)**:
   $$\text{CI}_{0.95} = \frac{\hat{e} + \frac{z^2}{2N} \pm z \sqrt{\frac{\hat{e}(1-\hat{e})}{N} + \frac{z^2}{4N^2}}}{1 + \frac{z^2}{N}}$$

3. **Hoeffding's Inequality Upper Bound on Forgery**:
   $$P(\hat{e} \le s_v \mid p_{\text{attack}}) \le \exp\left(-2 N (p_{\text{attack}} - s_v)^2\right)$$
   For $N=200$, $s_v=0.10$, and intercept-resend attack $p_{\text{attack}} = 0.3333$, the forgery escape probability is rigorously bounded by:
   $$P_{\text{forgery}} \le \exp(-400 \times 0.0544) \approx 3.4 \times 10^{-10}$$

4. **Dual Threshold Policy ($s_v, s_a$)**:
   - **$s_v = 10\%$ (Verification Threshold)**: Below this, normal physical channel attenuation is accepted.
   - **$s_a = 20\%$ (Abort Threshold)**: Above this, state disturbance confirms an adversarial attack.
   - **$[s_v, s_a)$ (Suspicious Zone)**: Alerts SOC analysts to channel degradation or weak probes.

---

## ⚔️ The 5 Attack Simulation Models

| Attack Vector | Mechanism | Expected Error ($\hat{e}$) | Threat Attribution | Action |
| :--- | :--- | :--- | :--- | :--- |
| **1. Quantum Forgery** | Intercept-resend guessing conjugate basis ($P_{\text{wrong}} = 2/3$) | $\sim 33.3\% + p_0$ | `FORGERY` | **BLOCK** |
| **2. Channel Manipulation** | 22% Depolarizing noise injected into quantum fiber | $\sim 14.7\%$ ($s_v < e < s_a$) | `CHANNEL_MANIPULATION` | **ALERT** |
| **3. Replay Attack** | Captured classical bits replayed; target Bell pairs already collapsed | Reused Nonce | `REPLAY` | **BLOCK** |
| **4. Signer Impersonation** | Rogue entity transmits without valid entanglement registry binding | Spoofed Identity | `IMPERSONATION` | **BLOCK** |
| **5. Unauthorized Verifier** | Third-party queries endpoint without verifier credentials | RBAC Violation | `UNAUTHORIZED_VERIFICATION` | **BLOCK** |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.11+
- Installed packages: `fastapi`, `uvicorn`, `scipy`, `numpy`, `cryptography`, `pytest`

### 2. Launch the System
```bash
python run.py
```
- **QDS Cyber SOC Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive REST API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Run Automated Test Suite
```bash
python -m pytest backend/tests -v
```
*All 31 unit & integration tests across Quantum Physics, Teleportation Fidelity, QDS Protocol, Attack Simulations, Wald SPRT, KL Divergence, Forensic Tamper Detection, Multi-Party Arbitration, and REST Endpoints pass cleanly in < 2 seconds.*

---

## 🧪 SOC Dashboard & Advanced Features

1. **Live Threat Cockpit**:
   - Real-time Circular Error Gauge with dynamic color transitions (Emerald, Amber, Rose).
   - One-click trigger for Legitimate verification and all 5 Attack Lab vectors.
   - Basis breakdown chart for $Z, X, Y$ Pauli observables.
   - **Wald's Sequential Probability Ratio Test (SPRT)**: Early-stopping decision boundary saving $>75\%$ measurement qubits.
   - **Kullback-Leibler (KL) Divergence**: $D_{KL}(Q \parallel P)$ in nats measuring informational distance from nominal channel noise.
2. **Teleportation Circuit Lab**:
   - Step-by-step circuit timeline: $|\psi\rangle \to |\Phi^+\rangle \to \text{BSM} \to (b_1, b_2) \to Z^{b_1} X^{b_2} \to |\psi\rangle$.
   - Live Bloch sphere coordinates $(x, y, z)$ and state amplitudes.
3. **Attack Comparison Matrix**:
   - Side-by-side comparative table evaluating theoretical vs. observed error rates across all scenarios.
4. **Monte Carlo Experiment Mode**:
   - Executes $K$ independent trials (e.g. 50 trials) to empirically compute False Acceptance Rate (FAR), False Rejection Rate (FRR), and latency.
5. **Tamper-Evident Merkle Ledger & On-Chain Anchor**:
   - Live append-only audit trail with interactive cryptographic inclusion proof inspector.
   - **Solidity Smart Contract** (`contracts/QuetzalcoatlEvidenceRegistry.sol`) anchoring Merkle roots on EVM blockchain.
   - **Interactive Forensic Tamper Demo**: Demonstrates mathematical proof failure and hash divergence upon simulated insider log alterations.
6. **Multi-Party Non-Repudiation (Alice $\to$ Bob & Charlie)**:
   - Implements Zeng-Christoph (2002) 3-party transferability theorem.
   - Direct verification by Bob ($e_B \le s_v$) and cross-dispute arbitration by Charlie ($|e_B - e_C| \le \Delta = 10\%$).
   - Asymmetric repudiation attacks by Alice are mathematically detected and flagged.
7. **Educational Guide**:
   - Theoretical explanations of qubits, Bell states, BSM, Pauli complementarity, and why no-cloning guarantees information-theoretic security.
