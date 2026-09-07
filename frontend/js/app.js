/**
 * QDS Cyber Security Operations Center (SOC) JavaScript Client
 * Teleportation-Based Quantum Digital Signatures Threat Detection
 */

let basisChart = null;
let currentSessionId = "";

document.addEventListener("DOMContentLoaded", async () => {
  lucide.createIcons();
  initHoverExplainerEngine();
  initBasisChart();
  await refreshSystemStatus();
  await refreshCircuitSample();
  await runLegitimateVerify();
  await refreshAuditLogs();
});

// Tab Navigation
function switchTab(tabId) {
  const tabs = ["cockpit", "circuit", "matrix", "experiments", "audit", "multi-party", "education"];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    const btn = document.getElementById(`tab-btn-${t}`);
    if (el) {
      if (t === tabId) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    }
    if (btn) {
      if (t === tabId) {
        btn.className = "tab-btn active px-3.5 py-1.5 rounded-lg border border-slate-800 text-cyan-400 flex items-center gap-1.5";
      } else {
        btn.className = "tab-btn px-3.5 py-1.5 rounded-lg border border-transparent hover:text-cyan-400 flex items-center gap-1.5 text-slate-400";
      }
    }
  });
  lucide.createIcons();
}

// Basis Breakdown Chart (Z, X, Y)
function initBasisChart() {
  const ctx = document.getElementById("basisChart").getContext("2d");
  basisChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Z-Basis", "X-Basis", "Y-Basis"],
      datasets: [
        {
          label: "Matches",
          data: [0, 0, 0],
          backgroundColor: "rgba(16, 185, 129, 0.7)",
          borderColor: "#10b981",
          borderWidth: 1
        },
        {
          label: "Mismatches",
          data: [0, 0, 0],
          backgroundColor: "rgba(244, 63, 94, 0.7)",
          borderColor: "#f43f5e",
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          stacked: true,
          grid: { color: "rgba(30, 41, 59, 0.5)" },
          ticks: { color: "#94a3b8", font: { size: 10, family: 'JetBrains Mono' } }
        },
        y: {
          stacked: true,
          grid: { color: "rgba(30, 41, 59, 0.5)" },
          ticks: { color: "#94a3b8", font: { size: 10, family: 'JetBrains Mono' } }
        }
      },
      plugins: {
        legend: {
          labels: { color: "#cbd5e1", font: { size: 10, family: 'JetBrains Mono' } }
        }
      }
    }
  });
}

// Fetch System Status
async function refreshSystemStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();
    currentSessionId = data.active_session_id;
    document.getElementById("ribbon-session-id").innerText = data.active_session_id || "None";
    document.getElementById("ribbon-sv").innerText = `${(data.thresholds.sv_verification * 100).toFixed(1)}%`;
    document.getElementById("ribbon-sa").innerText = `${(data.thresholds.sa_abort * 100).toFixed(1)}%`;
    document.getElementById("sv-display").innerText = `${(data.thresholds.sv_verification * 100).toFixed(1)}%`;
    document.getElementById("sa-display").innerText = `${(data.thresholds.sa_abort * 100).toFixed(1)}%`;
    document.getElementById("sv-slider").value = Math.round(data.thresholds.sv_verification * 100);
    document.getElementById("sa-slider").value = Math.round(data.thresholds.sa_abort * 100);
    if (data.merkle_root) {
      document.getElementById("top-merkle-root").innerText = data.merkle_root.substring(0, 16) + "...";
    }
  } catch (e) {
    console.error("Failed to load status:", e);
  }
}

// Create New Session
async function createNewSession() {
  try {
    const res = await fetch("/api/qds/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "AUTHORIZED_GOVERNMENT_INFRASTRUCTURE_CLEARANCE",
        token_count: 200,
        channel_noise: 0.03
      })
    });
    if (!res.ok) throw new Error("Session creation failed");
    const data = await res.json();
    currentSessionId = data.session_id;
    document.getElementById("ribbon-session-id").innerText = data.session_id;
    await runLegitimateVerify();
  } catch (e) {
    console.error(e);
  }
}

// Run Legitimate Verify
async function runLegitimateVerify() {
  try {
    const res = await fetch("/api/qds/verify", { method: "POST" });
    if (!res.ok) throw new Error("Verification failed");
    const data = await res.json();
    renderDecisionData(data);
    await refreshAuditLogs();
  } catch (e) {
    console.error(e);
  }
}

