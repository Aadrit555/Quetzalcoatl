"""
tests/test_social_scenarios.py
Verifies end-to-end simulation of high-impact social problem missions:
1. Pediatric Donor Heart Emergency Allocation (Forgery Intercept)
2. National Power Grid Emergency Substation Tripping (Nonce Replay)
3. $45M Flood Relief Direct Aid Disbursement (Channel Noise)
"""

from qds_protocol.social_scenarios import list_social_scenarios, simulate_social_mission


def test_list_social_scenarios():
    scenarios = list_social_scenarios()
    assert len(scenarios) == 3
    ids = [s["id"] for s in scenarios]
    assert "healthcare_organ_dispatch" in ids
    assert "grid_blackout_command" in ids
    assert "disaster_relief_aid" in ids


def test_healthcare_organ_dispatch_forgery():
    result = simulate_social_mission("healthcare_organ_dispatch", attack_mode="forgery")
    assert result["scenario"]["id"] == "healthcare_organ_dispatch"
    # Intercept-resend attack triggers high QBER (~34%) and abort
    assert result["qber"] > 0.20
    assert result["social_verdict"] == "QUANTUM FORGERY INTERCEPTED"
    assert "Pediatric" in result["scenario"]["title"]
    assert "Catastrophe averted" in result["impact_summary"]


def test_grid_blackout_replay_attack():
    result = simulate_social_mission("grid_blackout_command", attack_mode="replay")
    assert result["scenario"]["id"] == "grid_blackout_command"
    assert result["attribution"]["attack_class"] == "replay"
    assert result["social_verdict"] == "REPLAY SABOTAGE INTERDICTED"
    assert "4.2M" in result["impact_summary"] or "Metropolitan" in result["impact_summary"]


def test_disaster_relief_channel_noise():
    result = simulate_social_mission("disaster_relief_aid", attack_mode="channel_noise")
    assert result["scenario"]["id"] == "disaster_relief_aid"
    assert 0.10 <= result["qber"] <= 0.20
    assert "CHANNEL NOISE ALERT" in result["social_verdict"]
    assert "Auto-calibrating" in result["impact_summary"]


def test_nominal_mission_success():
    result = simulate_social_mission("healthcare_organ_dispatch", attack_mode="nominal")
    assert result["decision"] == "ACCEPT"
    assert result["qber"] < 0.10
    assert result["social_verdict"] == "MISSION AUTHENTICATED & SECURED"

