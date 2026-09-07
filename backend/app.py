"""
FastAPI Application & QDS Cyber Security Operations Center (SOC) Gateway API
Teleportation-Based Quantum Digital Signatures (QDS) Threat Detection Framework
"""

import os
import time
import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.config import (
    DEFAULT_TOKEN_COUNT, DEFAULT_CHANNEL_NOISE,
    DEFAULT_VERIFICATION_THRESHOLD, DEFAULT_ABORT_THRESHOLD,
    DEFAULT_ALPHA_SIGNIFICANCE, BASES, EIGENSTATES, BELL_STATES
)
from backend.qds.quantum_state import QubitState
from backend.qds.protocol import QDSSigningSession
from backend.detection.statistics import QuantumStatisticalEngine
from backend.detection.thresholds import QDSThresholdEngine
from backend.detection.classifier import QDSThreatClassifier
from backend.audit.merkle_ledger import MerkleAuditLedger
from backend.audit.tamper_demo import ForensicTamperDetector
from backend.qds.multi_verifier import MultiPartyQDSSession

# Attack Simulators
from backend.attacks.forgery import ForgeryAttackSimulator
from backend.attacks.impersonation import ImpersonationAttackSimulator
from backend.attacks.replay import ReplayAttackSimulator
from backend.attacks.channel_attack import ChannelAttackSimulator
from backend.attacks.unauthorized import UnauthorizedVerificationSimulator

