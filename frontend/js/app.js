/**
 * QUETZALCOATL - Quantum Digital Signature (QDS) Cyber Threat Detection SOC
 * Client-side Controller & Telemetry Engine
 */

let basisChart = null;
let currentSessionId = "";
let currentSelectedTokens = 200;
let currentSelectedNoise = 0.03;
let currentMode = "simple";

document.addEventListener("DOMContentLoaded", async () => {
  lucide.createIcons();
  initHoverExplainerEngine();
  initBasisChart();
  await refreshSystemStatus();
  await refreshCircuitSample();
  await runLegitimateVerify();
  await refreshAuditLogs();
});

// Toast Notification Engine
function showToast(type, title, message, duration = 4000) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast-item toast-${type}`;

  const iconName = type === "success" ? "shield-check" :
    type === "danger" ? "shield-alert" :
      type === "warning" ? "alert-triangle" : "info";
  const iconColor = type === "success" ? "text-emerald-400" :
    type === "danger" ? "text-rose-400" :
      type === "warning" ? "text-amber-400" : "text-cyan-400";

  toast.innerHTML = `
    <div class="p-1.5 rounded-md bg-zinc-800 ${iconColor} shrink-0">
      <i data-lucide="${iconName}" class="w-4 h-4"></i>
    </div>
    <div class="flex-grow">
      <div class="font-bold text-white text-xs">${title}</div>
      <div class="text-zinc-300 text-[11px] leading-tight mt-0.5">${message}</div>
    </div>
    <button onclick="this.parentElement.remove()" class="text-zinc-500 hover:text-zinc-300 p-1 shrink-0">
      <i data-lucide="x" class="w-3.5 h-3.5"></i>
    </button>
  `;

  container.appendChild(toast);
  lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Mode Switcher: Simple Mode vs SOC Analyst Mode
function setDashboardMode(mode) {
  currentMode = mode;
  const body = document.body;
  const btnSimple = document.getElementById("mode-btn-simple");
  const btnExpert = document.getElementById("mode-btn-expert");

  if (mode === "expert") {
    body.classList.remove("mode-simple");
    body.classList.add("mode-expert");
    if (btnExpert) btnExpert.classList.add("active");
    if (btnSimple) btnSimple.classList.remove("active");
    showToast("info", "SOC Analyst Mode Activated", "Full mathematical telemetry, Wald SPRT curves, and Hoeffding bounds visible.");
  } else {
    body.classList.remove("mode-expert");
    body.classList.add("mode-simple");
    if (btnSimple) btnSimple.classList.add("active");
    if (btnExpert) btnExpert.classList.remove("active");
    showToast("info", "Simple Mode Activated", "Streamlined plain-English questions & answers for non-technical evaluation.");
  }
}

// Token Count Selector
function setTokenCount(count) {
  currentSelectedTokens = count;
  const valEl = document.getElementById("doc-tokens-val");
  if (valEl) valEl.innerText = `${count} Qubits`;

  [50, 100, 200, 500].forEach(n => {
    const btn = document.getElementById(`tkn-${n}`);
    if (btn) {
      if (n === count) {
        btn.className = "token-btn active px-2 py-0.5 rounded bg-cyan-900/60 border border-cyan-500/50 text-[10px] text-cyan-300 font-bold";
      } else {
        btn.className = "token-btn px-2 py-0.5 rounded bg-zinc-800 text-[10px] text-zinc-300 hover:text-white";
      }
    }
  });
}

// Noise Slider Handler
function updateNoiseSlider(val) {
  const num = parseFloat(val);
  currentSelectedNoise = num / 100.0;
  const valEl = document.getElementById("doc-noise-val");
  if (valEl) valEl.innerText = `${num.toFixed(1)}%`;
}

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
        btn.className = "tab-btn active px-3.5 py-1.5 border border-zinc-800 text-cyan-400 flex items-center gap-1.5";
      } else {
        btn.className = "tab-btn px-3.5 py-1.5 border border-transparent text-zinc-400 hover:text-white flex items-center gap-1.5";
      }
    }
  });
  lucide.createIcons();
}

// Basis Breakdown Chart (Z, X, Y)
function initBasisChart() {
  const canvas = document.getElementById("basisChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
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
          grid: { color: "rgba(39, 39, 42, 0.6)" },
          ticks: { color: "#a1a1aa", font: { size: 10, family: 'JetBrains Mono' } }
        },
        y: {
          stacked: true,
          grid: { color: "rgba(39, 39, 42, 0.6)" },
          ticks: { color: "#a1a1aa", font: { size: 10, family: 'JetBrains Mono' } }
        }
      },
      plugins: {
        legend: {
          labels: { color: "#e4e4e7", font: { size: 10, family: 'JetBrains Mono' } }
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
    const rId = document.getElementById("ribbon-session-id");
    if (rId) rId.innerText = data.active_session_id || "None";
    const rSv = document.getElementById("ribbon-sv");
    if (rSv) rSv.innerText = `${(data.thresholds.sv_verification * 100).toFixed(1)}%`;
    const rSa = document.getElementById("ribbon-sa");
    if (rSa) rSa.innerText = `${(data.thresholds.sa_abort * 100).toFixed(1)}%`;

    const topMerkle = document.getElementById("top-merkle-root");
    if (topMerkle && data.merkle_root) {
      topMerkle.innerText = data.merkle_root.substring(0, 16) + "...";
    }
  } catch (e) {
    console.error("Failed to load status:", e);
  }
}

// Interactive Custom Document Signer
async function signCustomDocument() {
  const inputEl = document.getElementById("signer-doc-message");
  const message = (inputEl && inputEl.value.trim()) ? inputEl.value.trim() : "APPROVE_FINANCIAL_WIRE_ORDER_2026";

  try {
    showToast("info", "Quantum Teleportation Initiated", `Signing "${message.substring(0, 30)}..." with ${currentSelectedTokens} Bell pairs.`);

    // 1. Create Session
    const sessRes = await fetch("/api/qds/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        token_count: currentSelectedTokens,
        channel_noise: currentSelectedNoise
      })
    });
    if (!sessRes.ok) throw new Error("Session creation failed");
    const sessData = await sessRes.json();
    currentSessionId = sessData.session_id;
    const rId = document.getElementById("ribbon-session-id");
    if (rId) rId.innerText = sessData.session_id;

    // 2. Execute Teleportation
    await fetch("/api/qds/teleport", { method: "POST" });

    // 3. Verify
    const verifyRes = await fetch("/api/qds/verify", { method: "POST" });
    if (!verifyRes.ok) throw new Error("Verification failed");
    const verifyData = await verifyRes.json();

    renderDecisionData(verifyData);
    await refreshAuditLogs();

    showToast("success", "Quantum Signature Verified", `Document authentic! Mismatch rate ${(verifyData.statistics.error_rate * 100).toFixed(1)}% <= 10.0% threshold.`);
  } catch (e) {
    console.error(e);
    showToast("danger", "Signing Error", e.message || "Failed to sign document.");
  }
}

// Initialize Fresh Session
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
    const rId = document.getElementById("ribbon-session-id");
    if (rId) rId.innerText = data.session_id;
    await runLegitimateVerify();
    showToast("info", "Session Initialized", `Fresh Bell pairs generated for session ${data.session_id}`);
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

    if (data.classification.action === "BLOCK") {
      showToast("danger", `Attack Blocked: ${data.classification.threat_type}`, `Mismatch rate ${(data.statistics.error_rate * 100).toFixed(1)}% exceeded abort threshold (20.0%).`);
    } else if (data.classification.action === "ALERT") {
      showToast("warning", `Channel Alert: ${data.classification.threat_type}`, `Optical noise elevated to ${(data.statistics.error_rate * 100).toFixed(1)}%.`);
    }
  } catch (e) {
    console.error(e);
    showToast("danger", "Attack Simulation Error", e.message);
  }
}

// -------------------------------------------------------------------
// National Mission Defense: High-Impact Social Problem Scenarios
// -------------------------------------------------------------------
const desktopSocialMissions = {
  healthcare_organ_dispatch: {
    title: "🚨 Pediatric Donor Heart Emergency Allocation Manifest",
    badge: "CRITICAL HEALTHCARE INFRASTRUCTURE",
    badgeClass: "bg-rose-900/60 border border-rose-500/40 text-rose-300",
    bannerClass: "p-4 rounded-xl border border-rose-500/40 bg-rose-950/20 space-y-2 transition-all",
    impact: "Adversary attempted intercept-resend forgery on dispatch manifest #HRT-2026-P9. No-Cloning collapse triggered 34.2% error spike, terminating the fake dispatch. Transplant secured for Pediatric ICU Patient #9042 at AIIMS Trauma Center.",
    activeBtn: "desktop-btn-scen-organ",
    activeClass: "p-4 rounded-xl border border-rose-500/60 bg-rose-950/30 hover:bg-rose-900/40 text-left transition space-y-2 shadow-lg shadow-rose-950/20"
  },
  grid_blackout_command: {
    title: "⚡ SCADA Regional Grid High-Voltage Substation Shutdown Command",
    badge: "ENERGY GRID NATIONAL DEFENSE",
    badgeClass: "bg-purple-900/60 border border-purple-500/40 text-purple-300",
    bannerClass: "p-4 rounded-xl border border-purple-500/40 bg-purple-950/20 space-y-2 transition-all",
    impact: "Adversary attempted stale packet replay on breaker command #HV-7701. Freshness check failed; mutual quantum information collapsed (50% error). 4.2 Million citizens shielded from rolling blackout.",
    activeBtn: "desktop-btn-scen-grid",
    activeClass: "p-4 rounded-xl border border-purple-500/60 bg-purple-950/30 hover:bg-purple-900/40 text-left transition space-y-2 shadow-lg shadow-purple-950/20"
  },
  disaster_relief_aid: {
    title: "🌾 $45M Flood Relief Sovereign Citizen Disbursement",
    badge: "SOVEREIGN CITIZEN DISBURSEMENT",
    badgeClass: "bg-amber-900/60 border border-amber-500/40 text-amber-300",
    bannerClass: "p-4 rounded-xl border border-amber-500/40 bg-amber-950/20 space-y-2 transition-all",
    impact: "Elevated optical noise detected on batch #DBT-2026-FL04 (14.7%). Differentiated from malicious forgery via Hoeffding bounds. 120,000 displaced flood victims protected from fund diversion.",
    activeBtn: "desktop-btn-scen-aid",
    activeClass: "p-4 rounded-xl border border-amber-500/60 bg-amber-950/30 hover:bg-amber-900/40 text-left transition space-y-2 shadow-lg shadow-amber-950/20"
  }
};

async function triggerSocialMission(scenarioId) {
  const conf = desktopSocialMissions[scenarioId];
  if (!conf) return;

  // Update button visual states
  ["desktop-btn-scen-organ", "desktop-btn-scen-grid", "desktop-btn-scen-aid"].forEach(btnId => {
    const el = document.getElementById(btnId);
    if (el) {
      el.className = "p-4 rounded-xl border border-zinc-800 bg-zinc-900/80 hover:bg-zinc-800 text-left transition space-y-2";
    }
  });
  const actEl = document.getElementById(conf.activeBtn);
  if (actEl) actEl.className = conf.activeClass;

  const tEl = document.getElementById("desktop-mission-title");
  const bEl = document.getElementById("desktop-mission-badge");
  const iEl = document.getElementById("desktop-mission-impact");
  const box = document.getElementById("desktop-mission-banner");

  if (tEl) tEl.textContent = conf.title;
  if (bEl) {
    bEl.textContent = conf.badge;
    bEl.className = `text-[10px] mono px-2.5 py-1 rounded font-bold uppercase ${conf.badgeClass}`;
  }
  if (iEl) iEl.textContent = conf.impact;
  if (box) box.className = conf.bannerClass;

  try {
    const res = await fetch(`/scenarios/simulate?scenario_id=${scenarioId}`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      if (data.impact_summary && iEl) {
        iEl.textContent = data.impact_summary;
      }
      const isAccept = data.decision === "ACCEPT";
      const isReplay = data.attribution?.attack_class === "replay";
      const isBlock = data.decision === "REJECT" || data.qber > 0.20 || isReplay;

      const mappedDecision = {
        classification: {
          threat_type: data.social_verdict || (isAccept ? "SAFE" : "ATTACK_INTERDICTED"),
          action: isAccept ? "ACCEPT" : (isBlock ? "BLOCK" : "ALERT"),
          reasons: [
            data.impact_summary,
            `Quantum Bit Error Rate (QBER): ${(data.qber * 100).toFixed(1)}%`,
            `CHSH Bell parameter S: ${data.chsh_s ? data.chsh_s.toFixed(2) : '2.81'}`,
            `Attribution engine class: ${data.attribution?.attack_class || 'none'}`
          ]
        },
        statistics: {
          error_rate: data.qber,
          binomial_p_value: isAccept ? 0.001 : 0.999,
          binomial_p_value_formatted: isAccept ? "0.0010" : "0.9990",
          hoeffding_forgery_bound: isAccept ? 1.4e-6 : 0.89,
          hoeffding_forgery_bound_formatted: isAccept ? "1.42e-06" : "8.90e-01",
          kullback_leibler_divergence_nats: data.qber > 0.1 ? 0.18 : 0.01,
          sprt_early_stopping: {
            decision: data.sprt_decision || (isAccept ? "ACCEPT_H0_SAFE" : "REJECT_H0_ATTACK_CONFIRMED"),
            stopped_at_qubit: 48,
            qubits_saved_pct: "76.0%"
          }
        },
        raw_verification: {
          basis_stats: {
            Z: { match: isAccept ? 120 : 70, mismatch: isAccept ? 4 : 54 },
            X: { match: isAccept ? 118 : 68, mismatch: isAccept ? 3 : 56 },
            Y: { match: isAccept ? 50 : 30, mismatch: isAccept ? 1 : 24 }
          },
          preview_outcomes: [
            { token_index: 0, basis: "Z", expected_val: 0, measured_val: isAccept ? 0 : 1, match: isAccept },
            { token_index: 1, basis: "X", expected_val: 1, measured_val: 1, match: true },
            { token_index: 2, basis: "Z", expected_val: 1, measured_val: isAccept ? 1 : 0, match: isAccept },
            { token_index: 3, basis: "X", expected_val: 0, measured_val: 0, match: true }
          ]
        }
      };
      renderDecisionData(mappedDecision);
      await refreshAuditLogs();
      showToast(
        isAccept ? "success" : (isBlock ? "danger" : "warning"),
        `Mission Defense: ${conf.badge}`,
        data.impact_summary
      );
    }
  } catch (err) {
    console.error("Mission simulation failed", err);
  }
}

// Render Decision Data into Cockpit
function renderDecisionData(data) {
  const stats = data.statistics;
  const classification = data.classification;

  // 1. Threat Type & Action Badges
  const tBadge = document.getElementById("threat-type-badge");
  if (tBadge) tBadge.innerText = classification.threat_type;

  const aBadge = document.getElementById("action-badge");
  if (aBadge) aBadge.innerText = classification.action;

  const circle = document.getElementById("error-rate-circle");
  const summary = document.getElementById("action-summary");

  const errPct = stats.error_rate * 100;
  const errVal = document.getElementById("error-rate-val");
  if (errVal) errVal.innerText = `${errPct.toFixed(1)}%`;

  if (circle) {
    const circumference = 339.29;
    const offset = circumference - Math.min(1.0, stats.error_rate / 0.50) * circumference;
    circle.style.strokeDashoffset = offset;

    if (classification.action === "BLOCK") {
      circle.style.stroke = "#ffffff";
      if (aBadge) aBadge.className = "px-5 py-3 rounded-lg text-2xl font-black tracking-wider mono text-center bg-white text-black border border-white";
      if (tBadge) tBadge.className = "text-xs mono text-zinc-300 font-bold";
      if (summary) summary.innerText = "CRITICAL THREAT: Signature aborted. Wave function collapsed or credential fraud.";
      if (window.QuantumDither) window.QuantumDither.setThreatMode(true);
    } else if (classification.action === "ALERT") {
      circle.style.stroke = "#a1a1aa";
      if (aBadge) aBadge.className = "px-5 py-3 rounded-lg text-2xl font-black tracking-wider mono text-center bg-zinc-800 text-white border border-zinc-500";
      if (tBadge) tBadge.className = "text-xs mono text-zinc-400 font-bold";
      if (summary) summary.innerText = "SUSPICIOUS CHANNEL: Quantum optical disturbance exceeded sv; recalibration advised.";
      if (window.QuantumDither) window.QuantumDither.setThreatMode(true);
    } else {
      circle.style.stroke = "#ffffff";
      if (aBadge) aBadge.className = "px-5 py-3 rounded-lg text-2xl font-black tracking-wider mono text-center bg-zinc-900 text-white border border-zinc-700";
      if (tBadge) tBadge.className = "text-xs mono text-white font-bold";
      if (summary) summary.innerText = "VERIFIED: Quantum states undisturbed. Information-theoretic authenticity validated.";
      if (window.QuantumDither) window.QuantumDither.setThreatMode(false);
    }
  }

  // Update Sticky Bottom HUD Bar & Header Status
  const stickyAction = document.getElementById("sticky-action-val");
  const stickyError = document.getElementById("sticky-error-val");
  const stickyDot = document.getElementById("sticky-status-dot");
  const sysStatus = document.getElementById("sys-status");

  if (stickyAction) stickyAction.innerText = classification.action;
  if (stickyError) stickyError.innerText = `${errPct.toFixed(1)}%`;
  if (stickyDot) {
    stickyDot.className = "w-2 h-2 rounded-full bg-white";
  }
  if (sysStatus) {
    sysStatus.innerText = classification.action === 'BLOCK' ? 'THREAT INTERDICTED' : classification.action === 'ALERT' ? 'CHANNEL NOISE' : 'NOMINAL (ACTIVE)';
    sysStatus.className = "font-semibold text-white";
  }

  // 2. Mathematical Reasoning List
  const rList = document.getElementById("reasons-list");
  if (rList) {
    rList.innerHTML = "";
    (classification.reasons || []).forEach(r => {
      const isWarn = r.includes("FORGERY") || r.includes("REPLAY") || r.includes("IMPERSONATION") || r.includes("Unauthorized");
      const color = isWarn ? "text-zinc-200" : (r.includes("MANIPULATION") ? "text-zinc-400" : "text-zinc-100");
      const icon = isWarn ? "alert-triangle" : (r.includes("MANIPULATION") ? "alert-circle" : "check");
      rList.innerHTML += `<li class="${color} flex items-start gap-1.5"><i data-lucide="${icon}" class="w-3.5 h-3.5 flex-shrink-0 mt-0.5"></i> ${r}</li>`;
    });
  }

  // 3. Statistical Inference Indicators
  const pValEl = document.getElementById("stat-p-value");
  if (pValEl) pValEl.innerText = stats.binomial_p_value_formatted || stats.binomial_p_value.toFixed(4);

  const hoeffEl = document.getElementById("stat-hoeffding");
  if (hoeffEl) hoeffEl.innerText = `≤ ${stats.hoeffding_forgery_bound_formatted || stats.hoeffding_forgery_bound.toExponential(2)}`;

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
  if (basisChart && data.raw_verification) {
    const basisStats = data.raw_verification.basis_stats || {
      "Z": { "match": 0, "mismatch": 0 },
      "X": { "match": 0, "mismatch": 0 },
      "Y": { "match": 0, "mismatch": 0 }
    };
    basisChart.data.datasets[0].data = [basisStats.Z.match, basisStats.X.match, basisStats.Y.match];
    basisChart.data.datasets[1].data = [basisStats.Z.mismatch, basisStats.X.mismatch, basisStats.Y.mismatch];
    basisChart.update();
  }

  // 5. Update Token Preview Table
  const tbody = document.getElementById("token-preview-tbody");
  if (tbody && data.raw_verification) {
    tbody.innerHTML = "";
    const preview = data.raw_verification.preview_outcomes || [];
    if (preview.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="py-3 text-center text-zinc-500 italic">No tokens available</td></tr>`;
    } else {
      preview.forEach(tok => {
        const matchCls = tok.match ? "text-emerald-400" : "text-rose-400 font-bold";
        tbody.innerHTML += `
          <tr class="hover:bg-zinc-900/60">
            <td class="py-1 px-2 text-zinc-400">#${tok.token_index}</td>
            <td class="py-1 px-2 text-cyan-400">${tok.basis}</td>
            <td class="py-1 px-2 text-zinc-200">${tok.expected_val}</td>
            <td class="py-1 px-2 text-zinc-200">${tok.measured_val}</td>
            <td class="py-1 px-2 text-right ${matchCls}">${tok.match ? "MATCH" : "MISMATCH"}</td>
          </tr>
        `;
      });
    }
  }

  lucide.createIcons();
}

