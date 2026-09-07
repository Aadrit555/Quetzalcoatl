<p align="center">
  <img src="frontend/assets/cover.png" alt="Quetzalcoatl QDS Logo" width="280" />
</p>

<h1 align="center">QUETZALCOATL 🛡️</h1>
<h3 align="center">Quantum Digital Signature (QDS) Cyber Defense Command Center</h3>

<p align="center">
  <b>Built for Smart India Hackathon (SIH)</b><br>
  <i>Protecting Critical National Lifelines with Quantum Physics & Zero-Guesswork Mathematics</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20For-Smart%20India%20Hackathon%20(SIH)-FF9933?style=for-the-badge" alt="SIH">
  <img src="https://img.shields.io/badge/Security-Information--Theoretic%20(Quantum%20Laws)-blue?style=for-the-badge" alt="Quantum Security">
  <img src="https://img.shields.io/badge/Tests-45%2F45%20Passing%20(100%25)-brightgreen?style=for-the-badge" alt="Tests 100%">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
</p>

---

## 🇮🇳 What is Quetzalcoatl? (In Simple Words)

**Quetzalcoatl** is a cybersecurity system made during the **Smart India Hackathon (SIH)**.

It protects critical government, health, and energy systems from hackers using the **laws of quantum physics**.

Today, banks, power stations, and hospitals rely on standard math passwords (like RSA). When powerful quantum computers arrive, they will easily crack those passwords. Hackers could then fake government orders, shut down power grids, or alter hospital records without anyone noticing.

**Quetzalcoatl fixes this permanently.** Instead of relying on math that computers can break, it uses **Quantum Teleportation** and entangled photons. If a hacker tries to peek at, copy, or fake a message, the laws of physics immediately change the quantum state. The error rate spikes from **3% to 34%**, and the system blocks the attack on the spot.

> 💡 **No Guesswork / No AI Hallucinations**: Standard AI and Machine Learning can make mistakes or be tricked. Quetzalcoatl uses **100% exact statistics and physics**. It never guesses.

---

## 🚨 3 Life-Saving Missions Protected in SIH

We tested our system against 3 real-world emergencies where a cyber attack could cost human lives:

| Mission | What Is at Risk? | The Hacker's Attack | How Quetzalcoatl Saves the Day |
| :--- | :--- | :--- | :--- |
| 🏥 **Heart Transplant Delivery** | Hospital ICU & Transport System | **Fake Signature (Forgery)**: A hacker tries to change the recipient ID to steal a donor heart. | Detects the state change immediately (**QBER spikes to ~34%**), blocks the fake order, and ensures the child receives the life-saving heart. |
| ⚡ **Power Grid Blackout Defense** | Regional High-Voltage SCADA Stations | **Replay Attack**: A hacker re-sends an old emergency power shutdown command. | Checks fresh cryptographic time tokens (nonces); instantly drops the replayed command and shields **4.2 million citizens** from a blackout. |
| 🌾 **Emergency Disaster Relief** | $45M in Flood Aid for 120,000 People | **Bad Weather vs. Wire Fraud**: Storm water damages optical cables, creating natural noise. | Differentiates normal physical cable noise (10%) from true hacker forgery (34%), safely releasing $45M in flood relief without false alarms. |

---

## ✨ Main Features

- 🤖 **Autonomous Voice Guide (Agent Q)**: Click the **Tour Bot** button (`[T]`), lean back, and let the voice narrator guide you through every sector of the system automatically. No clicking required.
- 🎙️ **Deep AI & System Voices**: Powered by ElevenLabs Neural AI (Adam voice) and your computer's built-in voices. Includes custom voice presets (`Deep JARVIS`, `SOC Tactical`, `British Intel`) and pitch/speed sliders.
- 🎯 **Simple Mode & Analyst Mode**: Switch between a clean view with plain-English summaries (for leaders and judges) and an advanced view with quantum formulas and curves (for engineers).
- ⚡ **1-Click Attack Simulator**: Click one button to simulate quantum forgeries, channel noise, and replay attacks in real-time.
- 🔗 **Tamper-Proof Audit Ledger**: Every signature decision is hashed into a Merkle tree and verified on the blockchain, so no records can ever be secretly edited.
- 📱 **Works on Desktop and Mobile**: Run full operations on a desktop monitor or switch to the ultra-minimal view on a smartphone for field security officers.

