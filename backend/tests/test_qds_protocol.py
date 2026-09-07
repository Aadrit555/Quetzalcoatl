"""Unit tests for QDS Protocol signing, teleportation, and verification."""

from backend.qds.protocol import QDSSigningSession

def test_legitimate_qds_session():
    # Session with 150 tokens and 2% channel noise
    session = QDSSigningSession(
        message="AUTHORIZED_GOVERNMENT_DIRECTIVE_104",
        token_count=150,
        channel_noise=0.02
    )

    assert len(session.alice_secret_key) == 150
    assert len(session.alice_quantum_states) == 150

    # Teleport to Bob
    records = session.execute_teleportation()
    assert len(records) == 150
    assert len(session.bob_received_qubits) == 150

    # Bob verifies
    verify_res = session.verify()
    assert verify_res["total_measurements"] == 150
    # Under 2% noise, match rate should be high (> 90%)
    assert verify_res["matches"] > 130
    assert verify_res["error_rate"] < 0.10

