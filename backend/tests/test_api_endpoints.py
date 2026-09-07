"""Unit tests for FastAPI REST Endpoints for QDS Cyber SOC."""

from starlette.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_api_system_status():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    assert data["ai_ml_free"] is True
    assert "Z" in data["supported_bases"]

def test_api_create_session_and_teleport():
    resp = client.post("/api/qds/session", json={
        "message": "FINANCIAL_SETTLEMENT_ORDER",
        "token_count": 200,
        "channel_noise": 0.03
    })
    assert resp.status_code == 200
    sess = resp.json()
    assert sess["token_count"] == 200

    # Teleport
    tel_resp = client.post("/api/qds/teleport")
    assert tel_resp.status_code == 200
    tel_data = tel_resp.json()
    assert tel_data["total_tokens_teleported"] == 200
    assert tel_data["average_state_fidelity"] > 0.90

def test_api_legitimate_verify():
    # Session already teleported
    resp = client.post("/api/qds/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "ACCEPT"
    assert data["threat_type"] in ["SAFE", "NORMAL_NOISE"]
    assert "audit_record" in data

def test_api_simulate_forgery():
    resp = client.post("/api/attacks/simulate/forgery", json={
        "attack_type": "forgery",
        "forged_message": "TAMPERED_TREASURY_TRANSFER"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "BLOCK"
    assert data["threat_type"] == "FORGERY"
    assert data["statistics"]["binomial_p_value"] < 1e-4

def test_api_simulate_channel_manipulation():
    resp = client.post("/api/attacks/simulate/channel_manipulation", json={
        "attack_type": "channel_manipulation",
        "disturbance_level": 0.18
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "ALERT"
    assert data["threat_type"] == "CHANNEL_MANIPULATION"

def test_api_merkle_proof_verification():
    # Fetch recent proof
    logs_resp = client.get("/api/audit/logs")
    assert logs_resp.status_code == 200
    entries = logs_resp.json()["entries"]
    assert len(entries) > 0

    proof_resp = client.get("/api/audit/proof/0")
    assert proof_resp.status_code == 200
    proof = proof_resp.json()

    # Verify proof via API
    v_resp = client.post("/api/audit/verify-proof", json={
        "leaf_hash": proof["leaf_hash"],
        "merkle_root": proof["merkle_root"],
        "proof_path": proof["proof_path"]
    })
    assert v_resp.status_code == 200
    assert v_resp.json()["verified"] is True
    assert v_resp.json()["status"] == "CRYPTOGRAPHICALLY_AUTHENTIC"

def test_api_tamper_demonstration():
    resp = client.post("/api/audit/tamper-demo", json={"target_record_index": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["pre_tamper_verification"]["ledger_valid"] is True
    assert data["post_tamper_verification"]["ledger_valid"] is False
    assert data["post_tamper_verification"]["inclusion_proof_valid"] is False

def test_api_multi_verifier_legitimate():
    resp = client.post("/api/qds/multi-verifier/simulate", json={
        "token_count": 80,
        "repudiation_attack": False
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_outcome"] == "TRANSFER_CONFIRMED"
    assert data["bob_verification"]["is_accepted"] is True
    assert data["charlie_arbitration"]["is_accepted"] is True

def test_api_multi_verifier_repudiation():
    resp = client.post("/api/qds/multi-verifier/simulate", json={
        "token_count": 80,
        "repudiation_attack": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_outcome"] == "DISPUTE_RAISED"
    assert data["charlie_arbitration"]["arbitration_status"] == "REPUDIATION_ATTACK_DETECTED"

def test_api_blockchain_registry_status():
    resp = client.get("/api/blockchain/registry-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "QuetzalcoatlEvidenceRegistry" in data["contract_name"]
    assert "0x" in data["contract_address"]
    assert data["consensus_finality"] == "FINALIZED"