---

## 🔬 How It Works (Simplified)

```mermaid
flowchart LR
    A["1. Alice (Sender)"] -->|Entangled Quantum Pairs| B["2. Quantum Teleportation"]
    B -->|Check Error Rate (QBER)| C{"Did Hacker Touch It?"}
    C -->|No: Error < 6%| D["✅ ACCEPT: Signature Authentic"]
    C -->|Yes: Error > 20%| E["🚫 BLOCK: Attack Interdicted!"]
    D --> F["📜 Immutable Merkle Audit Trail"]
    E --> F
```

1. **Entanglement**: Alice and Bob share entangled pairs of quantum bits (EPR pairs).
2. **Teleportation**: Alice performs a Bell State Measurement to sign the message. The message state is teleported without physically travelling through the cable.
3. **No-Cloning Rule**: Because quantum states **cannot be copied** (Heisenberg Uncertainty Principle & No-Cloning Theorem), any hacker trying to intercept the signature will disturb the quantum particles.
4. **Immediate Detection**: The disturbance creates an unavoidable error spike (>20%). Our statistical engine (Wald SPRT) catches this early and halts the transfer before any harm is done.

---

## 🚀 Quickstart (Run It in 3 Easy Steps)

### Step 1: Install Dependencies
Make sure you have **Python 3.11 or 3.12** installed:
```bash
pip install -r requirements.txt
```

### Step 2: Start the System
```bash
python run.py
```
*(Or run `python -m presentation.serve --port 8000`)*

### Step 3: Open Your Browser
Go to:
- 🖥️ **Main Command Center (Desktop SOC)**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 📱 **Ultra-Minimal Mobile View**: [http://127.0.0.1:8000/minimal](http://127.0.0.1:8000/minimal)
- 📖 **Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Run Automated Tests

To test every quantum circuit, attack injector, and statistical detection engine:
```bash
python -m pytest -q
```
**Result**: `45 passed (100% success rate)`.

---

## 🏆 Presentation Guide for Evaluators & Judges

When demonstrating Quetzalcoatl:

1. **Start the Auto-Tour**: Press `T` on your keyboard or click **`🤖 Tour Bot [T]`** in the top bar. Listen to the AI narrator explain each sector hands-free.
2. **Test an Attack**:
   - Go to **Sector 01** on the Cockpit.
   - Click **`Simulate Quantum Forgery`**.
   - Watch the radial gauge jump to **~34% error rate** and see the verdict change from **ACCEPT** to **BLOCK**.
3. **Show Real-World Social Impact**:
   - Click on the **National Mission Defense** cards (Pediatric Organ Dispatch, SCADA Power Grid, Disaster Relief).
   - Explain how quantum physics prevents blackouts and saves human lives.
4. **Switch Modes**:
   - Click **`Simple Mode`** to show executive-level cards.
   - Click **`SOC Analyst Mode`** to reveal Bell state math, Wald SPRT charts, and Hoeffding bounds.
5. **Show Mobile View**:
   - Open `http://127.0.0.1:8000/minimal` to demonstrate the lightweight mobile interface designed for security officers on the move.

---

## 📜 Project Background & Credits

- **Event**: Smart India Hackathon (SIH)
- **Base Research**: Built upon [`kartikeywastaken/qds-threat-detection`](https://github.com/kartikeywastaken/qds-threat-detection)
- **Quantum Protocol**: Bennett 1993 3-Qubit Quantum Teleportation Protocol
- **License**: [MIT License](LICENSE) — Free and open-source for national security and post-quantum research.