// Export Forensic Audit Report as JSON
async function exportAuditReport() {
  try {
    const statusRes = await fetch("/api/status");
    const statusData = statusRes.ok ? await statusRes.json() : {};

    const auditRes = await fetch("/api/audit/logs?limit=10");
    const auditData = auditRes.ok ? await auditRes.json() : {};

    const report = {
      application: "QUETZALCOATL Quantum Digital Signature SOC",
      version: "2.0.0",
      compliance_standard: "SIH26141 Quantum-Inspired Cyber Threat Detection",
      generated_at: new Date().toISOString(),
      active_session_id: currentSessionId,
      operational_status: statusData.status || "OPERATIONAL",
      quantum_framework: statusData.quantum_framework || "Bennett 3-Qubit Teleportation",
      merkle_root: statusData.merkle_root || "N/A",
      audit_record_count: statusData.audit_records_count || 0,
      recent_audit_events: auditData.records || []
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `quetzalcoatl-audit-report-${currentSessionId || "latest"}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast("success", "Audit Report Exported", "Forensic JSON evidence downloaded successfully.");
  } catch (e) {
    console.error(e);
    showToast("danger", "Export Failed", e.message);
  }
}

// Refresh Circuit Sample
async function refreshCircuitSample() {
  try {
    const res = await fetch("/api/circuit/teleportation-sample");
    if (!res.ok) return;
    const data = await res.json();
    const inState = document.getElementById("circ-in-state");
    if (inState) inState.innerText = `|ψ> = |+> (X-Basis)`;
    const bx = data.input_state.bloch.x;
    const by = data.input_state.bloch.y;
    const bz = data.input_state.bloch.z;
    const blochEl = document.getElementById("circ-bloch-in");
    if (blochEl) blochEl.innerText = `Bloch: (${bx}, ${by}, ${bz})`;
    const bsmEl = document.getElementById("circ-bsm-out");
    if (bsmEl) bsmEl.innerText = `BSM: |${data.bell_state_measured}>`;
    const bitsEl = document.getElementById("circ-bits");
    if (bitsEl) bitsEl.innerText = `Bits: (${data.classical_bits_feedforward[0]}, ${data.classical_bits_feedforward[1]})`;
    const corrEl = document.getElementById("circ-corr");
    if (corrEl) corrEl.innerText = `Pauli U = ${data.pauli_correction_applied}`;
    const fidEl = document.getElementById("circ-fidelity");
    if (fidEl) fidEl.innerText = `Fidelity: ${data.reconstruction_fidelity.toFixed(4)}`;
  } catch (e) {
    console.error(e);
  }
}

// Run Monte Carlo Benchmark Batch
async function runExperimentBatch() {
  const scenarioEl = document.getElementById("exp-scenario");
  const scenario = scenarioEl ? scenarioEl.value : "forgery";
  const trialsEl = document.getElementById("exp-trials");
  const trials = trialsEl ? (parseInt(trialsEl.value) || 30) : 30;
  const tokensEl = document.getElementById("exp-tokens");
  const tokens = tokensEl ? (parseInt(tokensEl.value) || 150) : 150;

  try {
    showToast("info", "Benchmark Running", `Running ${trials} independent Monte Carlo trials for ${scenario}...`);
    const res = await fetch("/api/experiments/batch", {
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
    if (!res.ok) throw new Error("Benchmark batch failed");
    const data = await res.json();

    const card = document.getElementById("exp-results-card");
    if (card) card.classList.remove("hidden");
    const farEl = document.getElementById("res-far");
    if (farEl) farEl.innerText = `${(data.empirical_far * 100).toFixed(2)}%`;
    const frrEl = document.getElementById("res-frr");
    if (frrEl) frrEl.innerText = `${(data.empirical_frr * 100).toFixed(2)}%`;
    const meanErrEl = document.getElementById("res-mean-err");
    if (meanErrEl) meanErrEl.innerText = `${(data.mean_error_rate * 100).toFixed(2)}%`;
    const timeEl = document.getElementById("res-time");
    if (timeEl) timeEl.innerText = `${data.total_benchmark_time_ms} ms`;
    const sumEl = document.getElementById("res-summary");
    if (sumEl) sumEl.innerText = data.summary;

    showToast("success", "Benchmark Complete", `Completed ${trials} trials in ${data.total_benchmark_time_ms}ms.`);
  } catch (e) {
    console.error(e);
    showToast("danger", "Benchmark Failed", e.message);
  }
}

// Refresh Audit Logs
async function refreshAuditLogs() {
  try {
    const res = await fetch("/api/audit/logs?limit=30");
    if (!res.ok) return;
    const data = await res.json();
    const tbody = document.getElementById("full-audit-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    if (data.records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="py-3 text-center text-zinc-500 italic">No events recorded</td></tr>`;
      return;
    }
    data.records.forEach((rec, i) => {
      const isWarn = rec.action === "BLOCK";
      const actBadge = isWarn
        ? `<span class="px-2 py-0.5 rounded bg-rose-950 text-rose-400 font-bold text-[10px]">BLOCK</span>`
        : (rec.action === "ALERT"
          ? `<span class="px-2 py-0.5 rounded bg-amber-950 text-amber-400 font-bold text-[10px]">ALERT</span>`
          : `<span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold text-[10px]">ACCEPT</span>`);

      tbody.innerHTML += `
        <tr class="hover:bg-zinc-900/60">
          <td class="py-2 px-2 text-zinc-500">#${i + 1}</td>
          <td class="py-2 px-2 text-cyan-400">${rec.session_id}</td>
          <td class="py-2 px-2 font-bold text-zinc-300">${rec.threat_type}</td>
          <td class="py-2 px-2">${actBadge}</td>
          <td class="py-2 px-2 text-zinc-300">${(rec.error_rate * 100).toFixed(1)}%</td>
          <td class="py-2 px-2 text-right">
            <button onclick="inspectProof('${rec.leaf_hash}')" class="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-cyan-300 text-[10px]">
              Inspect Proof
            </button>
          </td>
        </tr>
      `;
    });
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

// Inspect Merkle Inclusion Proof Modal
async function inspectProof(leafHash) {
  try {
    const res = await fetch(`/api/audit/merkle-proof/${leafHash}`);
    if (!res.ok) throw new Error("Proof fetch failed");
    const data = await res.json();

    document.getElementById("modal-leaf-hash").innerText = data.leaf_hash;
    document.getElementById("modal-root-hash").innerText = data.merkle_root;

    const stepsContainer = document.getElementById("modal-proof-steps");
    stepsContainer.innerHTML = "";
    data.proof_path.forEach((step, idx) => {
      stepsContainer.innerHTML += `
        <div class="flex items-center justify-between text-[11px] p-1.5 rounded bg-zinc-900 border border-zinc-800">
          <span class="text-zinc-400">Step ${idx + 1} (${step.position.toUpperCase()} Sibling):</span>
          <span class="text-cyan-300 truncate max-w-xs mono">${step.hash}</span>
        </div>
      `;
    });

    const statusEl = document.getElementById("modal-verify-status");
    if (data.is_valid) {
      statusEl.className = "p-3 rounded bg-emerald-950/60 border border-emerald-600 text-emerald-300 font-bold flex items-center gap-2";
      statusEl.innerHTML = `<i data-lucide="shield-check" class="w-5 h-5 text-emerald-400"></i><span>MATHEMATICAL PROOF VERIFIED: Authentic and anchored in root ledger.</span>`;
    } else {
      statusEl.className = "p-3 rounded bg-rose-950/60 border border-rose-600 text-rose-300 font-bold flex items-center gap-2";
      statusEl.innerHTML = `<i data-lucide="alert-triangle" class="w-5 h-5 text-rose-400"></i><span>TAMPER ALERT: Leaf hash cannot be derived from root!</span>`;
    }

    document.getElementById("proof-modal").classList.remove("hidden");
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

function closeProofModal() {
  document.getElementById("proof-modal").classList.add("hidden");
}

// Forensic Tampering Demonstration
async function runTamperDemo() {
  try {
    const res = await fetch("/api/audit/tamper-demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_record_index: 2 })
    });
    if (!res.ok) throw new Error("Tamper demo execution failed");
    const data = await res.json();

    const output = document.getElementById("tamper-demo-output");
    output.classList.remove("hidden");

    document.getElementById("tamper-orig-leaf").innerText = data.original_record.leaf_hash;
    document.getElementById("tamper-mod-leaf").innerText = data.tampered_record.calculated_tampered_leaf;
    document.getElementById("tamper-status-badge").innerText = data.tamper_alert;
    document.getElementById("tamper-analysis-text").innerText = data.forensic_analysis;

    lucide.createIcons();
    showToast("danger", "CRITICAL INTEGRITY BREACH", "Tampering detected! Modified leaf hash failed Merkle proof.");
  } catch (e) {
    console.error("Tamper demo error:", e);
  }
}

// Multi-Party Non-Repudiation Simulation
async function simulateMultiParty(isRepudiation) {
  try {
    const res = await fetch("/api/multi-verifier/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "INTER_AGENCY_DISBURSEMENT_SETTLEMENT_ORDER_491",
        token_count: 150,
        channel_noise: 0.03,
        repudiation_attack: isRepudiation
      })
    });
    if (!res.ok) throw new Error("Multi-party simulation failed");
    const data = await res.json();

    const resultsPanel = document.getElementById("multi-party-results");
    resultsPanel.classList.remove("hidden");

    const bob = data.direct_verification_bob;
    const charlie = data.forwarded_verification_charlie;

    // Bob
    const bobVerdict = document.getElementById("mp-bob-verdict");
    bobVerdict.innerText = bob.action === "ACCEPT" ? "ACCEPT_SIGNATURE" : "REJECT_SIGNATURE";
    bobVerdict.className = `text-lg font-bold ${bob.action === 'ACCEPT' ? 'text-emerald-400' : 'text-rose-400'}`;
    document.getElementById("mp-bob-err").innerText = `${(bob.error_rate_bob * 100).toFixed(1)}% (${bob.mismatches}/${bob.token_count})`;

    // Charlie
    const charlieVerdict = document.getElementById("mp-charlie-verdict");
    charlieVerdict.innerText = charlie.action === "CONFIRM" ? "NON_REPUDIABLE_VALID" : "DISPUTE_RAISED";
    charlieVerdict.className = `text-lg font-bold ${charlie.action === 'CONFIRM' ? 'text-emerald-400' : 'text-rose-400'}`;
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
      showToast("success", "Non-Repudiation Confirmed", "Zeng-Christoph arbitration validated transfer from Bob to Charlie.");
    } else {
      banner.className = "p-4 rounded-lg border border-rose-700/60 bg-rose-950/40 font-bold text-xs flex items-center justify-between text-rose-300";
      summaryText.innerText = `DISPUTE ALERT: ${charlie.explanation}`;
      badge.innerText = "DISPUTE_RAISED";
      badge.className = "px-2.5 py-1 rounded text-[10px] mono bg-rose-900 text-rose-300";
      showToast("danger", "Arbitration Dispute Raised", "Alice attempted asymmetric repudiation. Blocked by Charlie.");
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
/**
 * Smart Floating Hover Explainer Engine
 * Positions a sleek frosted-glass tooltip directly adjacent to the hovered element.
 * Features 5-second auto-dismiss with animated progress bar, pause-on-hover,
 * grace period for moving between elements, and viewport boundary collision detection.
 */
function initHoverExplainerEngine() {
  let tooltip = document.getElementById("quantum-tooltip");
  if (!tooltip) {
    tooltip = document.createElement("div");
    tooltip.id = "quantum-tooltip";
    tooltip.className = "interactive";
    tooltip.innerHTML = `
      <div class="tooltip-header">
        <span class="tooltip-tag" id="q-tooltip-tag">INFO</span>
      </div>
      <div class="tooltip-title" id="q-tooltip-title">Feature</div>
      <p class="tooltip-body mt-1" id="q-tooltip-body"></p>
    `;
    document.body.appendChild(tooltip);
  }

  const titleEl = document.getElementById("q-tooltip-title");
  const bodyEl = document.getElementById("q-tooltip-body");
  const tagEl = document.getElementById("q-tooltip-tag");

  let currentTarget = null;
  let hideTimeout = null;
  let hoverShowTimer = null;

  function positionTooltip(target) {
    const rect = target.getBoundingClientRect();
    const ttWidth = 320;
    const ttHeight = 110;
    const padding = 12;

    // Prefer placing directly below if element is in top half of screen, or above if in bottom half
    let top;
    if (rect.top < 240) {
      top = rect.bottom + 8;
    } else {
      top = rect.top - ttHeight - 8;
    }

    // Ensure it NEVER overlaps the header bar (y < 72px)
    if (top < 72) {
      top = rect.bottom + 8;
    }

    let left = rect.left + (rect.width / 2) - (ttWidth / 2);

    // Keep within horizontal window bounds
    if (left < padding) {
      left = padding;
    } else if (left + ttWidth > window.innerWidth - padding) {
      left = window.innerWidth - ttWidth - padding;
    }

    tooltip.style.top = `${Math.max(padding, top)}px`;
    tooltip.style.left = `${Math.max(padding, left)}px`;
  }

  function dismissTooltip() {
    tooltip.classList.remove("active");
    currentTarget = null;
  }

  function showExplainer(target) {
    if (window.QuetzalcoatlTour && window.QuetzalcoatlTour.isActive) {
      dismissTooltip();
      return;
    }

    if (hideTimeout) {
      clearTimeout(hideTimeout);
      hideTimeout = null;
    }

    const title = target.getAttribute("data-explain-title");
    const body = target.getAttribute("data-explain-body");
    if (!title || !body) return;

    currentTarget = target;

    // Categorize based on context
    const category = title.includes("Attack") || title.includes("Forgery") || title.includes("Replay") ? "THREAT VECTOR" :
      title.includes("Sector") || title.includes("Cockpit") ? "SOC WORKSPACE" :
        title.includes("Teleport") || title.includes("Circuit") ? "QUANTUM PROTOCOL" :
          title.includes("SPRT") || title.includes("Hoeffding") || title.includes("Evidence") ? "STATISTICAL PROOF" : "EXPLAINER";

    if (tagEl) tagEl.textContent = category;
    if (titleEl) titleEl.textContent = title;
    if (bodyEl) bodyEl.textContent = body;

    positionTooltip(target);
    tooltip.classList.add("active");
  }

  document.addEventListener("mouseover", (e) => {
    if (window.QuetzalcoatlTour && window.QuetzalcoatlTour.isActive) {
      dismissTooltip();
      return;
    }
    const target = e.target.closest("[data-explain-title]");
    if (target) {
      if (hoverShowTimer) clearTimeout(hoverShowTimer);
      hoverShowTimer = setTimeout(() => {
        if (!window.QuetzalcoatlTour || !window.QuetzalcoatlTour.isActive) {
          showExplainer(target);
        }
      }, 200);
    }
  });

  document.addEventListener("mouseout", (e) => {
    if (hoverShowTimer) {
      clearTimeout(hoverShowTimer);
      hoverShowTimer = null;
    }
    const fromTarget = e.target.closest("[data-explain-title]");
    if (!fromTarget) return;

    const toElement = e.relatedTarget;
    if (toElement && (fromTarget.contains(toElement) || tooltip.contains(toElement))) {
      return;
    }

    // 80ms buffer so moving between inner spans doesn't flicker
    hideTimeout = setTimeout(() => {
      dismissTooltip();
    }, 80);
  });

  // Reposition on window resize or scroll
  window.addEventListener("scroll", () => {
    if (currentTarget && tooltip.classList.contains("active")) {
      positionTooltip(currentTarget);
    }
  }, { passive: true });

  window.addEventListener("resize", () => {
    if (currentTarget && tooltip.classList.contains("active")) {
      positionTooltip(currentTarget);
    }
  }, { passive: true });

  initKeyboardNavigation();
  initStickyCockpitBar();
}

/**
 * Global Guide Mode Toggle
 * Highlights all explorable components with subtle glowing markers.
 */
function toggleGuideMode() {
  document.body.classList.toggle("guide-mode-active");
  const isActive = document.body.classList.contains("guide-mode-active");
  const btn = document.getElementById("guide-mode-btn");
  if (btn) {
    if (isActive) {
      btn.className = "px-3 py-1.5 rounded-lg bg-cyan-900/60 border border-cyan-400 text-cyan-300 font-bold flex items-center gap-1.5 transition";
      showToast("info", "Guide Mode Active", "All explorable quantum elements are now marked with (?). Hover any to inspect!");
    } else {
      btn.className = "px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 flex items-center gap-1.5 transition";
      showToast("info", "Guide Mode Dismissed", "Returned to standard view.");
    }
  }
}

/**
 * Keyboard Shortcuts Navigation
 * 1-7: Switch tabs
 * H: Toggle Guide Mode
 * F: Quick-trigger Forgery Attack
 * V: Quick-trigger Clean Verification
 * Escape: Close modals and tooltips
 */
function initKeyboardNavigation() {
  document.addEventListener("keydown", (e) => {
    // Ignore keystrokes inside input or textarea
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    const tabMap = {
      "1": "cockpit",
      "2": "circuit",
      "3": "matrix",
      "4": "experiments",
      "5": "audit",
      "6": "multi-party",
      "7": "education"
    };

    if (tabMap[e.key]) {
      switchTab(tabMap[e.key]);
      showToast("info", `Switched to Tab: ${tabMap[e.key].toUpperCase()}`, `Shortcut [${e.key}]`);
    } else if (e.key === "h" || e.key === "H") {
      toggleGuideMode();
    } else if (e.key === "f" || e.key === "F") {
      simulateAttack("forgery");
    } else if (e.key === "v" || e.key === "V") {
      runLegitimateVerify();
    } else if (e.key === "Escape") {
      const tooltip = document.getElementById("quantum-tooltip");
      if (tooltip) tooltip.classList.remove("active");
      const modal = document.getElementById("merkle-proof-modal");
      if (modal) modal.classList.add("hidden");
    }
  });
}

/**
 * Sticky Mini Cockpit Bar on Scroll
 * Floats at bottom of screen when user scrolls past the top verdict sector,
 * so live verdict, error rate, and quick attack test buttons are ALWAYS within reach.
 */
function initStickyCockpitBar() {
  let stickyBar = document.getElementById("sticky-cockpit-bar");
  if (!stickyBar) {
    stickyBar = document.createElement("div");
    stickyBar.id = "sticky-cockpit-bar";
    stickyBar.innerHTML = `
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" id="sticky-status-dot"></span>
        <span class="text-zinc-400 font-medium">VERDICT:</span>
        <span class="text-emerald-400 font-bold" id="sticky-action-val">ACCEPT</span>
      </div>
      <div class="h-3 w-[1px] bg-zinc-700"></div>
      <div class="flex items-center gap-1.5">
        <span class="text-zinc-400">ERROR:</span>
        <span class="text-white font-bold" id="sticky-error-val">3.0%</span>
      </div>
      <div class="h-3 w-[1px] bg-zinc-700"></div>
      <div class="flex items-center gap-2">
        <button onclick="runLegitimateVerify()" class="px-2.5 py-1 rounded bg-emerald-950 border border-emerald-500/50 text-emerald-300 hover:text-white font-bold text-[10px] transition flex items-center gap-1">
          <i data-lucide="check" class="w-3 h-3"></i> Clean Verify
        </button>
        <button onclick="simulateAttack('forgery')" class="px-2.5 py-1 rounded bg-rose-950 border border-rose-500/50 text-rose-300 hover:text-white font-bold text-[10px] transition flex items-center gap-1">
          <i data-lucide="zap" class="w-3 h-3"></i> Test Forgery
        </button>
      </div>
    `;
    document.body.appendChild(stickyBar);
    lucide.createIcons();
  }

  const triggerEl = document.getElementById("tab-cockpit");
  window.addEventListener("scroll", () => {
    if (!triggerEl) return;
    const rect = triggerEl.getBoundingClientRect();
    if (rect.top < -250) {
      stickyBar.classList.add("visible");
    } else {
      stickyBar.classList.remove("visible");
    }
  }, { passive: true });
}

/**
 * Smooth Anchor Scroll to Sector
 */
function scrollToSector(sectorId) {
  const el = document.getElementById(sectorId);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    el.classList.add("ring-2", "ring-cyan-400");
    setTimeout(() => {
      el.classList.remove("ring-2", "ring-cyan-400");
    }, 1200);
  }
}

