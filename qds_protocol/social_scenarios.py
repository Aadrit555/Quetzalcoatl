"""
qds_protocol/social_scenarios.py
High-Impact Social & National Infrastructure Mission Scenarios for QDS Threat Detection.
Demonstrates how teleportation-based QDS prevents catastrophic real-world cyber warfare and social fraud.
"""

from typing import Dict, Any, List, Optional
import time
import numpy as np

from attack_simulation.attack_orchestrator import run_scenario
from quantum_core.bell_state_generator import sample_chsh
from detection_engine.integrity_monitor import inspect
from attribution_engine.rule_engine import attribute


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "healthcare_organ_dispatch": {
        "id": "healthcare_organ_dispatch",
        "title": "Pediatric Donor Heart Emergency Allocation",
        "category": "Healthcare & Life-Safety Logistics",
        "icon": "cardiology",
        "document_name": "ORGAN_DISPATCH_MANIFEST_#HRT-2026-P9.enc",
        "beneficiary": "Children's Critical Care ICU • Patient #9042",
        "social_stakes": "Donor organ viability window is 3.5 hours. Malicious intercept-resend forgery attempts to divert life-saving pediatric organ to black-market private facility.",
        "classical_vulnerability": "Classical RSA-4096 / ECDSA signatures are vulnerable to Harvest-Now-Decrypt-Later quantum attacks and quantum Shor factorization.",
        "default_attack": "forgery",
        "nominal_message": "AUTHORIZE_IMMEDIATE_TRANSIT_CARDIAC_GRAFT_TO_CHILDRENS_HOSPITAL_PRIMARY_ICU",
        "forged_message": "REROUTE_CARDIAC_GRAFT_TO_PRIVATE_AERODROME_VIP_HOLDING_FACILITY"
    },
    "grid_blackout_command": {
        "id": "grid_blackout_command",
        "title": "National Power Grid Emergency Substation Tripping",
        "category": "Critical Energy Infrastructure",
        "icon": "bolt",
        "document_name": "SCADA_GRID_EMERGENCY_BREAKER_CMD_#HV-7701.sig",
        "beneficiary": "Metropolitan Power Authority • 4.2M Civilian Population",
        "social_stakes": "Adversary captures a legitimate blizzard emergency shutdown packet from last month and attempts a Nonce Replay Attack during peak summer heatwave to trigger artificial regional blackout.",
        "classical_vulnerability": "Replay attacks in classical SCADA networks bypass signature checks if timestamp drift or certificate validation latency occurs.",
        "default_attack": "replay",
        "nominal_message": "EMERGENCY_SCADA_SUBSTATION_BREAKER_OPEN_GRID_ISOLATION_SEQ_77",
        "forged_message": "EMERGENCY_SCADA_SUBSTATION_BREAKER_OPEN_GRID_ISOLATION_SEQ_77"
    },
    "disaster_relief_aid": {
        "id": "disaster_relief_aid",
        "title": "$45M Emergency Flood Relief Fund Disbursement",
        "category": "Sovereign Citizen Welfare & Direct Aid",
        "icon": "volunteer_activism",
        "document_name": "TREASURY_DIRECT_RELIEF_BATCH_#DBT-2026-FL04.json",
        "beneficiary": "120,000 Displaced Flood Victims • Direct Subsidy Accounts",
        "social_stakes": "Optical fiber eavesdropping and depolarizing signal injection manipulates bank routing codes to siphon disaster relief funds from impoverished citizens to illicit offshore shell accounts.",
        "classical_vulnerability": "In-flight fiber manipulation and MITM taps can manipulate classical TLS sessions without triggering quantum state collapse.",
        "default_attack": "channel_manipulation",
        "nominal_message": "AUTHORIZE_DBT_DISASTER_TRANCHE_45M_TO_REGISTERED_FLOOD_RELIEF_CITIZENS",
        "forged_message": "AUTHORIZE_DBT_DISASTER_TRANCHE_45M_DIVERT_TO_OFFSHORE_SHELL_SWIFT_ROUTING"
    }
}


def list_social_scenarios() -> List[Dict[str, Any]]:
    """Returns metadata for all available real-world social impact scenarios."""
    return list(SCENARIOS.values())