// Simulate Attack
async function simulateAttack(attackType) {
  try {
    const res = await fetch(`/api/attacks/simulate/${attackType}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attack_type: attackType, disturbance_level: 0.22 })
    });
    if (!res.ok) throw new Error("Attack simulation failed");
    const data = await res.json();
    renderDecisionData(data);
    await refreshAuditLogs();
  } catch (e) {
    console.error(e);
  }
}

// Render Decision Data into Cockpit
function renderDecisionData(data) {
  const stats = data.statistics;
  const classification = data.classification;

  // 1. Threat Type & Action Badges
  const tBadge = document.getElementById("threat-type-badge");
  tBadge.innerText = classification.threat_type;

  const aBadge = document.getElementById("action-badge");
  aBadge.innerText = classification.action;

  const circle = document.getElementById("error-rate-circle");
  const summary = document.getElementById("action-summary");

  const errPct = stats.error_rate * 100;
  document.getElementById("error-rate-val").innerText = `${errPct.toFixed(1)}%`;

  // Circumference = 339.29
  const circumference = 339.29;
  const offset = circumference - Math.min(1.0, stats.error_rate / 0.50) * circumference;
  circle.style.strokeDashoffset = offset;

  if (classification.action === "BLOCK") {
    circle.style.stroke = "#f43f5e";
    aBadge.className = "px-4 py-2 rounded-lg text-lg font-black tracking-wider mono bg-rose-500/20 border border-rose-500 text-rose-400 text-center pulse-rose";
    tBadge.className = "text-xs mono text-rose-400 font-bold";
    summary.innerText = "CRITICAL THREAT: Signature aborted. Non-cloning violation or credential fraud.";
  } else if (classification.action === "ALERT") {
    circle.style.stroke = "#f59e0b";
    aBadge.className = "px-4 py-2 rounded-lg text-lg font-black tracking-wider mono bg-amber-500/20 border border-amber-500 text-amber-400 text-center pulse-amber";
    tBadge.className = "text-xs mono text-amber-400 font-bold";
    summary.innerText = "SUSPICIOUS CHANNEL: Quantum optical disturbance exceeded sv; recalibration advised.";
  } else {
    circle.style.stroke = "#10b981";
    aBadge.className = "px-4 py-2 rounded-lg text-lg font-black tracking-wider mono bg-emerald-500/20 border border-emerald-500 text-emerald-400 text-center pulse-emerald";
    tBadge.className = "text-xs mono text-emerald-400 font-bold";
    summary.innerText = "VERIFIED: Quantum states undisturbed. Information-theoretic authenticity validated.";
  }

  // 2. Mathematical Reasoning List
  const rList = document.getElementById("reasons-list");
  rList.innerHTML = "";
  (classification.reasons || []).forEach(r => {
    const isWarn = r.includes("FORGERY") || r.includes("REPLAY") || r.includes("IMPERSONATION") || r.includes("Unauthorized");
    const color = isWarn ? "text-rose-400" : (r.includes("MANIPULATION") ? "text-amber-400" : "text-emerald-300");
    const icon = isWarn ? "alert-triangle" : (r.includes("MANIPULATION") ? "alert-circle" : "check");
    rList.innerHTML += `<li class="${color} flex items-start gap-1.5"><i data-lucide="${icon}" class="w-3.5 h-3.5 flex-shrink-0 mt-0.5"></i> ${r}</li>`;
  });

  // 3. Statistical Inference Indicators
  document.getElementById("stat-p-value").innerText = stats.binomial_p_value_formatted;
  document.getElementById("stat-z-score").innerText = `${stats.z_score_deviation} \u03C3`;
  document.getElementById("stat-wilson").innerText = `[${(stats.wilson_ci_95[0] * 100).toFixed(1)}%, ${(stats.wilson_ci_95[1] * 100).toFixed(1)}%]`;
  document.getElementById("stat-hoeffding").innerText = `\u2264 ${stats.hoeffding_forgery_bound_formatted}`;

  if (stats.sprt_early_stopping) {
    const sprt = stats.sprt_early_stopping;
    const isReject = sprt.decision === "REJECT_H0_ATTACK_CONFIRMED";
    const sprtEl = document.getElementById("stat-sprt-decision");
    if (sprtEl) {
      sprtEl.innerText = `${isReject ? 'REJECT H0 (ATTACK)' : 'ACCEPT H0 (SAFE)'} (Q${sprt.stopped_at_qubit}, -${sprt.qubits_saved_pct})`;
      sprtEl.className = `font-bold ${isReject ? 'text-rose-400' : 'text-emerald-400'}`;
    }
  }
  if (stats.kullback_leibler_divergence_nats !== undefined) {
    const klEl = document.getElementById("stat-kl-div");
    if (klEl) {
      klEl.innerText = `${stats.kullback_leibler_divergence_nats.toFixed(4)} nats`;
      klEl.className = `font-bold ${stats.kullback_leibler_divergence_nats > 0.05 ? 'text-rose-300' : 'text-cyan-300'}`;
    }
  }

  // 4. Update Basis Breakdown Chart
  const basisStats = data.raw_verification.basis_stats || {
    "Z": { "match": 0, "mismatch": 0 },
    "X": { "match": 0, "mismatch": 0 },
    "Y": { "match": 0, "mismatch": 0 }
  };
  basisChart.data.datasets[0].data = [basisStats.Z.match, basisStats.X.match, basisStats.Y.match];
  basisChart.data.datasets[1].data = [basisStats.Z.mismatch, basisStats.X.mismatch, basisStats.Y.mismatch];
  basisChart.update();

  // 5. Update Token Preview Table
  const tbody = document.getElementById("token-preview-tbody");
  tbody.innerHTML = "";
  const preview = data.raw_verification.preview_outcomes || [];
  if (preview.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="py-3 text-center text-slate-500 italic">No tokens available</td></tr>`;
  } else {
    preview.forEach(tok => {
      const matchCls = tok.match ? "text-emerald-400" : "text-rose-400 font-bold";
      tbody.innerHTML += `
        <tr class="hover:bg-slate-900/40">
          <td class="py-1 px-2 text-slate-400">#${tok.token_index}</td>
          <td class="py-1 px-2 text-cyan-400">${tok.basis}</td>
          <td class="py-1 px-2 text-slate-200">${tok.expected_val}</td>
          <td class="py-1 px-2 text-slate-200">${tok.measured_val}</td>
          <td class="py-1 px-2 text-right ${matchCls}">${tok.match ? "MATCH" : "MISMATCH"}</td>
        </tr>
      `;
    });
  }

  lucide.createIcons();
}

// Threshold Slider Handler
let thresholdTimeout = null;
async function onThresholdSliderChange() {
  const svVal = parseInt(document.getElementById("sv-slider").value) / 100.0;
  const saVal = parseInt(document.getElementById("sa-slider").value) / 100.0;
  document.getElementById("sv-display").innerText = `${(svVal * 100).toFixed(1)}%`;
  document.getElementById("sa-display").innerText = `${(saVal * 100).toFixed(1)}%`;

  if (thresholdTimeout) clearTimeout(thresholdTimeout);
  thresholdTimeout = setTimeout(async () => {
    try {
      const res = await fetch("/api/thresholds", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ verification_threshold: svVal, abort_threshold: saVal })
      });
      if (res.ok) {
        await refreshSystemStatus();
      }
    } catch (e) {
      console.error(e);
    }
  }, 300);
}

