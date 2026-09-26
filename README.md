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

[Interactive Dashboard (index.html)](index.html) • [Mathematical Mechanics](DEMON_MECHANICS.md) • [Principles & Limits](LIMITS_AND_RULES.md)

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

## 🖥️ Local Interactive Dashboard

Demon Engine includes a lightweight, zero-dependency dashboard (`index.html`).
Double-click `index.html` in your browser to visualize:
- The chaotic superposition wave collapsing into a single resonant eigenstate.
- Real-time pairwise phase interference matrix ($I_{ij}$).
- Instant dampening of conflicting branches.

---

## 📄 License
MIT License. Inspired by biological quantum efficiency for clean, reliable software engineering.
