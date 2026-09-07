"""
Quantum Digital Signature (QDS) Cyber Threat Detection SOC
One-Click System Launcher
"""

import sys
import uvicorn

def main():
    print("=" * 80)
    print("  QUANTUM DIGITAL SIGNATURE (QDS) CYBER THREAT DETECTION SOC")
    print("  Teleportation-Based QDS Operational Security Monitoring Framework")
    print("=" * 80)
    print("  [+] Initializing Exact Quantum Linear Algebra Statevector Engine (C^2, C^4)...")
    print("  [+] Loading Pauli Eigenstate Observables (Z, X, Y) & 4 EPR Bell States...")
    print("  [+] Mounting 3-Qubit Quantum Teleportation & BSM Projection Engine...")
    print("  [+] Loading Non-ML Statistical Engine (Binomial, Wilson CI, Hoeffding, Wald SPRT, KL)...")
    print("  [+] Loading Multi-Party Arbitration (Zeng-Christoph 3-Party Non-Repudiation)...")
    print("  [+] Initializing 5 Attack Simulators (Forgery, Impersonation, Replay, Channel, RBAC)...")
    print("  [+] Mounting Tamper-Evident SHA-256 Merkle Ledger & Solidity Blockchain Anchor...")
    print("=" * 80)
    print("  >>> QDS SOC Dashboard:      http://127.0.0.1:8000")
    print("  >>> Interactive REST Docs:  http://127.0.0.1:8000/docs")
    print("=" * 80)

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