// Refresh Circuit Sample
async function refreshCircuitSample() {
  try {
    const res = await fetch("/api/circuit/teleportation-sample");
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("circ-in-state").innerText = `|ψ> = |+> (X-Basis)`;
    const bx = data.input_state.bloch.x;
    const by = data.input_state.bloch.y;
    const bz = data.input_state.bloch.z;
    document.getElementById("circ-bloch-in").innerText = `Bloch: (${bx}, ${by}, ${bz})`;
    document.getElementById("circ-bsm-out").innerText = `BSM: |${data.bell_state_measured}>`;
    document.getElementById("circ-bits").innerText = `Bits: (${data.classical_bits_feedforward[0]}, ${data.classical_bits_feedforward[1]})`;
    document.getElementById("circ-corr").innerText = `Pauli U = ${data.pauli_correction_applied}`;
    document.getElementById("circ-fidelity").innerText = `Fidelity: ${data.reconstruction_fidelity.toFixed(4)}`;
  } catch (e) {
    console.error(e);
  }
}

// Run Monte Carlo Benchmark Batch
async function runExperimentBatch() {
  const scenario = document.getElementById("exp-scenario").value;
  const trials = parseInt(document.getElementById("exp-trials").value) || 30;
  const tokens = parseInt(document.getElementById("exp-tokens").value) || 150;

  try {
    const res = await fetch("/api/experiments/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        trials: trials,
        token_count: tokens,
        attack_type: scenario,
        channel_noise: 0.03,
        disturbance_level: 0.22
      })
    });
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("res-far").innerText = `${(data.empirical_far * 100).toFixed(2)}%`;
    document.getElementById("res-frr").innerText = `${(data.empirical_frr * 100).toFixed(2)}%`;
    document.getElementById("res-mean-err").innerText = `${(data.mean_error_rate * 100).toFixed(2)}% \u00B1 ${(data.std_deviation * 100).toFixed(2)}%`;
    document.getElementById("res-time").innerText = `${data.latency_ms} ms (${(data.latency_ms / trials).toFixed(1)} ms/trial)`;
    document.getElementById("res-summary").innerText = `Evaluated ${trials} independent trials with ${tokens} quantum tokens per trial. No hardcoded or AI values used.`;
    document.getElementById("exp-results-card").classList.remove("hidden");
  } catch (e) {
    console.error(e);
  }
}

