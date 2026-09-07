/**
 * QUETZALCOATL - Autonomous Interactive Tutorial Walkthrough Bot (Agent Q)
 * Hands-free automatic guided tour through all features, sectors, and labs
 * with focus spotlight, countdown meter, synthesized audio, and live scenario triggers.
 */

(function () {
  'use strict';

  class QuetzalcoatlTour {
    constructor() {
      this.isActive = false;
      this.currentStep = 0;
      this.isAutoPlaying = true; // Auto-play by default as requested
      this.isMuted = localStorage.getItem("qds_tour_muted") === "true";
      this.voiceEnabled = localStorage.getItem("qds_tour_voice") !== "false"; // Spoken vocal voice enabled by default!
      this.stepDuration = 6500; // Baseline duration
      this.timerStart = 0;
      this.animFrameId = null;
      this.audioCtx = null;
      this.selectedVoice = null;
      this.isSpeaking = false;
      this.speechTimeoutId = null;
      this.currentUtterance = null;

      this.initVoices();
      this.initDom();
      this.bindEvents();
    }

    // Voice Synthesizer via Native Web Speech API (Speaks out loud through speakers!)
    initVoices() {
      if (!('speechSynthesis' in window)) return;
      const selectBestVoice = () => {
        const voices = window.speechSynthesis.getVoices();
        if (!voices || !voices.length) return;
        const natural = voices.find(v => v.lang && v.lang.startsWith("en") && (
          v.name.includes("Natural") ||
          v.name.includes("Google US English") ||
          v.name.includes("Neural") ||
          v.name.includes("Jenny") ||
          v.name.includes("Guy") ||
          v.name.includes("Aria") ||
          v.name.includes("Daniel") ||
          v.name.includes("Samantha")
        ));
        this.selectedVoice = natural || voices.find(v => v.lang && v.lang.startsWith("en")) || voices[0];
      };

      selectBestVoice();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = selectBestVoice;
      }
    }

    speakStep(text) {
      this.stopSpeaking();
      if (!this.voiceEnabled || !('speechSynthesis' in window)) return;

      try {
        const utter = new SpeechSynthesisUtterance(text);
        utter.rate = 1.02; // crisp, comfortable speaking pace
        utter.pitch = 1.0;
        if (this.selectedVoice) utter.voice = this.selectedVoice;

        utter.onstart = () => {
          this.isSpeaking = true;
          this.updateSpeakingWave(true);
        };

        utter.onend = () => {
          this.isSpeaking = false;
          this.updateSpeakingWave(false);
          // If auto-play is active, advance after a short comfortable pause
          if (this.isAutoPlaying && this.isActive) {
            this.speechTimeoutId = setTimeout(() => {
              const steps = this.getSteps();
              if (this.currentStep < steps.length - 1) {
                this.next();
              } else {
                this.stop();
              }
            }, 1100);
          }
        };

        utter.onerror = (e) => {
          this.isSpeaking = false;
          this.updateSpeakingWave(false);
        };

        this.currentUtterance = utter;
        window.speechSynthesis.speak(utter);
      } catch (err) {
        console.warn("Speech synthesis error:", err);
      }
    }

    stopSpeaking() {
      if (this.speechTimeoutId) {
        clearTimeout(this.speechTimeoutId);
        this.speechTimeoutId = null;
      }
      if ('speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
        } catch (e) {}
      }
      this.isSpeaking = false;
      this.currentUtterance = null;
      this.updateSpeakingWave(false);
    }

    updateSpeakingWave(isSpeaking) {
      const wave = document.getElementById("tour-voice-wave");
      if (wave) {
        if (isSpeaking) {
          wave.classList.remove("hidden");
        } else {
          wave.classList.add("hidden");
        }
      }
    }

    toggleVoice() {
      this.voiceEnabled = !this.voiceEnabled;
      localStorage.setItem("qds_tour_voice", this.voiceEnabled.toString());
      this.updateVoiceUi();

      if (this.voiceEnabled) {
        const steps = this.getSteps();
        const step = steps[this.currentStep];
        if (step && this.isActive) {
          this.speakStep(step.speech);
          if (this.isAutoPlaying) this.startCountdownTimer();
        }
      } else {
        this.stopSpeaking();
      }
    }

    updateVoiceUi() {
      const btn = document.getElementById("tour-btn-voice");
      const icon = document.getElementById("tour-voice-icon");
      if (btn) {
        if (this.voiceEnabled) {
          btn.classList.add("tour-voice-on");
          btn.title = "Spoken Voice: ON (Click to mute voice) [V]";
        } else {
          btn.classList.remove("tour-voice-on");
          btn.title = "Spoken Voice: OFF (Click to unmute voice) [V]";
        }
      }
      if (icon) {
        icon.textContent = this.voiceEnabled ? "🎙️" : "🔇";
      }
    }

    // Sound Synthesizer via Web Audio API (Native zero-asset sound effects)
    playTone(freqStart, freqEnd, duration, type = "sine") {
      if (this.isMuted) return;
      try {
        if (!this.audioCtx) {
          const AudioContextClass = window.AudioContext || window.webkitAudioContext;
          if (AudioContextClass) this.audioCtx = new AudioContextClass();
        }
        if (!this.audioCtx) return;
        if (this.audioCtx.state === "suspended") this.audioCtx.resume();

        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.type = type;

        const now = this.audioCtx.currentTime;
        osc.frequency.setValueAtTime(freqStart, now);
        if (freqEnd && freqEnd !== freqStart) {
          osc.frequency.exponentialRampToValueAtTime(freqEnd, now + duration);
        }

        gain.gain.setValueAtTime(0.04, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

        osc.connect(gain);
        gain.connect(this.audioCtx.destination);
        osc.start(now);
        osc.stop(now + duration);
      } catch (e) {
        // AudioContext blocked or not allowed
      }
    }

    soundNext() {
      this.playTone(540, 880, 0.12, "sine");
    }

    soundPrev() {
      this.playTone(660, 440, 0.12, "sine");
    }

    soundAction() {
      this.playTone(440, 980, 0.22, "triangle");
    }

    soundExit() {
      this.playTone(400, 260, 0.16, "sine");
    }

    // Initialize DOM Overlay & Bot Speech Modal
    initDom() {
      if (document.getElementById("tour-bot-root")) return;

      const root = document.createElement("div");
      root.id = "tour-bot-root";
      root.className = "tour-bot-root hidden";

      root.innerHTML = `
        <!-- Dark Backdrop with SVG Cutout Mask -->
        <svg id="tour-svg-mask" class="tour-svg-mask">
          <defs>
            <mask id="tour-spotlight-cutout">
              <rect x="0" y="0" width="100%" height="100%" fill="white" />
              <rect id="tour-mask-hole" x="0" y="0" width="0" height="0" rx="12" ry="12" fill="black" />
            </mask>
          </defs>
          <rect x="0" y="0" width="100%" height="100%" fill="rgba(0, 0, 0, 0.82)" mask="url(#tour-spotlight-cutout)" />
        </svg>

        <!-- Focus Spotlight Frame (Dynamically sits on active target) -->
        <div id="tour-focus-frame" class="tour-focus-frame">
          <div class="tour-corner top-left"></div>
          <div class="tour-corner top-right"></div>
          <div class="tour-corner bottom-left"></div>
          <div class="tour-corner bottom-right"></div>
          <span id="tour-focus-label" class="tour-focus-label">FOCUS TARGET</span>
        </div>

        <!-- Floating Conversational Bot Card -->
        <div id="tour-bot-dialog" class="tour-bot-dialog" role="dialog" aria-modal="true">
          <!-- Card Header -->
          <div class="tour-dialog-header">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="tour-avatar-pulse shrink-0">
                <span class="tour-bot-icon">🤖</span>
                <span class="tour-live-dot"></span>
              </div>
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <span class="tour-bot-name">AGENT Q</span>
                  <span class="tour-auto-indicator" id="tour-auto-status">AUTOMATED TOUR</span>
                  <div class="tour-voice-wave hidden" id="tour-voice-wave" title="Speaking out loud">
                    <span></span><span></span><span></span><span></span>
                  </div>
                </div>
                <div class="tour-step-badge" id="tour-step-indicator">STEP 1 OF 16</div>
              </div>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button id="tour-btn-voice" class="tour-icon-btn ${this.voiceEnabled ? 'tour-voice-on' : ''}" title="Toggle Spoken Voice [V]">
                <span id="tour-voice-icon">${this.voiceEnabled ? '🎙️' : '🔇'}</span>
              </button>
              <button id="tour-btn-mute" class="tour-icon-btn" title="Toggle Sound FX [M]">
                <span id="tour-mute-icon">${this.isMuted ? '🔇' : '🔊'}</span>
              </button>
              <button id="tour-btn-close" class="tour-icon-btn" title="Exit Tour [Esc]">✕</button>
            </div>
          </div>

          <!-- Linear Step Progress Bar -->
          <div class="tour-progress-track">
            <div id="tour-progress-bar" class="tour-progress-bar" style="width: 6.25%;"></div>
          </div>

          <!-- Animated Auto-Play Countdown Meter -->
          <div class="tour-countdown-wrapper flex items-center justify-between text-[10px] mono text-zinc-400 mb-2">
            <span id="tour-countdown-text">Auto-Advancing: <b class="text-white" id="tour-countdown-val">6.5s</b></span>
            <span class="text-zinc-500 hidden sm:inline">[Space: Pause]</span>
          </div>
          <div class="tour-countdown-track mb-3">
            <div id="tour-countdown-bar" class="tour-countdown-bar" style="width: 100%;"></div>
          </div>

          <!-- Dialog Body -->
          <div class="tour-dialog-body">
            <div class="tour-category-pill" id="tour-category-pill">SYSTEM ARCHITECTURE</div>
            <h3 class="tour-step-title" id="tour-step-title">Welcome to Quantum Teleportation SOC</h3>
            <p class="tour-speech-text" id="tour-speech-text">
              Greetings, Operator! I am Agent Q, your automated tour assistant. Sit back as I walk you through each component of our platform.
            </p>

            <!-- Technical Deep-Dive / SOC Callout Box -->
            <div class="tour-callout-box" id="tour-callout-box">
              <div class="flex items-center gap-1.5 font-bold text-[10px] text-zinc-300 mono mb-1">
                <span>🔬</span> <span id="tour-callout-title">QUANTUM PROTOCOL BASIS</span>
              </div>
              <p class="text-[11px] text-zinc-400 leading-relaxed" id="tour-callout-text">
                Bennett 1993 teleportation leverages 3-qubit entanglement to transfer unknown quantum states with zero physical transmission.
              </p>
            </div>

            <!-- Optional Interactive Live Action Button -->
            <div id="tour-action-container" class="mt-3 hidden">
              <button id="tour-btn-live-action" class="tour-live-action-btn">
                <span class="tour-action-icon">⚡</span>
                <span id="tour-action-label">Trigger Live Scenario</span>
              </button>
            </div>
          </div>

          <!-- Card Footer & Controls -->
          <div class="tour-dialog-footer">
            <div class="tour-key-hints mono">
              <span class="hidden sm:inline">Keys: [← / →] [Space: Pause] [V: Voice] [T: Bot]</span>
              <span class="sm:hidden">[← / →] [V]</span>
            </div>
            <div class="flex items-center gap-2">
              <button id="tour-btn-prev" class="tour-btn tour-btn-secondary" title="Previous Step [←]">◂ Prev</button>
              <button id="tour-btn-autoplay" class="tour-btn tour-btn-secondary active" title="Toggle Auto-Play [Space]">
                <span id="tour-autoplay-icon">⏸</span> <span id="tour-autoplay-label">Pause</span>
              </button>
              <button id="tour-btn-next" class="tour-btn tour-btn-primary" title="Next Step [→]">Next ➔</button>
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(root);
      this.renderQuickLaunchPrompt();
    }

    // Floating welcome prompt for first-time visitors
    renderQuickLaunchPrompt() {
      const dismissed = localStorage.getItem("qds_tour_prompt_dismissed");
      if (dismissed) return;

      const prompt = document.createElement("div");
      prompt.id = "tour-welcome-prompt";
      prompt.className = "tour-welcome-prompt";
      prompt.innerHTML = `
        <div class="flex items-center gap-3">
          <div class="text-xl">🤖</div>
          <div class="text-left">
            <div class="font-bold text-xs text-white">First time at Quetzalcoatl SOC?</div>
            <div class="text-[11px] text-zinc-400">Take the autonomous, hands-free guided tour.</div>
          </div>
        </div>
        <div class="flex items-center gap-2 mt-2 sm:mt-0">
          <button id="prompt-btn-start" class="px-2.5 py-1 rounded bg-white text-black font-bold text-xs hover:bg-zinc-200 transition">
            Start Tour
          </button>
          <button id="prompt-btn-dismiss" class="p-1 text-zinc-500 hover:text-zinc-300 text-xs transition" title="Dismiss">
            ✕
          </button>
        </div>
      `;
      document.body.appendChild(prompt);

      document.getElementById("prompt-btn-start")?.addEventListener("click", () => {
        prompt.remove();
        localStorage.setItem("qds_tour_prompt_dismissed", "true");
        this.start();
      });

      document.getElementById("prompt-btn-dismiss")?.addEventListener("click", () => {
        prompt.remove();
        localStorage.setItem("qds_tour_prompt_dismissed", "true");
      });
    }

    // Comprehensive 16-Step Walkthrough for Desktop SOC
    getDesktopSteps() {
      return [
        {
          id: "brand_posture",
          tab: "cockpit",
          target: "header",
          category: "SYSTEM ARCHITECTURE",
          title: "1. Brand & Post-Quantum SOC Posture",
          speech: "Welcome to Quetzalcoatl! This is a state-of-the-art post-quantum Cyber Threat Detection SOC designed to interdict quantum forgery and eavesdropping on critical national infrastructure.",
          calloutTitle: "INFORMATION-THEORETIC SECURITY",
          calloutText: "Unlike classical signatures broken by Shor's algorithm, QDS relies on quantum mechanics: state measurements alter wave functions irreversibly (No-Cloning Theorem).",
          placement: "bottom"
        },
        {
          id: "session_telemetry",
          tab: "cockpit",
          target: "#ribbon-session-id",
          category: "OPERATIONAL TELEMETRY",
          title: "2. Live Session Freshness & Dual Thresholds",
          speech: "Here is the active session identifier. In quantum key distribution, every signature sequence uses fresh, single-use Bell pairs. Notice our dual thresholds: sv = 6.0% (optical channel noise limit) and sa = 21.0% (security abort limit).",
          calloutTitle: "DUAL THRESHOLD DERIVATION",
          calloutText: "If quantum bit error rate e ≤ sv, signatures are verified authentic. If e > sa, the signature is aborted due to active eavesdropping.",
          placement: "bottom"
        },
        {
          id: "merkle_root",
          tab: "cockpit",
          target: "#top-merkle-root",
          category: "IMMUTABLE AUDIT",
          title: "3. Blockchain-Anchored Merkle Root",
          speech: "Every signature verdict is cryptographically hashed into an immutable Merkle tree. The top root hash shown here is anchored directly into an Ethereum smart contract for court-admissible audit proof.",
          calloutTitle: "ZERO-TRUST VERIFICATION",
          calloutText: "Any tampering with historical event logs invalidates the cryptographic root derivation immediately.",
          placement: "bottom"
        },
        {
          id: "mode_switcher",
          tab: "cockpit",
          target: ".mode-switcher",
          category: "USER EXPERIENCE",
          title: "4. Simple Mode vs SOC Analyst Mode",
          speech: "Operators can toggle between Simple Mode (streamlined for executives and non-technical evaluators) and SOC Analyst Mode (unveiling deep mathematical formulas, Wald SPRT curves, and Hoeffding bounds).",
          calloutTitle: "REAL-TIME ADAPTATION",
          calloutText: "Clicking either mode instantly tailors the visual presentation without reloading data.",
          placement: "bottom"
        },
        {
          id: "verdict_card",
          tab: "cockpit",
          target: "#sector-verdict",
          category: "REAL-TIME VERDICT",
          title: "5. Sector 01: Executive Security Verdict Cockpit",
          speech: "This is Sector 01: The Verdict Cockpit. Our verification engine compares incoming states against Alice's keys. When clean, the verdict is ACCEPT. Under attack, it triggers an uncompromising BLOCK.",
          calloutTitle: "ZERO TRUST BOUNDARY",
          calloutText: "Fresh cryptographic nonces and sender identity certificates are verified alongside quantum error rates to prevent replay and impersonation.",
          actionLabel: "⚡ Simulate Quantum Forgery Interdiction",
          actionFn: () => {
            if (typeof window.simulateAttack === "function") window.simulateAttack('forgery');
          },
          placement: "bottom"
        },
        {
          id: "gauge",
          tab: "cockpit",
          target: "#error-rate-val",
          category: "QUANTUM METRICS",
          title: "6. Quantum Mismatch Radial Gauge (QBER)",
          speech: "The radial gauge visualizes real-time Quantum Bit Error Rate (QBER). Under nominal conditions, errors remain below 4%. If an adversary tries to copy or measure the states, error spikes to ~34%, collapsing the state.",
          calloutTitle: "NO-CLONING COLLAPSE",
          calloutText: "Because quantum states cannot be cloned, an adversary's basis guess matches only 50% of the time, guaranteeing detectable disturbance on the remaining states.",
          placement: "left"
        },
        {
          id: "instant_actions",
          tab: "cockpit",
          target: "#instant-actions-panel",
          category: "OPERATOR TOOLS",
          title: "7. Instant Operator Action Triggers",
          speech: "These quick buttons allow operators to test authentic quantum signatures, simulate quantum forgery attacks, or initialize fresh session keys with a single click.",
          calloutTitle: "FAST INTERACTION",
          calloutText: "Dispatches simulated Bell state measurements through the verification engine and updates the live ledger.",
          placement: "left"
        },
        {
          id: "missions",
          tab: "cockpit",
          target: "#sector-missions",
          category: "SOCIAL IMPACT PROBLEM",
          title: "8. Sector 02: National Mission Defense (Social Problems)",
          speech: "See how our project solves high-stakes real-world social problems! Explore 3 critical national missions: Emergency Pediatric Organ Dispatch, SCADA Power Grid Shutdown, and $45M Flood Relief Sovereign Aid.",
          calloutTitle: "CRITICAL INFRASTRUCTURE DEFENSE",
          calloutText: "An unauthorized forged command to a power substation could trigger a blackout for 4.2 million citizens. QDS guarantees mathematical immutability.",
          actionLabel: "⚡ Dispatch Organ Manifest Defense",
          actionFn: () => {
            if (typeof window.triggerSocialMission === "function") window.triggerSocialMission('healthcare_organ_dispatch');
          },
          placement: "top"
        },
        {
          id: "signer",
          tab: "cockpit",
          target: "#sector-signer",
          category: "INTERACTIVE PLAYGROUND",
          title: "9. Sector 03: Custom Document Signer Playground",
          speech: "You can sign custom high-value payloads in real-time! Type any clearance command, choose your quantum token count (50 to 500 Bell pairs), adjust fiber noise, and click 'Sign & Teleport Document'.",
          calloutTitle: "BENNETT 1993 FEEDFORWARD",
          calloutText: "Alice entangles the message qubit with an EPR pair, performs Bell State Measurement (BSM), and transmits 2 classical bits so Bob can apply the exact Pauli correction (I, X, Z, ZX).",
          actionLabel: "⚡ Sign Custom Sovereign Order",
          actionFn: () => {
            if (typeof window.signCustomDocument === "function") window.signCustomDocument();
          },
          placement: "top"
        },
        {
          id: "threats",
          tab: "cockpit",
          target: "#sector-threats",
          category: "ATTACK LAB",
          title: "10. Sector 04: Cyber Threat Simulation Lab (5 Vectors)",
          speech: "Test our deterministic Attribution Engine across 5 cyber threat models! Trigger Intercept-Resend Forgery (~34% ERR), Channel Decoherence (~12% ERR), Stale Nonce Replay, Signer Impersonation, or Unauthorized Verifier tampering.",
          calloutTitle: "DETERMINISTIC ATTRIBUTION",
          calloutText: "Unlike black-box machine learning that can hallucinate, our engine uses strict rule-based physics and cryptographic proofs to classify the exact attack mechanism.",
          actionLabel: "⚡ Interdict Stale Nonce Replay",
          actionFn: () => {
            if (typeof window.simulateAttack === "function") window.simulateAttack('replay');
          },
          placement: "top"
        },
        {
          id: "evidence",
          tab: "cockpit",
          target: "#sector-evidence",
          category: "STATISTICAL EVIDENCE",
          title: "11. Sector 05: Scientific Statistical Evidence & Wald SPRT",
          speech: "In SOC Analyst Mode, inspect the rigorous mathematics: Wald SPRT early-stopping terminates testing after only ~48 qubits (saving 74% of quantum resources), while Hoeffding bounds guarantee forgery bounds ≤ 1.42×10⁻⁶.",
          calloutTitle: "TRIPLE-BASIS TOMOGRAPHY",
          calloutText: "The chart displays match and mismatch distributions across Pauli Z, X, and Y measurement bases.",
          placement: "top"
        },
        {
          id: "tab_circuit",
          tab: "circuit",
          target: "#tab-circuit",
          category: "QUANTUM CIRCUITS",
          title: "12. Tab 2: 3-Qubit Bennett Teleportation Circuit Lab",
          speech: "Let's inspect the teleportation circuit! Here is an exact step-by-step visualizer of Bennett 1993: input state |ψ⟩, EPR Bell pair generation (|Φ+⟩), Bell State Measurement (BSM), classical feedforward bits, and Bob's Pauli correction.",
          calloutTitle: "ZERO QUANTUM CHANNEL TRANSMISSION",
          calloutText: "Reconstruction fidelity exceeds 99.9% without ever transmitting the quantum signature state through a physical wire.",
          placement: "bottom"
        },
        {
          id: "tab_matrix",
          tab: "matrix",
          target: "#tab-matrix",
          category: "THREAT MODELING",
          title: "13. Tab 3: Attack Comparison Matrix",
          speech: "The Attack Matrix provides a comprehensive side-by-side comparison of all 5 threat models against nominal conditions, detailing QBER signatures, entropy shifts, and cryptographic impact.",
          calloutTitle: "EVALUATION RUBRIC",
          calloutText: "Provides auditors and judges with complete clarity on how quantum physics distinguishes malicious attacks from physical decoherence.",
          placement: "bottom"
        },
        {
          id: "tab_experiments",
          tab: "experiments",
          target: "#tab-experiments",
          category: "MONTE CARLO TESTING",
          title: "14. Tab 4: Monte Carlo Batch Benchmark Engine",
          speech: "Run automated Monte Carlo batches of 30 to 100 trials to measure empirical False Acceptance Rate (FAR = 0.00%) and False Rejection Rate (FRR = 0.00%) with millisecond latency benchmarking.",
          calloutTitle: "STATISTICAL RIGOR",
          calloutText: "Validates high-throughput performance and statistical robustness under varying optical disturbance.",
          placement: "bottom"
        },
        {
          id: "tab_audit",
          tab: "audit",
          target: "#tab-audit",
          category: "FORENSIC INTEGRITY",
          title: "15. Tab 5: Tamper-Evident Merkle Audit Ledger",
          speech: "Here is the forensic audit ledger! Every event has a cryptographic leaf hash. You can click 'Inspect Proof' to trace the Merkle sibling path, or click 'Simulate Tampering' to watch modified records get quarantined.",
          calloutTitle: "IMMUTABLE AUDIT CHAIN",
          calloutText: "Guarantees that once a signature verdict is registered, no insider or attacker can silently alter the log.",
          placement: "bottom"
        },
        {
          id: "tab_arbitration",
          tab: "multi-party",
          target: "#tab-multi-party",
          category: "NON-REPUDIATION",
          title: "16. Tab 6: Multi-Party Non-Repudiation Arbitration",
          speech: "Zeng-Christoph arbitration guarantees non-repudiation: Alice cannot sign an order for Bob and later deny it when Bob forwards it to Charlie. If Alice sends conflicting keys, Charlie detects the gap (|e_B - e_C| > 10%) and blocks transfer.",
          calloutTitle: "NON-REPUDIATION THEOREM",
          calloutText: "Guarantees cross-agency document validity without requiring a centralized, trusted third-party arbiter.",
          placement: "bottom"
        }
      ];
    }

    // Step Definitions for Mobile / Minimal View
    getMobileSteps() {
      return [
        {
          id: "mob-welcome",
          target: "#hdr-title",
          category: "MOBILE BRIEFING",
          title: "1. Quetzalcoatl Ultra-Minimal Mobile SPA",
          speech: "Welcome to the ultra-minimal mobile view! Designed for field security officers to inspect quantum signature verifications on smartphones and tablets.",
          calloutTitle: "STANDALONE HYBRID ARCHITECTURE",
          calloutText: "Functions completely standalone in offline field environments or automatically syncs with the central SOC server when connected.",
          placement: "bottom"
        },
        {
          id: "mob-pipeline",
          target: "#pipeline-stepper",
          category: "PIPELINE ENGINE",
          title: "2. 4-Stage Teleportation Pipeline",
          speech: "Tap through the 4 core stages of quantum signing: 1. Session Initialization, 2. Nonce Generation, 3. Bell State Teleportation, and 4. Measurement & Verification.",
          calloutTitle: "CIRCUIT RECONSTRUCTION",
          calloutText: "Each stage updates the classical feedforward bits and applies the required Pauli correction matrix.",
          placement: "bottom"
        },
        {
          id: "mob-vectors",
          target: "#vector-buttons",
          category: "ATTACK VECTORS",
          title: "3. Field Threat Simulation Vectors",
          speech: "Quickly toggle between Nominal baseline, Quantum Forgery (~34% QBER), Channel Decoherence Noise, and Replay vectors to test the mobile detection engine.",
          calloutTitle: "INSTANT DECISION",
          calloutText: "The mobile cockpit renders immediate ACCEPT, ALERT, or BLOCK status badges with vibration and audio cues.",
          placement: "top"
        },
        {
          id: "mob-missions",
          target: "#social-missions-panel",
          category: "SOCIAL IMPACT MISSIONS",
          title: "4. Emergency Social Problem Scenarios",
          speech: "Inspect how emergency organ dispatch (#HRT-2026) and SCADA power grid commands are secured against tampering in life-critical field operations.",
          calloutTitle: "REAL-TIME IMPACT",
          calloutText: "Each mission details the specific citizen lives or infrastructure gigawatts protected by quantum physics.",
          placement: "top"
        },
        {
          id: "mob-ledger",
          target: "#view-ledger",
          category: "MERKLE AUDIT",
          title: "5. Immutable Forensic Ledger",
          speech: "Every signature verdict is cryptographically hashed into an append-only Merkle tree and anchored to the blockchain for non-repudiation and court-admissible audit trails.",
          calloutTitle: "TAMPER EVIDENT",
          calloutText: "Any unauthorized modification to historical records invalidates the Merkle root hash instantly.",
          placement: "top"
        }
      ];
    }

    getSteps() {
      const isMinimal = window.location.pathname.includes("minimal") ||
        window.location.pathname.includes("mobile") ||
        document.getElementById("pipeline-stepper") !== null;

      return isMinimal ? this.getMobileSteps() : this.getDesktopSteps();
    }

    // Bind Controls & Global Hotkeys
    bindEvents() {
      document.getElementById("tour-btn-close")?.addEventListener("click", () => this.stop());
      document.getElementById("tour-btn-next")?.addEventListener("click", () => {
        this.next();
      });
      document.getElementById("tour-btn-prev")?.addEventListener("click", () => {
        this.prev();
      });
      document.getElementById("tour-btn-voice")?.addEventListener("click", () => this.toggleVoice());
      document.getElementById("tour-btn-mute")?.addEventListener("click", () => this.toggleMute());
      document.getElementById("tour-btn-autoplay")?.addEventListener("click", () => this.toggleAutoPlay());

      // Global Keyboard Hotkeys
      window.addEventListener("keydown", (e) => {
        // [T] toggles tour if not typing in an input
        if ((e.key === "t" || e.key === "T") && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
          e.preventDefault();
          this.toggle();
          return;
        }

        if (!this.isActive) return;

        if (e.key === "ArrowRight" || e.key === "Enter") {
          e.preventDefault();
          this.next();
        } else if (e.key === "ArrowLeft") {
          e.preventDefault();
          this.prev();
        } else if (e.key === "Escape") {
          e.preventDefault();
          this.stop();
        } else if (e.key === " " || e.key === "Spacebar") {
          e.preventDefault();
          this.toggleAutoPlay();
        } else if (e.key === "v" || e.key === "V") {
          e.preventDefault();
          this.toggleVoice();
        } else if (e.key === "m" || e.key === "M") {
          e.preventDefault();
          this.toggleMute();
        }
      });

      // Window resize / scroll repositioning
      window.addEventListener("resize", () => {
        if (this.isActive) this.positionOnTarget();
      });
      window.addEventListener("scroll", () => {
        if (this.isActive) this.positionOnTarget();
      }, { passive: true });
    }

    // Start Guided Tour (Defaults to Auto-Play without clicking anything)
    start(stepIndex = 0) {
      this.isActive = true;
      this.currentStep = stepIndex;
      this.isAutoPlaying = true; // Auto-play enabled immediately!

      const root = document.getElementById("tour-bot-root");
      if (root) root.classList.remove("hidden");

      // Dismiss any open tooltip
      const tt = document.getElementById("quantum-tooltip");
      if (tt) tt.classList.remove("active");

      this.soundNext();
      this.updateVoiceUi();
      this.renderCurrentStep();
      this.startCountdownTimer();
    }

    stop() {
      this.isActive = false;
      this.stopSpeaking();
      this.stopCountdownTimer();

      const root = document.getElementById("tour-bot-root");
      if (root) root.classList.add("hidden");

      // Reset to cockpit tab on exit
      if (typeof window.switchTab === "function") {
        window.switchTab("cockpit");
      }

      this.soundExit();
    }

    toggle() {
      if (this.isActive) {
        this.stop();
      } else {
        this.start();
      }
    }

    next() {
      this.stopSpeaking();
      this.stopCountdownTimer();
      const steps = this.getSteps();
      if (this.currentStep < steps.length - 1) {
        this.currentStep++;
        this.soundNext();
        this.renderCurrentStep();
        if (this.isAutoPlaying) this.startCountdownTimer();
      } else {
        // Tour completed
        this.stop();
        if (typeof window.showToast === "function") {
          window.showToast("success", "Tour Complete", "You have completed the full Quetzalcoatl SOC walkthrough!");
        }
      }
    }

    prev() {
      this.stopSpeaking();
      this.stopCountdownTimer();
      if (this.currentStep > 0) {
        this.currentStep--;
        this.soundPrev();
        this.renderCurrentStep();
        if (this.isAutoPlaying) this.startCountdownTimer();
      }
    }

    toggleMute() {
      this.isMuted = !this.isMuted;
      localStorage.setItem("qds_tour_muted", this.isMuted.toString());
      const icon = document.getElementById("tour-mute-icon");
      if (icon) icon.textContent = this.isMuted ? '🔇' : '🔊';
      if (!this.isMuted) this.playTone(600, 900, 0.12);
    }

    toggleAutoPlay() {
      if (this.isAutoPlaying) {
        this.isAutoPlaying = false;
        this.stopCountdownTimer();
        if (this.speechTimeoutId) {
          clearTimeout(this.speechTimeoutId);
          this.speechTimeoutId = null;
        }
        if (this.isSpeaking && 'speechSynthesis' in window) {
          window.speechSynthesis.pause();
        }
        this.updateAutoPlayUi(false);
      } else {
        this.isAutoPlaying = true;
        this.updateAutoPlayUi(true);
        if ('speechSynthesis' in window && window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
        } else if (!this.isSpeaking && this.voiceEnabled) {
          const steps = this.getSteps();
          const step = steps[this.currentStep];
          if (step) this.speakStep(step.speech);
        }
        this.startCountdownTimer();
      }
    }

    startCountdownTimer() {
      this.stopCountdownTimer();
      if (!this.isAutoPlaying || !this.isActive) return;

      this.timerStart = performance.now();

      const tick = (now) => {
        if (!this.isAutoPlaying || !this.isActive) return;

        const elapsed = now - this.timerStart;
        const remaining = Math.max(0, this.stepDuration - elapsed);
        const pct = (remaining / this.stepDuration) * 100;

        const bar = document.getElementById("tour-countdown-bar");
        const val = document.getElementById("tour-countdown-val");

        if (bar) bar.style.width = `${pct}%`;
        if (val) {
          if (this.isSpeaking) {
            val.textContent = "Speaking...";
          } else if (this.speechTimeoutId) {
            val.textContent = "Advancing...";
          } else {
            val.textContent = `${(remaining / 1000).toFixed(1)}s`;
          }
        }

        if (elapsed >= this.stepDuration) {
          // If Agent Q is currently speaking or queued to advance, let speech complete naturally
          if (this.isSpeaking || this.speechTimeoutId) {
            this.animFrameId = requestAnimationFrame(tick);
            return;
          }

          const steps = this.getSteps();
          if (this.currentStep < steps.length - 1) {
            this.next();
          } else {
            this.stop();
          }
        } else {
          this.animFrameId = requestAnimationFrame(tick);
        }
      };

      this.animFrameId = requestAnimationFrame(tick);
    }

    stopCountdownTimer() {
      if (this.animFrameId) {
        cancelAnimationFrame(this.animFrameId);
        this.animFrameId = null;
      }
    }

    updateAutoPlayUi(isPlaying) {
      const icon = document.getElementById("tour-autoplay-icon");
      const label = document.getElementById("tour-autoplay-label");
      const statusBadge = document.getElementById("tour-auto-status");
      const btn = document.getElementById("tour-btn-autoplay");
      const countWrapper = document.querySelector(".tour-countdown-wrapper");

      if (isPlaying) {
        if (icon) icon.textContent = "⏸";
        if (label) label.textContent = "Pause";
        if (statusBadge) statusBadge.textContent = "AUTOMATED TOUR";
        if (btn) btn.classList.add("active");
        if (countWrapper) countWrapper.style.opacity = "1";
      } else {
        if (icon) icon.textContent = "▶";
        if (label) label.textContent = "Resume";
        if (statusBadge) statusBadge.textContent = "PAUSED";
        if (btn) btn.classList.remove("active");
        if (countWrapper) countWrapper.style.opacity = "0.4";
      }
    }

    renderCurrentStep() {
      const steps = this.getSteps();
      const step = steps[this.currentStep];
      if (!step) return;

      // Automatically switch to correct tab if step requires it!
      if (step.tab && typeof window.switchTab === "function") {
        window.switchTab(step.tab);
      }

      // 1. Update Indicators
      const ind = document.getElementById("tour-step-indicator");
      if (ind) ind.textContent = `STEP ${this.currentStep + 1} OF ${steps.length}`;

      const prog = document.getElementById("tour-progress-bar");
      if (prog) {
        const pct = ((this.currentStep + 1) / steps.length) * 100;
        prog.style.width = `${pct}%`;
      }

      const cat = document.getElementById("tour-category-pill");
      if (cat) cat.textContent = step.category || "OPERATIONAL TELEMETRY";

      const title = document.getElementById("tour-step-title");
      if (title) title.textContent = step.title;

      const speech = document.getElementById("tour-speech-text");
      if (speech) speech.textContent = step.speech;

      // 2. Callout Box
      const calloutBox = document.getElementById("tour-callout-box");
      const calloutTitle = document.getElementById("tour-callout-title");
      const calloutText = document.getElementById("tour-callout-text");
      if (step.calloutText) {
        if (calloutBox) calloutBox.classList.remove("hidden");
        if (calloutTitle) calloutTitle.textContent = step.calloutTitle || "QUANTUM PROTOCOL BASIS";
        if (calloutText) calloutText.textContent = step.calloutText;
      } else {
        if (calloutBox) calloutBox.classList.add("hidden");
      }

      // 3. Optional Live Action Button
      const actionContainer = document.getElementById("tour-action-container");
      const actionLabel = document.getElementById("tour-action-label");
      const actionBtn = document.getElementById("tour-btn-live-action");
      if (step.actionFn && step.actionLabel) {
        if (actionContainer) actionContainer.classList.remove("hidden");
        if (actionLabel) actionLabel.textContent = step.actionLabel;

        const newBtn = actionBtn.cloneNode(true);
        actionBtn.parentNode.replaceChild(newBtn, actionBtn);
        newBtn.addEventListener("click", () => {
          this.soundAction();
          step.actionFn();
        });
      } else {
        if (actionContainer) actionContainer.classList.add("hidden");
      }

      // 4. Update Prev / Next Buttons
      const prevBtn = document.getElementById("tour-btn-prev");
      if (prevBtn) {
        prevBtn.disabled = this.currentStep === 0;
        prevBtn.style.opacity = this.currentStep === 0 ? "0.4" : "1";
      }

      const nextBtn = document.getElementById("tour-btn-next");
      if (nextBtn) {
        nextBtn.textContent = this.currentStep === steps.length - 1 ? "Complete ✓" : "Next ➔";
      }

      this.updateAutoPlayUi(this.isAutoPlaying);

      // 5. Position spotlight and dialog over target element
      this.positionOnTarget();

      // 6. Speak out loud with realistic voice synthesis!
      this.speakStep(step.speech);

      // Dynamically match step duration to speech length
      const words = (step.speech || "").split(/\s+/).filter(Boolean).length;
      const dynamicSec = this.voiceEnabled ? Math.max(6.5, (words / 2.6) + 1.2) : 6.5;
      this.stepDuration = dynamicSec * 1000;
    }

    positionOnTarget() {
      const steps = this.getSteps();
      const step = steps[this.currentStep];
      if (!step) return;

      let el = null;
      if (step.target) {
        el = document.querySelector(step.target);
      }

      const maskHole = document.getElementById("tour-mask-hole");
      const focusFrame = document.getElementById("tour-focus-frame");
      const dialog = document.getElementById("tour-bot-dialog");

      if (!el) {
        if (maskHole) {
          maskHole.setAttribute("width", "0");
          maskHole.setAttribute("height", "0");
        }
        if (focusFrame) focusFrame.style.display = "none";
        if (dialog) {
          dialog.style.top = "50%";
          dialog.style.left = "50%";
          dialog.style.transform = "translate(-50%, -50%)";
        }
        return;
      }

      // Smoothly scroll target element into viewport center
      const rect = el.getBoundingClientRect();
      const isVisible = rect.top >= 80 && rect.bottom <= window.innerHeight - 80;
      if (!isVisible) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      setTimeout(() => {
        const updatedRect = el.getBoundingClientRect();
        const pad = 10;
        const x = Math.max(0, updatedRect.left - pad);
        const y = Math.max(0, updatedRect.top - pad);
        const w = updatedRect.width + pad * 2;
        const h = updatedRect.height + pad * 2;

        // 1. Update SVG mask hole cutout
        if (maskHole) {
          maskHole.setAttribute("x", x);
          maskHole.setAttribute("y", y);
          maskHole.setAttribute("width", w);
          maskHole.setAttribute("height", h);
        }

        // 2. Update Focus Frame
        if (focusFrame) {
          focusFrame.style.display = "block";
          focusFrame.style.top = `${y}px`;
          focusFrame.style.left = `${x}px`;
          focusFrame.style.width = `${w}px`;
          focusFrame.style.height = `${h}px`;
        }

        // 3. Position Conversational Bot Dialog
        if (dialog) {
          const dialogWidth = Math.min(window.innerWidth - 32, 440);
          const dialogHeight = 400; // Estimated height
          const margin = 16;

          let topPos, leftPos;

          // On mobile screens (< 640px), dock dialog at bottom
          if (window.innerWidth < 640) {
            dialog.style.top = "auto";
            dialog.style.bottom = "16px";
            dialog.style.left = "16px";
            dialog.style.right = "16px";
            dialog.style.transform = "none";
            return;
          }

          // Desktop positioning: Place below if room, else above
          const spaceBelow = window.innerHeight - (y + h);
          const spaceAbove = y;

          if (spaceBelow >= dialogHeight || spaceBelow >= spaceAbove) {
            topPos = y + h + margin;
          } else {
            topPos = Math.max(margin, y - dialogHeight - margin);
          }

          // Clamp top position inside window
          topPos = Math.max(margin, Math.min(window.innerHeight - dialogHeight - margin, topPos));

          // Center horizontally relative to target element
          leftPos = x + (w / 2) - (dialogWidth / 2);
          leftPos = Math.max(margin, Math.min(window.innerWidth - dialogWidth - margin, leftPos));

          dialog.style.top = `${topPos}px`;
          dialog.style.left = `${leftPos}px`;
          dialog.style.bottom = "auto";
          dialog.style.right = "auto";
          dialog.style.transform = "none";
        }
      }, 60);
    }
  }

  // Initialize and attach to global window
  document.addEventListener("DOMContentLoaded", () => {
    window.QuetzalcoatlTour = new QuetzalcoatlTour();
  });
})();