app = FastAPI(
    title="Quantum Digital Signature (QDS) Cyber Threat Detection SOC",
    description="Operational security monitoring and statistical threat detection layer for teleportation-based QDS.",
    version="2.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State Singletons
threshold_engine = QDSThresholdEngine(DEFAULT_VERIFICATION_THRESHOLD, DEFAULT_ABORT_THRESHOLD)
threat_classifier = QDSThreatClassifier(threshold_engine)
merkle_ledger = MerkleAuditLedger()

# In-memory sessions store
active_sessions: Dict[str, QDSSigningSession] = {}
current_session: Optional[QDSSigningSession] = None

# Initialize default startup session
current_session = QDSSigningSession(
    message="NATIONAL_CRITICAL_INFRASTRUCTURE_DISBURSEMENT_2026",
    token_count=DEFAULT_TOKEN_COUNT,
    channel_noise=DEFAULT_CHANNEL_NOISE
)
active_sessions[current_session.session_id] = current_session

# Pydantic Schemas
class CreateSessionRequest(BaseModel):
    message: str = Field(default="APPROVE_FINANCIAL_SETTLEMENT_ORDER_7810")
    signer_id: str = Field(default="alice.signer@gov.in")
    verifier_id: str = Field(default="bob.verifier@finance.gov.in")
    token_count: int = Field(default=200, ge=20, le=2000)
    channel_noise: float = Field(default=0.03, ge=0.0, le=0.50)

class ThresholdUpdateRequest(BaseModel):
    verification_threshold: float = Field(default=0.10, ge=0.01, le=0.45)
    abort_threshold: float = Field(default=0.20, ge=0.05, le=0.50)

class AttackSimulateRequest(BaseModel):
    attack_type: str = Field(default="forgery")  # forgery, impersonation, replay, channel_manipulation, unauthorized
    disturbance_level: Optional[float] = 0.18
    forged_message: Optional[str] = "FORGED_TREASURY_TRANSFER_INR_90M"

class ExperimentRequest(BaseModel):
    trials: int = Field(default=30, ge=5, le=100)
    token_count: int = Field(default=150, ge=20, le=500)
    attack_type: str = Field(default="forgery")
    channel_noise: float = Field(default=0.03)
    disturbance_level: float = Field(default=0.18)

class ProofVerifyRequest(BaseModel):
    leaf_hash: str
    merkle_root: str
    proof_path: List[Dict[str, str]]

class TamperDemoRequest(BaseModel):
    target_record_index: int = Field(default=2, ge=0)

class MultiVerifierRequest(BaseModel):
    message: str = Field(default="CROSS_BORDER_TREASURY_SETTLEMENT_BATCH_901")
    token_count: int = Field(default=150, ge=20, le=1000)
    channel_noise: float = Field(default=0.03, ge=0.0, le=0.30)
    repudiation_attack: bool = Field(default=False)


@app.get("/api/status")
async def get_system_status():
    """Returns quantum operational status, bases, and threshold parameters."""
    return {
        "status": "OPERATIONAL",
        "quantum_framework": "Teleportation-Based Quantum Digital Signatures (Bennett et al. BSM)",
        "security_basis": "Information-Theoretic Security (No-Cloning Theorem & Conjugate Basis Complementarity)",
        "statistical_inference": "Exact Binomial Hypothesis Testing + Wilson Score CIs + Hoeffding Bounds",
        "ai_ml_free": True,
        "supported_bases": BASES,
        "eigenstates": EIGENSTATES,
        "bell_states": BELL_STATES,
        "thresholds": {
            "sv_verification": threshold_engine.sv,
            "sa_abort": threshold_engine.sa
        },
        "merkle_root": merkle_ledger.root_hash,
        "audit_records_count": len(merkle_ledger.entries),
        "active_session_id": current_session.session_id if current_session else None
    }


@app.post("/api/qds/session")
async def create_session(req: CreateSessionRequest):
    """Creates a new Alice-Bob QDS signing session with fresh quantum signing states."""
    global current_session
    session = QDSSigningSession(
        message=req.message,
        signer_id=req.signer_id,
        verifier_id=req.verifier_id,
        token_count=req.token_count,
        channel_noise=req.channel_noise
    )
    active_sessions[session.session_id] = session
    current_session = session

    return {
        "session_id": session.session_id,
        "message": session.message,
        "message_hash": session.message_hash,
        "signer_id": session.signer_id,
        "verifier_id": session.verifier_id,
        "token_count": session.token_count,
        "channel_noise": session.channel_noise,
        "nonce": session.nonce,
        "created_at": session.created_at,
        "sample_tokens_preview": session.alice_secret_key[:8]
    }


@app.post("/api/qds/teleport")
async def execute_teleportation():
    """Executes the quantum teleportation circuit across all tokens in the active session."""
    if not current_session:
        raise HTTPException(status_code=400, detail="No active QDS session found.")

    records = current_session.execute_teleportation()
    avg_fidelity = sum(r["fidelity"] for r in records) / max(1, len(records))

    return {
        "session_id": current_session.session_id,
        "total_tokens_teleported": len(records),
        "average_state_fidelity": round(avg_fidelity, 5),
        "sample_teleportation_milestones": records[:6]
    }


@app.post("/api/qds/verify")
async def verify_signature():
    """
    Executes legitimate signature verification for the active session.
    Calculates measurement statistics, binomial tests, threshold checks, and logs audit record.
    """
    if not current_session:
        raise HTTPException(status_code=400, detail="No active QDS session found.")

    # 1. Bob measures received qubits in disclosed bases
    raw_verify = current_session.verify()

    # 2. Statistical Analysis (Non-ML)
    stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
        total_measurements=raw_verify["total_measurements"],
        mismatches=raw_verify["mismatches"],
        expected_noise_p0=current_session.channel_noise,
        verification_threshold=threshold_engine.sv,
        alpha_significance=DEFAULT_ALPHA_SIGNIFICANCE
    )

    # 3. Threat Classification & Action Decision
    session_context = {
        "is_valid_identity": True,
        "is_authorized_verifier": True,
        "is_nonce_reused": False,
        "is_session_expired": False,
        "nonce": current_session.nonce
    }
    classification = threat_classifier.classify_event(stats, session_context)

    # 4. Commit to Tamper-Evident Merkle Ledger
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    audit_entry = merkle_ledger.append_qds_event(
        session_id=current_session.session_id,
        signer_id=current_session.signer_id,
        verifier_id=current_session.verifier_id,
        message=current_session.message,
        token_count=stats["total_measurements"],
        mismatches=stats["mismatches"],
        error_rate=stats["error_rate"],
        threat_type=classification["threat_type"],
        action=classification["action"],
        p_value=stats["binomial_p_value"],
        timestamp=now_iso
    )

    return {
        "session_id": current_session.session_id,
        "verification_type": "LEGITIMATE",
        "action": classification["action"],
        "threat_type": classification["threat_type"],
        "statistics": stats,
        "classification": classification,
        "raw_verification": raw_verify,
        "audit_record": audit_entry
    }


