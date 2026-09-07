/**
 * QUETZALCOATL - Interactive Tutorial Walkthrough Bot (Agent Q)
 * Step-by-step conversational guide with spotlight highlight, auto-play,
 * audio telemetry chirps, and live scenario triggers.
 */

(function () {
  'use strict';

  class QuetzalcoatlTour {
    constructor() {
      this.isActive = false;
      this.currentStep = 0;
      this.autoPlayTimer = null;
      this.isAutoPlaying = false;
      this.isMuted = localStorage.getItem("qds_tour_muted") === "true";
      this.autoPlayIntervalSeconds = 8;
      this.autoPlayRemaining = this.autoPlayIntervalSeconds;
      this.countdownInterval = null;
      this.audioCtx = null;

      this.initDom();
      this.bindEvents();
    }

    // Sound Synthesizer via Web Audio API (No external sound files required)
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
        // AudioContext not permitted or blocked
      }
    }

    soundNext() {
      this.playTone(520, 880, 0.14, "sine");
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

    // Build Tour Overlay and Bot Dialog in DOM
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
              <rect id="tour-mask-hole" x="0" y="0" width="0" height="0" rx="10" ry="10" fill="black" />
            </mask>
          </defs>
          <rect x="0" y="0" width="100%" height="100%" fill="rgba(0, 0, 0, 0.78)" mask="url(#tour-spotlight-cutout)" />
        </svg>

        <!-- Focus Spotlight Frame (Positioned dynamically over target element) -->
        <div id="tour-focus-frame" class="tour-focus-frame">
          <div class="tour-corner top-left"></div>
          <div class="tour-corner top-right"></div>
          <div class="tour-corner bottom-left"></div>
          <div class="tour-corner bottom-right"></div>
          <span id="tour-focus-label" class="tour-focus-label">TARGET IN FOCUS</span>
        </div>

        <!-- Floating Conversational Bot Card -->
        <div id="tour-bot-dialog" class="tour-bot-dialog" role="dialog" aria-modal="true">
          <!-- Card Header -->
          <div class="tour-dialog-header">
            <div class="flex items-center gap-2.5">
              <div class="tour-avatar-pulse">
                <span class="tour-bot-icon">🤖</span>
                <span class="tour-live-dot"></span>
              </div>
              <div>
                <div class="tour-bot-name">AGENT Q // SOC ASSISTANT</div>
                <div class="tour-step-badge" id="tour-step-indicator">STEP 1 OF 9</div>
              </div>
            </div>
            <div class="flex items-center gap-1.5">
              <button id="tour-btn-mute" class="tour-icon-btn" title="Toggle Sound [M]">
                <span id="tour-mute-icon">${this.isMuted ? '🔇' : '🔊'}</span>
              </button>
              <button id="tour-btn-close" class="tour-icon-btn" title="Exit Tour [Esc]">✕</button>
            </div>
          </div>

          <!-- Linear Step Progress Bar -->
          <div class="tour-progress-track">
            <div id="tour-progress-bar" class="tour-progress-bar" style="width: 11%;"></div>
          </div>

          <!-- Dialog Body -->
          <div class="tour-dialog-body">
            <div class="tour-category-pill" id="tour-category-pill">SYSTEM ARCHITECTURE</div>
            <h3 class="tour-step-title" id="tour-step-title">Welcome to Quantum Teleportation SOC</h3>
            <p class="tour-speech-text" id="tour-speech-text">
              Greetings, Operator! I am Agent Q, your quantum threat monitoring guide.
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
              <span class="hidden sm:inline">Keys: [← / →] [Space: Play] [T: Toggle]</span>
              <span class="sm:hidden">[← / →]</span>
            </div>
            <div class="flex items-center gap-2">
              <button id="tour-btn-prev" class="tour-btn tour-btn-secondary">◂ Prev</button>
              <button id="tour-btn-autoplay" class="tour-btn tour-btn-secondary" title="Auto-advance through tour">
                <span id="tour-autoplay-icon">▶</span> <span id="tour-autoplay-label">Auto</span>
                <span id="tour-autoplay-timer" class="text-[10px] opacity-70 ml-0.5"></span>
              </button>
              <button id="tour-btn-next" class="tour-btn tour-btn-primary">Next ➔</button>
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(root);

      // Add Tour Launch Floating Banner (if not already dismissed)
      this.renderQuickLaunchPrompt();
    }

    // Quick launch prompt for first-time visitors
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
            <div class="text-[11px] text-zinc-400">Take the 60-second interactive guided bot walkthrough.</div>
          </div>
        </div>
        <div class="flex items-center gap-2 mt-2 sm:mt-0">
          <button id="prompt-btn-start" class="px-2.5 py-1 rounded bg-white text-black font-bold text-xs hover:bg-zinc-200 transition">
            Start Walkthrough
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

    // Step Definitions for Desktop Dashboard
    getDesktopSteps() {
      return [
        {
          id: "welcome",
          target: "header",
          category: "MISSION BRIEFING",
          title: "Welcome to Quetzalcoatl QDS SOC",
          speech: "Greetings, Operator! I am Agent Q, your quantum SOC intelligence assistant. Quetzalcoatl is a post-quantum cyber defense platform that uses 3-qubit Bennett teleportation to authenticate high-stakes documents and protect critical national infrastructure.",
          calloutTitle: "WHY QUANTUM SIGNATURES?",
          calloutText: "Classical digital signatures (RSA, ECC) can be broken by Shor's algorithm on a quantum computer. QDS relies on fundamental laws of quantum physics: uncopyability and the No-Cloning theorem.",
          placement: "bottom"
        },
        {
          id: "thresholds",
          target: "#ribbon-session-id",
          category: "SECURITY THRESHOLDS",
          title: "Dual Quantum Security Thresholds",
          speech: "Look at the telemetry ribbon above. Notice our dual thresholds: sv = 6.0% (verification tolerance for optical noise) and sa = 21.0% (security abort limit). Any eavesdropper trying to intercept or measure states creates irreducible errors that exceed sa.",
          calloutTitle: "INFORMATION THEORETIC BOUND",
          calloutText: "As proven by Gottesman-Chuang and Zeng-Christoph, when error rate e ≤ sv, probability of forgery is bounded by Hoeffding exponential decay P ≤ exp(-2N(sa-sv)²).",
          placement: "bottom"
        },
        {
          id: "verdict",
          target: "#sector-verdict",
          category: "OPERATIONAL DEFENSE",
          title: "Real-Time Executive Security Verdict",
          speech: "This is Sector 01: The Verdict Cockpit. Here, the verification engine analyzes incoming Bell measurements against the registered quantum key. It delivers instantaneous verdicts: ACCEPT (authentic), ALERT (channel noise), or BLOCK (quantum attack interdicted).",
          calloutTitle: "ZERO TRUST BOUNDARY",
          calloutText: "Fresh cryptographic nonces and sender identity certificates are verified alongside quantum bit error rates to prevent replay and impersonation.",
          actionLabel: "⚡ Simulate Quantum Forgery Interdiction",
          actionFn: () => {
            if (typeof window.simulateAttack === "function") window.simulateAttack('forgery');
          },
          placement: "bottom"
        },
        {
          id: "gauge",
          target: "#error-rate-val",
          category: "QUANTUM METRICS",
          title: "Quantum Mismatch Radial Gauge",
          speech: "The center gauge displays the live Quantum Bit Error Rate (QBER). Under nominal conditions with normal optical fiber decoherence, errors stay around ~3%. If an attacker measures the quantum states, error spikes to ~34%, immediately collapsing the state.",
          calloutTitle: "NO-CLONING COLLAPSE",
          calloutText: "Because quantum states cannot be cloned, an adversary's basis guess matches only 50% of the time, guaranteeing detectable disturbance on the remaining states.",
          placement: "left"
        },
        {
          id: "missions",
          target: "#sector-missions",
          category: "SOCIAL IMPACT PROBLEM",
          title: "National Mission Defense (Social Impact)",
          speech: "Here is how our project solves real-world crises! Click between high-impact national missions: Emergency Pediatric Organ Dispatch (#HRT-2026), Regional SCADA Power Grid (#HV-7701), and $45M Flood Relief Sovereign Aid (#DBT-2026).",
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
          target: "#sector-signer",
          category: "INTERACTIVE PLAYGROUND",
          title: "Custom Document Signer & Teleportation",
          speech: "You can sign custom high-value payloads in real-time! Type any clearance command, choose your quantum token count (50, 100, 200, or 500 Bell pairs), adjust fiber channel noise, and click 'Sign & Teleport Document'.",
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
          target: "#sector-threats",
          category: "ATTACK LAB",
          title: "Controlled Cyber Threat Simulation Lab",
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
          target: "#sector-evidence",
          category: "MATHEMATICAL EVIDENCE",
          title: "Scientific Evidence & Wald SPRT Stopping",
          speech: "In SOC Analyst Mode, inspect the rigorous statistical mathematics: Wald SPRT early stopping terminates testing after only ~48 qubits (saving 74% of quantum resources), while Hoeffding bounds guarantee forgery bounds ≤ 1.42×10⁻⁶.",
          calloutTitle: "TRIPLE-BASIS VERIFICATION",
          calloutText: "The chart displays match and mismatch distributions across Pauli Z, X, and Y measurement bases.",
          placement: "top"
        },
        {
          id: "tabs",
          target: "nav",
          category: "ADVANCED LABS",
          title: "Deep-Dive Labs & Merkle Audit Ledger",
          speech: "Use the top navigation bar to explore deeper modules: Tab 2 (Teleportation Circuit Lab), Tab 3 (Attack Matrix), Tab 4 (Monte Carlo Benchmark Batch), Tab 5 (Ethereum-anchored Merkle Audit Ledger), and Tab 6 (Zeng-Christoph Multi-Party Arbitration).",
          calloutTitle: "ALL SYSTEMS READY",
          calloutText: "You are now fully trained to operate the Quetzalcoatl Quantum Digital Signature SOC! Press [T] anytime to restart this tour.",
          actionLabel: "🔬 Open Teleportation Circuit Lab",
          actionFn: () => {
            if (typeof window.switchTab === "function") window.switchTab('circuit');
          },
          placement: "bottom"
        }
      ];
    }

    // Step Definitions for Minimal / Mobile SPA
    getMobileSteps() {
      return [
        {
          id: "mob-welcome",
          target: "#hdr-title",
          category: "MOBILE BRIEFING",
          title: "Quetzalcoatl Ultra-Minimal Mobile SPA",
          speech: "Welcome to the ultra-minimal mobile view! Designed for field security officers to inspect quantum signature verifications on smartphones and tablets.",
          calloutTitle: "STANDALONE HYBRID ARCHITECTURE",
          calloutText: "Functions completely standalone in offline field environments or automatically syncs with the central SOC server when connected.",
          placement: "bottom"
        },
        {
          id: "mob-pipeline",
          target: "#pipeline-stepper",
          category: "PIPELINE ENGINE",
          title: "4-Stage Teleportation Pipeline",
          speech: "Tap through the 4 core stages of quantum signing: 1. Session Initialization, 2. Nonce Generation, 3. Bell State Teleportation, and 4. Measurement & Verification.",
          calloutTitle: "CIRCUIT RECONSTRUCTION",
          calloutText: "Each stage updates the classical feedforward bits and applies the required Pauli correction matrix.",
          placement: "bottom"
        },
        {
          id: "mob-vectors",
          target: "#vector-buttons",
          category: "ATTACK VECTORS",
          title: "Field Threat Simulation Vectors",
          speech: "Quickly toggle between Nominal baseline, Quantum Forgery (~34% QBER), Channel Decoherence Noise, and Replay vectors to test the mobile detection engine.",
          calloutTitle: "INSTANT DECISION",
          calloutText: "The mobile cockpit renders immediate ACCEPT, ALERT, or BLOCK status badges with vibration and audio cues.",
          placement: "top"
        },
        {
          id: "mob-missions",
          target: "#social-missions-panel",
          category: "SOCIAL IMPACT MISSIONS",
          title: "Emergency Social Problem Scenarios",
          speech: "Inspect how emergency organ dispatch (#HRT-2026) and SCADA power grid commands are secured against tampering in life-critical field operations.",
          calloutTitle: "REAL-TIME IMPACT",
          calloutText: "Each mission details the specific citizen lives or infrastructure gigawatts protected by quantum physics.",
          placement: "top"
        },
        {
          id: "mob-ledger",
          target: "#view-ledger",
          category: "MERKLE AUDIT",
          title: "Immutable Forensic Ledger",
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

    // Bind Controls and Hotkeys
    bindEvents() {
      document.getElementById("tour-btn-close")?.addEventListener("click", () => this.stop());
      document.getElementById("tour-btn-next")?.addEventListener("click", () => this.next());
      document.getElementById("tour-btn-prev")?.addEventListener("click", () => this.prev());
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

    start(stepIndex = 0) {
      this.isActive = true;
      this.currentStep = stepIndex;
      const root = document.getElementById("tour-bot-root");
      if (root) root.classList.remove("hidden");

      // Stop any existing auto-play timer
      this.stopAutoPlay();

      this.soundNext();
      this.renderCurrentStep();
    }

    stop() {
      this.isActive = false;
      this.stopAutoPlay();
      const root = document.getElementById("tour-bot-root");
      if (root) root.classList.add("hidden");
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
      const steps = this.getSteps();
      if (this.currentStep < steps.length - 1) {
        this.currentStep++;
        this.soundNext();
        this.renderCurrentStep();
      } else {
        // Finished tour
        this.stop();
        if (typeof window.showToast === "function") {
          window.showToast("success", "Tour Complete", "You are now ready to pilot the Quetzalcoatl Quantum SOC!");
        }
      }
    }

    prev() {
      if (this.currentStep > 0) {
        this.currentStep--;
        this.soundPrev();
        this.renderCurrentStep();
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
        this.stopAutoPlay();
      } else {
        this.startAutoPlay();
      }
    }

    startAutoPlay() {
      this.isAutoPlaying = true;
      this.autoPlayRemaining = this.autoPlayIntervalSeconds;
      this.updateAutoPlayUi();

      this.countdownInterval = setInterval(() => {
        this.autoPlayRemaining--;
        this.updateAutoPlayUi();
        if (this.autoPlayRemaining <= 0) {
          const steps = this.getSteps();
          if (this.currentStep < steps.length - 1) {
            this.next();
            this.autoPlayRemaining = this.autoPlayIntervalSeconds;
          } else {
            this.stop();
          }
        }
      }, 1000);
    }

    stopAutoPlay() {
      this.isAutoPlaying = false;
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
        this.countdownInterval = null;
      }
      this.updateAutoPlayUi();
    }

    updateAutoPlayUi() {
      const icon = document.getElementById("tour-autoplay-icon");
      const label = document.getElementById("tour-autoplay-label");
      const timer = document.getElementById("tour-autoplay-timer");
      const btn = document.getElementById("tour-btn-autoplay");

      if (this.isAutoPlaying) {
        if (icon) icon.textContent = "⏸";
        if (label) label.textContent = "Pause";
        if (timer) timer.textContent = `(${this.autoPlayRemaining}s)`;
        if (btn) btn.classList.add("active");
      } else {
        if (icon) icon.textContent = "▶";
        if (label) label.textContent = "Auto";
        if (timer) timer.textContent = "";
        if (btn) btn.classList.remove("active");
      }
    }

    renderCurrentStep() {
      const steps = this.getSteps();
      const step = steps[this.currentStep];
      if (!step) return;

      // Reset AutoPlay timer on step change
      if (this.isAutoPlaying) {
        this.autoPlayRemaining = this.autoPlayIntervalSeconds;
        this.updateAutoPlayUi();
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

        // Replace click listener
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

      // 5. Position spotlight and dialog over target element
      this.positionOnTarget();
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
        // Fallback: Centered dialog without cutout
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

      // Ensure target is on visible tab if inside tabbed container
      const tabAncestor = el.closest("[id^='tab-']");
      if (tabAncestor && tabAncestor.classList.contains("hidden")) {
        const tabId = tabAncestor.id.replace("tab-", "");
        if (typeof window.switchTab === "function") {
          window.switchTab(tabId);
        }
      }

      // Scroll element smoothly into view if needed
      const rect = el.getBoundingClientRect();
      const isVisible = rect.top >= 80 && rect.bottom <= window.innerHeight - 80;
      if (!isVisible) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      // Allow a frame for scroll to calculate accurate client rect
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
          const dialogWidth = Math.min(window.innerWidth - 32, 420);
          const dialogHeight = 360; // Estimated max height
          const margin = 16;

          let topPos, leftPos;

          // On mobile screens (< 640px), stick dialog comfortably at screen bottom
          if (window.innerWidth < 640) {
            dialog.style.top = "auto";
            dialog.style.bottom = "16px";
            dialog.style.left = "16px";
            dialog.style.right = "16px";
            dialog.style.transform = "none";
            return;
          }

          // Desktop positioning: Place below if enough space, else above
          const spaceBelow = window.innerHeight - (y + h);
          const spaceAbove = y;

          if (spaceBelow >= dialogHeight || spaceBelow >= spaceAbove) {
            // Place Below target
            topPos = y + h + margin;
          } else {
            // Place Above target
            topPos = Math.max(margin, y - dialogHeight - margin);
          }

          // Center horizontally relative to target element
          leftPos = x + (w / 2) - (dialogWidth / 2);
          // Clamp inside viewport
          leftPos = Math.max(margin, Math.min(window.innerWidth - dialogWidth - margin, leftPos));

          dialog.style.top = `${topPos}px`;
          dialog.style.left = `${leftPos}px`;
          dialog.style.bottom = "auto";
          dialog.style.right = "auto";
          dialog.style.transform = "none";
        }
      }, 50);
    }
  }

  // Initialize and attach to global window
  document.addEventListener("DOMContentLoaded", () => {
    window.QuetzalcoatlTour = new QuetzalcoatlTour();
  });
})();