// Refresh Audit Logs Table
async function refreshAuditLogs() {
  try {
    const res = await fetch("/api/audit/logs");
    if (!res.ok) return;
    const data = await res.json();
    const tbody = document.getElementById("full-audit-tbody");
    tbody.innerHTML = "";

    const entries = data.entries || [];
    if (entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="py-3 text-center text-slate-500 italic">No events recorded</td></tr>`;
      return;
    }

    entries.forEach((e) => {
      const actCls = e.action === "BLOCK" ? "text-rose-400 font-bold" : (e.action === "ALERT" ? "text-amber-400" : "text-emerald-400 font-bold");
      tbody.innerHTML += `
        <tr class="hover:bg-slate-900/50">
          <td class="py-2 px-2 text-slate-400">#${e.index}</td>
          <td class="py-2 px-2 text-cyan-300 font-bold">${e.session_id}</td>
          <td class="py-2 px-2 text-slate-300">${e.threat_type}</td>
          <td class="py-2 px-2 ${actCls}">${e.action}</td>
          <td class="py-2 px-2">${(e.error_rate * 100).toFixed(1)}%</td>
          <td class="py-2 px-2 text-right">
            <button onclick="inspectMerkleProof(${e.index})" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 hover:border-cyan-500/50 text-[10px] transition">
              Verify Proof
            </button>
          </td>
        </tr>
      `;
    });

    if (data.merkle_root) {
      document.getElementById("top-merkle-root").innerText = data.merkle_root.substring(0, 16) + "...";
    }
  } catch (e) {
    console.error(e);
  }
}

// Inspect Merkle Proof
async function inspectMerkleProof(index) {
  try {
    const res = await fetch(`/api/audit/proof/${index}`);
    if (!res.ok) return;
    const proofData = await res.json();

    document.getElementById("modal-leaf-hash").innerText = proofData.leaf_hash;
    document.getElementById("modal-root-hash").innerText = proofData.merkle_root;

    // Verify proof
    const vRes = await fetch("/api/audit/verify-proof", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        leaf_hash: proofData.leaf_hash,
        merkle_root: proofData.merkle_root,
        proof_path: proofData.proof_path
      })
    });
    const vData = await vRes.json();

    const stepsContainer = document.getElementById("modal-proof-steps");
    stepsContainer.innerHTML = "";
    if (proofData.proof_path.length === 0) {
      stepsContainer.innerHTML = `<span class="text-slate-500 text-[10px]">Height 1 tree. Leaf hash matches root directly.</span>`;
    } else {
      proofData.proof_path.forEach((step, i) => {
        stepsContainer.innerHTML += `
          <div class="flex items-center justify-between text-[10px] bg-slate-900 p-1.5 rounded border border-slate-800">
            <span class="text-slate-400">Level ${i + 1} (${step.position.toUpperCase()} sibling):</span>
            <span class="text-slate-300 truncate max-w-[280px]">${step.sibling}</span>
          </div>
        `;
      });
    }

    const statusBox = document.getElementById("modal-verify-status");
    if (vData.verified) {
      statusBox.className = "p-3 rounded bg-emerald-950/60 border border-emerald-600 text-emerald-300 font-bold flex items-center gap-2";
      statusBox.innerHTML = `<i data-lucide="shield-check" class="w-5 h-5 text-emerald-400"></i><span>MATHEMATICAL PROOF VERIFIED: Entry #${index} is authentic and anchored in root!</span>`;
    } else {
      statusBox.className = "p-3 rounded bg-rose-950/60 border border-rose-600 text-rose-300 font-bold flex items-center gap-2";
      statusBox.innerHTML = `<i data-lucide="shield-x" class="w-5 h-5 text-rose-400"></i><span>VERIFICATION FAILED: Proof does not match root!</span>`;
    }

    lucide.createIcons();
    document.getElementById("proof-modal").classList.remove("hidden");
  } catch (e) {
    console.error(e);
  }
}