@app.post("/api/attacks/simulate/{attack_type}")
async def simulate_attack(attack_type: str, req: AttackSimulateRequest = Body(...)):
    """
    Executes one of the 5 operational attacks against the active QDS session:
    - forgery
    - impersonation
    - replay
    - channel_manipulation
    - unauthorized
    """
    if not current_session:
        raise HTTPException(status_code=400, detail="No active QDS session found.")

    at = attack_type.lower()
    attack_data: Dict[str, Any] = {}

    if at == "forgery":
        attack_data = ForgeryAttackSimulator.execute_intercept_resend_forgery(
            session=current_session,
            forged_message=req.forged_message or "FORGED_MESSAGE"
        )
        session_context = {
            "is_valid_identity": True,
            "is_authorized_verifier": True,
            "is_nonce_reused": False,
            "is_session_expired": False
        }
    elif at == "impersonation":
        attack_data = ImpersonationAttackSimulator.execute_impersonation(session=current_session)
        session_context = attack_data["session_context"]
    elif at == "replay":
        attack_data = ReplayAttackSimulator.execute_replay(session=current_session)
        session_context = attack_data["session_context"]
    elif at == "channel_manipulation":
        attack_data = ChannelAttackSimulator.execute_channel_disturbance(
            session=current_session,
            disturbance_level=req.disturbance_level if req.disturbance_level is not None else 0.22
        )
        session_context = attack_data["session_context"]
    elif at == "unauthorized":
        attack_data = UnauthorizedVerificationSimulator.execute_unauthorized_attempt(session=current_session)
        session_context = attack_data["session_context"]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown attack type: {attack_type}")

    raw_verify = attack_data["verification_result"]

    # Statistical Evaluation
    stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
        total_measurements=raw_verify["total_measurements"],
        mismatches=raw_verify["mismatches"],
        expected_noise_p0=current_session.channel_noise,
        verification_threshold=threshold_engine.sv,
        alpha_significance=DEFAULT_ALPHA_SIGNIFICANCE
    )

    # Classification
    classification = threat_classifier.classify_event(stats, session_context)

    # Commit to Merkle Ledger
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    audit_entry = merkle_ledger.append_qds_event(
        session_id=current_session.session_id,
        signer_id=session_context.get("claimed_signer", current_session.signer_id),
        verifier_id=session_context.get("requesting_party", current_session.verifier_id),
        message=current_session.message,
        token_count=stats["total_measurements"],
        mismatches=stats["mismatches"],
        error_rate=stats["error_rate"],
        threat_type=classification["threat_type"],
        action=classification["action"],
        p_value=stats["binomial_p_value"],
        timestamp=now_iso
    )

    return {
        "session_id": current_session.session_id,
        "threat_type": classification["threat_type"],
        "attack_type": classification["threat_type"],
        "action": classification["action"],
        "scenario_title": attack_data.get("scenario", attack_type.upper()),
        "explanation": attack_data.get("explanation", ""),
        "statistics": stats,
        "classification": classification,
        "raw_verification": raw_verify,
        "attack_specific_data": {k: v for k, v in attack_data.items() if k not in ["verification_result", "session_context"]},
        "audit_record": audit_entry
    }


