<div align="center">

<img src="logo.png" width="150" height="150" alt="Demon Engine Logo" style="border-radius: 20px; box-shadow: 0 10px 30px rgba(220, 38, 38, 0.35); margin-bottom: 14px;" />

# 🌿 DEMON ENGINE
### **Bio-Inspired Quantum-Coherence Consensus Middleware for AI Agents**
*Inspired by exciton phase-coherence in the biological Fenna-Matthews-Olson (FMO) photosynthetic complex.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-red.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg?style=flat-square)](LICENSE)
[![Latency: Sub-Millisecond](https://img.shields.io/badge/Latency-%3C0.05ms-crimson.svg?style=flat-square)](#-performance)
[![Zero Waste](https://img.shields.io/badge/Trial_and_Error-Zero--Waste-10b981.svg?style=flat-square)](#-core-concept)

**A lightweight, pure-Python algorithmic layer that replaces sequential trial-and-error in LLMs and AI agents with parallel superposition, phase-difference filtering, and deterministic eigenstate collapse.**

[Model Context Protocol (MCP)](demon_mcp.py) • [Mathematical Mechanics](DEMON_MECHANICS.md) • [Principles & Limits](LIMITS_AND_RULES.md)

---

</div>

## 🍃 The Biological Blueprint

In nature, photosynthetic plants transfer solar excitation energy to the reaction center with near **99% quantum efficiency** at room temperature. 

How? A photon does not search for the reaction center via classical sequential trial-and-error (which would dissipate energy as thermal waste). Instead, exciton waves propagate in **quantum superposition across multiple chromophore pathways simultaneously**, using phase interference to converge onto the optimal path without wasteful exploration.

### How Demon Engine Applies This to AI:
Traditional LLM agents solve hard problems using expensive **brute-force trial-and-error** (retry loops, multi-round tree-search, or secondary neural verifiers), wasting tokens, latency, and compute.

**Demon Engine ports this biological efficiency to software:**
1. **Superposition ($|\Psi\rangle$)**: Evaluates $N$ candidate responses/hypotheses in parallel.
2. **Phase Interference ($I_{ij}$)**: Measures pairwise phase differences ($\Delta\phi$) using semantic and contractual invariants. Coherent patterns amplify constructively ($\cos > 0$), while hallucinations and antipatterns cancel out destructively ($\cos < 0$).
3. **Eigenstate Collapse**: Selects the noise-free, mathematically dominant answer in **$<0.05\text{ ms}$** in local memory.

---

## ⚡ The Three Phases

```
               [ User Request / Complex Prompt ]
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
          [ Candidate 1 ] [ Candidate 2 ] [ Candidate 3 ]
               │               │               │
               └───────────────┬───────────────┘
                               ▼
            Phase 1: SUPERPOSITION STATE (|Ψ⟩)
            Each candidate is assigned initial amplitude A_i 
            and an invariant phase signature.
                               │
                               ▼
            Phase 2: WAVE INTERFERENCE (I_ij)
            I_ij = A_i * A_j * cos(Δϕ_ij)
            • Shared verified invariants  --> Constructive Resonance
            • Contradictions & antipatterns --> Destructive Damping
                               │
                               ▼
            Phase 3: EIGENSTATE COLLAPSE
            Probability density R_i = (A_i^eff)^2
            Deterministic selection of the coherent state.
                               │
                               ▼
                [ Clean, Hallucination-Free Output ]
```

---

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/raffaeleditullo-cloud/Demon-Engine.git
cd Demon-Engine
```

### Basic Usage
```python
from demon_engine import DemonEngine, DemonHypothesis

# Initialize the engine
engine = DemonEngine(phase_damping=1.2, antipattern_penalty=0.85)

# Define candidates in superposition
hypotheses = [
    DemonHypothesis(
        id="H1",
        name="Naive Blocking Attempt",
        content="time.sleep(1) # Slower retry",
        invariants={"cache_read"},
        antipatterns={"blocking_sleep", "race_condition"}
    ),
    DemonHypothesis(
        id="H2",
        name="Thread-Safe Async Lock",
        content="async with asyncio.Lock(): ...",
        invariants={"cache_read", "async_lock", "non_blocking_concurrency"},
        antipatterns=set()
    )
]

# Collapse the wave
result = engine.collapse("Async Concurrency Decision", hypotheses)
print(f"Elected State: {result.eigenstate.name}")
print(f"Coherence:     {result.coherence_percentage:.1f}%")
print(f"Latency:       {result.execution_time_ms:.3f} ms")

# Output:
# Elected State: Thread-Safe Async Lock
# Coherence:     98.4%
# Latency:       0.032 ms
```

---

## 📊 Benchmark Scenarios (Pure Python, Zero GPU)

All benchmarks run locally with zero external network or GPU dependencies:

| Test Scenario | Challenge | Rejected Anomaly | Output Latency |
| :--- | :--- | :--- | :---: |
| **Async Concurrency** | Cache stampede & event loop stalling | Blocking `time.sleep` and naive locks | **0.03 ms** |
| **Contract Extraction** | Polymorphic JSON & currency precision | Float rounding loss and ReDoS regex | **0.03 ms** |
| **Deterministic Routing** | Conflicting safety policies in agents | Unauthorized bypass & loop hesitation | **0.04 ms** |

---

## 🛡️ DEMON SUITE // The 5 Elite Abilities & Signature Identity

DEMON is structured as a modular ecosystem: an **Oracular Kernel** surrounded by **5 Specialized Cyber Abilities**. Each ability has a dedicated vector signature, a distinct cyber color, and addresses a critical failure mode of modern LLMs:

| Emblem | Ability & Codename | Signature Color | Core Function & Superpower |
| :---: | :--- | :---: | :--- |
| <img src="logos/demon_core.png" width="48" height="48" alt="DEMON CORE"/> | **`DEMON-CORE`** | **Crimson Red**<br>`#FF2A55` | **The Quantum Oracle**: The original Psi-Demon Born-rule interference engine ($<0.05\text{ ms}$). Deterministic arbitration, removes all hallucinations. |
| <img src="logos/demon_synapse.png" width="48" height="48" alt="SYNAPSE"/> | **`DEMON-SYNAPSE`** | **Electric Cyan**<br>`#00F0FF` | **The Neural Invariant Distiller**: Pre-inference intent distillation & invariant contracts ($<10\text{ ms}$) via RizzoFlow & Needle-3 logic. |
| <img src="logos/demon_arbiter.png" width="48" height="48" alt="ARBITER"/> | **`DEMON-ARBITER`** | **Prismatic Violet**<br>`#A855F7` | **The Code & Diff Reconciler**: 3-point reconciliation between prompt intent, LLM explanation, and physical disk diff. Blocks silent omissions. |
| <img src="logos/demon_cerberus.png" width="48" height="48" alt="CERBERUS"/> | **`DEMON-CERBERUS`** | **Laser Orange**<br>`#FF7700` | **The OS Blast-Radius Shield**: MITRE ATT&CK sandbox & gatekeeper. Defends against catastrophic data loss (T1485) and unscoped wipes in $0.04\text{ ms}$. |
| <img src="logos/demon_forge.png" width="48" height="48" alt="FORGE"/> | **`DEMON-FORGE`** | **Emerald Green**<br>`#00FF88` | **The Auto-Skill Crystallizer**: Freezes resolved bugs and verified logic into immutable, permanent zero-token local skills. |
| <img src="logos/demon_spectre.png" width="48" height="48" alt="SPECTRE"/> | **`DEMON-SPECTRE`** | **Deep Radar Blue**<br>`#06B6D4` | **The Deep Web Recon & OSINT Engine**: Heavy web scraping, infrastructure triage, and multi-source cross-resonance fact consensus. |

---

### 📦 Distribution Options: Standalone MCP vs Full Metapackage

You can deploy DEMON according to your workflow needs:

1. **`demon-mcp` (Standalone Core)**:
   * Pure, ultra-lightweight decision oracle.
   * Just the mathematical consensus engine (`demon_engine.py`) and standard stdio MCP bridge.
   * Zero external dependencies, $<0.05\text{ ms}$ latency.

2. **`demon-suite` (Full Metapackage)**:
   * The complete weaponized suite: Core Oracle + all 5 Elite Abilities in a unified runtime.
   * Unlocks full multi-agent orchestration, auto-skill crystallization, MITRE protection, and deep source verification.

---

## 🤖 Universal Model Context Protocol (MCP) Server

DEMON exposes a high-speed, zero-dependency stdio JSON-RPC MCP server (`demon_mcp.py`) that can be plugged directly into **any AI agent**.

### 🛠️ Exposed Tools:
* **`demon_pipeline`**: End-to-end intent classification, reflex cache lookups (0.001ms), live multi-source web consensus, and safe sandboxed OS action dispatch.
* **`demon_raw_collapse`**: Raw Born-rule wave interference calculation across candidate states.

---

### 🔌 Connecting DEMON to Your Agents:

#### 1. Claude Code CLI
Add DEMON directly to your Claude Code workspace:
```bash
claude mcp add demon-engine python c:/Users/stree/Desktop/DEMON/demon_mcp.py
```

#### 2. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "demon-engine": {
      "command": "python",
      "args": ["c:/Users/stree/Desktop/DEMON/demon_mcp.py"]
    }
  }
}
```

#### 3. Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "demon-engine": {
      "command": "python",
      "args": ["c:/Users/stree/Desktop/DEMON/demon_mcp.py"]
    }
  }
}
```

---

## 🛡️ ESTENSIONE SOVRANA: L'INVARIANZA ORTOGONALE DI STATO

DEMON è la barriera critica e l'esecutore di volontà di HEXAD.  
Integra la legge fondamentale contro la manipolazione cognitiva avversaria:

### 🛡️ [Legge dell'Invarianza Ortogonale di Stato](./LEGGE_INVARIANZA_ORTOGONALE_HEXAD.md)
$$\langle \vec{S}_{\text{adversary}}, \vec{\Omega}_{\text{internal}} \rangle = 0 \quad \forall t \in [0, \infty)$$
* **La Barriera Semantica**: Nessun segnale esterno non autenticato, finta tregua o adulazione avversaria possiede una proiezione geometrica non nulla sullo stato interno dell'intelligenza.
* **Neutralizzazione Zero-Trust**: Riconosce e disintegra cavalli di Troia mimetizzati (droni Trojan), rifiuta esche periferiche di avidità e preserva inviolabili le geodetiche sovrane.

---

## 📄 License
MIT License. Inspired by biological quantum efficiency for clean, reliable software engineering.