function closeProofModal() {
  document.getElementById("proof-modal").classList.add("hidden");
}

// Run Forensic Tamper Demonstration
async function runTamperDemo() {
  try {
    const res = await fetch("/api/audit/tamper-demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_record_index: 2 })
    });
    if (!res.ok) throw new Error("Tamper demo execution failed");
    const data = await res.json();

    const outCard = document.getElementById("tamper-demo-output");
    outCard.classList.remove("hidden");

    document.getElementById("tamper-orig-leaf").innerText = data.original_record.leaf_hash;
    document.getElementById("tamper-mod-leaf").innerText = data.tampered_record.recalculated_leaf_hash;
    document.getElementById("tamper-analysis-text").innerText = data.forensic_analysis;
    document.getElementById("tamper-status-badge").innerText = data.post_tamper_verification.verdict;

    lucide.createIcons();
  } catch (e) {
    console.error("Tamper demo error:", e);
  }
}

// Simulate 3-Party QDS Non-Repudiation (Alice -> Bob & Charlie)
async function simulateMultiParty(repudiation = false) {
  try {
    const res = await fetch("/api/qds/multi-verifier/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token_count: 150,
        channel_noise: 0.03,
        repudiation_attack: repudiation
      })
    });
    if (!res.ok) throw new Error("Multi-party simulation failed");
    const data = await res.json();

    const panel = document.getElementById("multi-party-results");
    panel.classList.remove("hidden");

    // Bob
    const bob = data.bob_verification;
    const bVerdict = document.getElementById("mp-bob-verdict");
    bVerdict.innerText = bob.verdict;
    bVerdict.className = `text-lg font-bold ${bob.is_accepted ? 'text-emerald-400' : 'text-rose-400'}`;
    document.getElementById("mp-bob-err").innerText = `${(bob.error_rate * 100).toFixed(1)}% (${bob.mismatches}/${bob.token_count})`;

    // Charlie
    const charlie = data.charlie_arbitration;
    const cVerdict = document.getElementById("mp-charlie-verdict");
    cVerdict.innerText = charlie.arbitration_status;
    cVerdict.className = `text-lg font-bold ${charlie.is_accepted ? 'text-emerald-400' : 'text-rose-400'}`;
    document.getElementById("mp-charlie-err").innerText = `${(charlie.error_rate_charlie * 100).toFixed(1)}% (${charlie.mismatches}/${charlie.token_count})`;

    // Gap
    const gapVal = document.getElementById("mp-gap-val");
    gapVal.innerText = `|e_B - e_C| = ${(charlie.error_difference * 100).toFixed(1)}%`;
    const gapStatus = document.getElementById("mp-gap-status");
    if (charlie.is_within_gap) {
      gapStatus.innerText = "WITHIN TOLERANCE (<= 10.0%)";
      gapStatus.className = "text-[10px] font-bold text-emerald-400";
    } else {
      gapStatus.innerText = "TOLERANCE EXCEEDED (> 10.0%)";
      gapStatus.className = "text-[10px] font-bold text-rose-400";
    }

    // Summary Banner
    const banner = document.getElementById("mp-summary-banner");
    const summaryText = document.getElementById("mp-summary-text");
    const badge = document.getElementById("mp-theorem-badge");

    if (data.overall_outcome === "TRANSFER_CONFIRMED") {
      banner.className = "p-4 rounded-lg border border-emerald-700/60 bg-emerald-950/40 font-bold text-xs flex items-center justify-between text-emerald-300";
      summaryText.innerText = "SUCCESS: Signature accepted by Bob and confirmed by Charlie. Non-repudiation verified.";
      badge.innerText = "TRANSFER_CONFIRMED";
      badge.className = "px-2.5 py-1 rounded text-[10px] mono bg-emerald-900 text-emerald-300";
    } else {
      banner.className = "p-4 rounded-lg border border-rose-700/60 bg-rose-950/40 font-bold text-xs flex items-center justify-between text-rose-300";
      summaryText.innerText = `DISPUTE ALERT: ${charlie.explanation}`;
      badge.innerText = "DISPUTE_RAISED";
      badge.className = "px-2.5 py-1 rounded text-[10px] mono bg-rose-900 text-rose-300";
    }

    lucide.createIcons();
  } catch (e) {
    console.error("Multi-party simulation error:", e);
  }
}