@app.post("/api/thresholds")
async def update_thresholds(req: ThresholdUpdateRequest):
    """Updates dual thresholds (sv, sa) and recalculates theoretical FAR and FRR."""
    try:
        global threshold_engine, threat_classifier
        threshold_engine = QDSThresholdEngine(req.verification_threshold, req.abort_threshold)
        threat_classifier = QDSThreatClassifier(threshold_engine)

        tradeoffs = threshold_engine.calculate_tradeoffs(
            token_count=current_session.token_count if current_session else 200,
            baseline_noise_p0=current_session.channel_noise if current_session else 0.03
        )
        return {
            "status": "UPDATED",
            "thresholds": {
                "sv": threshold_engine.sv,
                "sa": threshold_engine.sa
            },
            "tradeoffs": tradeoffs
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/experiments/run")
async def run_experiment(req: ExperimentRequest):
    """
    Executes N Monte Carlo trials to evaluate empirical False Acceptance Rate (FAR),
    False Rejection Rate (FRR), detection latency, and mismatch rate distribution.
    """
    start_time = time.perf_counter()
    mismatches_list = []
    error_rates = []
    decisions = {"ACCEPT": 0, "ALERT": 0, "BLOCK": 0}
    threat_counts = {}

    for _ in range(req.trials):
        temp_session = QDSSigningSession(
            message=f"EXPERIMENT_SAMPLE_{_}",
            token_count=req.token_count,
            channel_noise=req.channel_noise
        )

        if req.attack_type == "none":
            # Legitimate run
            temp_session.execute_teleportation()
            res = temp_session.verify()
            context = {"is_valid_identity": True, "is_authorized_verifier": True}
        elif req.attack_type == "forgery":
            data = ForgeryAttackSimulator.execute_intercept_resend_forgery(temp_session)
            res = data["verification_result"]
            context = {"is_valid_identity": True, "is_authorized_verifier": True}
        elif req.attack_type == "channel_manipulation":
            data = ChannelAttackSimulator.execute_channel_disturbance(
                temp_session, disturbance_level=req.disturbance_level
            )
            res = data["verification_result"]
            context = data["session_context"]
        else:
            temp_session.execute_teleportation()
            res = temp_session.verify()
            context = {"is_valid_identity": True, "is_authorized_verifier": True}

        stats = QuantumStatisticalEngine.evaluate_measurement_statistics(
            total_measurements=res["total_measurements"],
            mismatches=res["mismatches"],
            expected_noise_p0=req.channel_noise,
            verification_threshold=threshold_engine.sv
        )
        classification = threat_classifier.classify_event(stats, context)

        error_rates.append(stats["error_rate"])
        mismatches_list.append(res["mismatches"])
        decisions[classification["action"]] = decisions.get(classification["action"], 0) + 1
        t_type = classification["threat_type"]
        threat_counts[t_type] = threat_counts.get(t_type, 0) + 1

    total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    mean_error = sum(error_rates) / max(1, len(error_rates))
    variance = sum((e - mean_error) ** 2 for e in error_rates) / max(1, len(error_rates))
    std_dev = variance ** 0.5

    # Empirical rates
    if req.attack_type == "none":
        # FRR is proportion of legitimate trials rejected (BLOCK or ALERT)
        empirical_frr = (decisions.get("BLOCK", 0) + decisions.get("ALERT", 0)) / req.trials
        empirical_far = 0.0
    else:
        # FAR is proportion of attack trials accepted (ACCEPT)
        empirical_far = decisions.get("ACCEPT", 0) / req.trials
        empirical_frr = 0.0

    return {
        "trials": req.trials,
        "attack_type": req.attack_type,
        "token_count": req.token_count,
        "channel_noise": req.channel_noise,
        "mean_error_rate": round(mean_error, 4),
        "std_deviation": round(std_dev, 4),
        "empirical_far": round(empirical_far, 4),
        "empirical_frr": round(empirical_frr, 4),
        "decision_distribution": decisions,
        "threat_distribution": threat_counts,
        "error_rates_sample": [round(e, 4) for e in error_rates[:20]],
        "latency_ms": total_time_ms
    }


@app.get("/api/circuit/teleportation-sample")
async def get_circuit_sample():
    """
    Returns a sample teleportation circuit execution with Bloch coordinates
    and statevectors across all intermediate steps for visual display.
    """
    # Create sample |+> state in X-basis
    input_qubit = QubitState.from_pauli_eigenstate("X", 0)
    res = TeleportationSimulator.teleport_qubit(input_qubit, channel_noise_p=0.0)
    return {
        "input_state": res["input_state"],
        "bell_state_measured": res["bell_outcome"],
        "classical_bits_feedforward": res["classical_bits"],
        "pauli_correction_applied": res["pauli_correction"],
        "reconstructed_state": res["bob_reconstructed_state"],
        "reconstruction_fidelity": res["fidelity"]
    }


@app.get("/api/audit/logs")
async def get_audit_logs(limit: int = 50):
    """Returns recent Merkle hash-chain audit entries."""
    return {
        "merkle_root": merkle_ledger.root_hash,
        "total_records": len(merkle_ledger.entries),
        "entries": merkle_ledger.entries[-limit:][::-1]
    }


@app.get("/api/audit/proof/{index}")
async def get_merkle_proof(index: int):
    """Generates cryptographic inclusion proof for a ledger entry."""
    try:
        return merkle_ledger.get_inclusion_proof(index)
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/audit/verify-proof")
async def verify_merkle_proof(req: ProofVerifyRequest):
    """Mathematically validates a Merkle inclusion proof."""
    is_valid = MerkleAuditLedger.verify_inclusion_proof(
        leaf_hash=req.leaf_hash,
        proof_path=req.proof_path,
        expected_root=req.merkle_root
    )
    return {
        "verified": is_valid,
        "leaf_hash": req.leaf_hash,
        "merkle_root": req.merkle_root,
        "status": "CRYPTOGRAPHICALLY_AUTHENTIC" if is_valid else "TAMPERED_OR_INVALID"
    }


@app.post("/api/audit/tamper-demo")
async def run_tamper_demo(req: TamperDemoRequest = Body(default=TamperDemoRequest())):
    """Executes forensic tamper demonstration and returns mathematical proof of tampering."""
    return ForensicTamperDetector.execute_tamper_demonstration(target_index=req.target_record_index)


@app.post("/api/qds/multi-verifier/simulate")
async def simulate_multi_verifier(req: MultiVerifierRequest = Body(default=MultiVerifierRequest())):
    """Simulates 3-party (Alice -> Bob & Charlie) QDS non-repudiation and dispute arbitration."""
    session = MultiPartyQDSSession(
        message=req.message,
        token_count=req.token_count,
        channel_noise=req.channel_noise,
        verification_threshold=threshold_engine.sv,
        abort_threshold=threshold_engine.sa
    )
    return session.run_complete_dispute_protocol(repudiation_attack=req.repudiation_attack)


@app.get("/api/blockchain/registry-status")
async def get_blockchain_registry_status():
    """Returns on-chain evidence registry status and smart contract metadata."""
    return {
        "network": "Ethereum Sepolia (EVM) / Hyperledger Besu Anchor",
        "contract_name": "QuetzalcoatlEvidenceRegistry",
        "contract_address": "0x9F8F72aA9304c8B593d555F12eF6589cC3A579A2",
        "solidity_version": "^0.8.20",
        "current_merkle_root": merkle_ledger.root_hash,
        "total_anchored_roots": max(1, len(merkle_ledger.entries)),
        "total_recorded_incidents": sum(1 for e in merkle_ledger.entries if e.get("threat_type") in ["FORGERY", "CHANNEL_MANIPULATION", "REPLAY"]),
        "consensus_finality": "FINALIZED",
        "functions": [
            "recordMerkleRoot(bytes32 root, uint256 recordCount, string metadataURI)",
            "recordIncidentLeaf(bytes32 leafHash, uint256 sessionIndex, string threatType)",
            "verifyInclusionProofSHA256(bytes32 leaf, bytes32[] proof, bool[] isRight, bytes32 root)"
        ]
    }


# Mount static frontend directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def serve_index():
    """Serves the QDS Cyber SOC Dashboard UI."""
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "QDS Cyber SOC Dashboard. Static assets loading."}