def simulate_social_mission(scenario_id: str, attack_mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes an end-to-end QDS teleportation protocol for a specific real-world mission.
    Uses the attack simulation orchestrator and statistical detection engine.
    """
    if scenario_id not in SCENARIOS:
        scenario_id = "healthcare_organ_dispatch"

    scenario = SCENARIOS[scenario_id]
    attack = attack_mode if attack_mode is not None else scenario["default_attack"]

    token_count = 512
    seed = int(time.time() * 1000) % 100000
    p0, p1 = 0.03, 0.18

    # 1. Execute physical scenario via Attack Orchestrator
    if attack in ["forgery", "individual"]:
        # Intercept-resend attack with full measurement strength
        scenario_run = run_scenario(kind="forgery", strength=1.0, seed=seed, n=token_count)
        chsh_receipts = sample_chsh(8192, 0.35, seed + 4)
    elif attack == "replay":
        # Nonce replay injection
        scenario_run = run_scenario(kind="replay", strength=1.0, seed=seed, n=token_count)
        chsh_receipts = sample_chsh(8192, 0.02, seed + 4)
    elif attack in ["channel_noise", "channel_manipulation"]:
        # Physical fiber noise / eavesdropping
        scenario_run = run_scenario(kind="channel_manipulation", strength=0.5, seed=seed, n=token_count)
        chsh_receipts = sample_chsh(8192, 0.145, seed + 4)
    else:  # nominal / honest
        scenario_run = run_scenario(kind="honest", strength=0.0, seed=seed, n=token_count)
        chsh_receipts = sample_chsh(8192, 0.02, seed + 4)

    # 2. Statistical Threat Detection & Attribution
    stats = inspect(scenario_run.records, chsh_receipts, scenario_run.integrity, p0, p1)
    attr = attribute(stats)
    decision = stats["decision"]
    qber = stats["qber"]

    # 3. Formulate Human-Readable Social Impact Outcome
    if decision == "ACCEPT":
        social_verdict = "MISSION AUTHENTICATED & SECURED"
        status_color = "emerald"
        impact_summary = (
            f"Quantum integrity confirmed (QBER = {qber*100:.1f}%). "
            f"Zero eavesdropping detected. {scenario['title']} executed safely for {scenario['beneficiary']}."
        )
    elif attr.get("attack_class") == "replay":
        social_verdict = "REPLAY SABOTAGE INTERDICTED"
        status_color = "purple"
        impact_summary = (
            f"Adversary attempted replay of stale command on {scenario['document_name']}. "
            f"Freshness check failed; mutual quantum information collapsed (QBER = {qber*100:.1f}%). Unauthorized operation blocked. "
            f"Protected: {scenario['beneficiary']}."
        )
    elif qber > 0.20 or attr.get("attack_class") in ["forgery", "intercept_resend", "individual"]:
        social_verdict = "QUANTUM FORGERY INTERCEPTED"
        status_color = "rose"
        impact_summary = (
            f"Adversary attempted quantum state interception and forgery on {scenario['document_name']}. "
            f"No-Cloning collapse triggered fatal error spike ({qber*100:.1f}% > 20% abort bound). "
            f"Transfer halted. Catastrophe averted for {scenario['beneficiary']}."
        )
    else:
        social_verdict = "CHANNEL NOISE ALERT • TRANSMISSION RETUNED"
        status_color = "amber"
        impact_summary = (
            f"Degraded fiber noise detected ({qber*100:.1f}%). "
            f"Distinguished from malicious forgery via Hoeffding bounds. Auto-calibrating quantum channel for {scenario['document_name']}."
        )

    return {
        "scenario": scenario,
        "attack_mode": attack,
        "decision": decision,
        "qber": float(qber),
        "chsh_s": float(stats.get("chsh_s", 2.81)),
        "sprt_decision": stats.get("sprt_decision", decision),
        "attribution": attr,
        "social_verdict": social_verdict,
        "status_color": status_color,
        "impact_summary": impact_summary,
        "timestamp": time.strftime("%H:%M:%S UTC")
    }