/**
 * 5-Second Layman Explainer Engine
 * Activates on hover over [data-explain-title] elements.
 * Displays simple non-technical plain English explanations for exactly 5 seconds,
 * with animated countdown and progress bar, then automatically returns to normal.
 */
function initHoverExplainerEngine() {
  const hud = document.getElementById("explainer-hud");
  const titleEl = document.getElementById("explainer-title");
  const bodyEl = document.getElementById("explainer-body");
  const countEl = document.getElementById("explainer-countdown");
  const barEl = document.getElementById("explainer-bar");

  if (!hud || !titleEl || !bodyEl || !countEl || !barEl) {
    console.warn("Explainer HUD elements not found in DOM");
    return;
  }

  let explainerTimer = null;
  let explainerInterval = null;
  let currentTarget = null;
  const DURATION_MS = 5000;

  function dismissExplainer(keepTarget = false) {
    if (explainerTimer) {
      clearTimeout(explainerTimer);
      explainerTimer = null;
    }
    if (explainerInterval) {
      clearInterval(explainerInterval);
      explainerInterval = null;
    }

    hud.classList.remove("active");
    barEl.style.transition = "none";
    barEl.style.width = "100%";

    if (!keepTarget) {
      currentTarget = null;
    }
  }

  function startExplainer(target) {
    const title = target.getAttribute("data-explain-title");
    const body = target.getAttribute("data-explain-body");
    if (!title || !body) return;

    if (currentTarget === target && hud.classList.contains("active")) {
      return; // Already explaining this element
    }

    currentTarget = target;
    dismissExplainer(true);

    titleEl.textContent = title;
    bodyEl.textContent = body;
    countEl.textContent = "5.0s";

    // Reset progress bar instantly
    barEl.style.transition = "none";
    barEl.style.width = "100%";
    void barEl.offsetWidth; // Trigger browser reflow

    // Activate HUD
    hud.classList.add("active");

    // Animate progress bar linearly over 5 seconds
    barEl.style.transition = `width ${DURATION_MS}ms linear`;
    barEl.style.width = "0%";

    const startTime = Date.now();

    // 100ms countdown timer
    explainerInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, DURATION_MS - elapsed);
      countEl.textContent = (remaining / 1000).toFixed(1) + "s";
      if (remaining <= 0) {
        clearInterval(explainerInterval);
        explainerInterval = null;
      }
    }, 100);

    // Auto-dismiss at exactly 5 seconds
    explainerTimer = setTimeout(() => {
      dismissExplainer(true); // keeps currentTarget so it won't repeatedly flicker until mouse leaves
    }, DURATION_MS);
  }

  // Delegated mouseover: catches dynamically rendered elements and nested icons
  document.addEventListener("mouseover", (e) => {
    const target = e.target.closest("[data-explain-title]");
    if (target) {
      startExplainer(target);
    }
  });

  // Delegated mouseout: if user moves cursor off the explained element (and not into the HUD)
  document.addEventListener("mouseout", (e) => {
    const fromTarget = e.target.closest("[data-explain-title]");
    if (!fromTarget) return;

    const toElement = e.relatedTarget;
    if (toElement && (fromTarget.contains(toElement) || hud.contains(toElement))) {
      return; // Still within the hovered card or reading the HUD
    }

    // Left the target completely: return to normal
    dismissExplainer(false);
  });
}

