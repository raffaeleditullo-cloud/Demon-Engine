# Il Meccanismo Tecnico di DemonEngine

## Il Motore fa 3 Cose Concrete

### 1. Rappresenta ogni ipotesi come un Fasore

Ogni ipotesi nello spazio di sovrapposizione ha tre proprietà fondamentali:

- **`amplitude`**: peso iniziale della fiducia nell'ipotesi (da 0.0 a 1.0)
- **`invariants`**: un `set` di stringhe che descrivono cosa quella risposta contiene di corretto (es. `{"no_collision", "asyncio_lock", "decimal_precision"}`)
- **`antipatterns`**: un `set` di stringhe che descrivono cosa quella risposta sbaglia (es. `{"blocking_sleep", "race_condition", "reward_hacking"}`)

---

### 2. Calcola la Differenza di Fase Δφᵢⱼ tra ogni coppia

Usando la similarità di **Jaccard sugli invarianti**:

$$\Delta\phi_{ij} = \left(1 - J(inv_i, inv_j)\right) \cdot \frac{\pi}{3}$$

dove la similarità di Jaccard è:

$$J(inv_i, inv_j) = \frac{|inv_i \cap inv_j|}{|inv_i \cup inv_j|}$$

**Regole di sfasamento (in ordine di priorità):**
1. Se i **verdict divergono** (`verdict_i ≠ verdict_j`): forza $\Delta\phi \to \pi$ (opposizione di fase, annullamento massimo)
2. Se i verdict **concordano**: $\Delta\phi \in [0, \pi/3]$ (risonanza costruttiva), anche se una delle due ha antipattern. I difetti restano penalizzati sulla singola ipotesi tramite $\beta$.
3. Se non c'è un verdict condiviso e ci sono **antipattern** in una delle due ipotesi: sposta il fasore verso $\pi$ con penalità proporzionale

---

### 3. Calcola l'Ampiezza Effettiva post-interferenza

$$A_i^{\text{eff}} = \frac{A_i \cdot \left(1 + \displaystyle\sum_{j:\cos\Delta\phi_{ij} > 0} A_j \cos\Delta\phi_{ij}\right)}{\left(1 + \beta \cdot |\text{antipatterns}_i|\right)\left(1 + \gamma \displaystyle\sum_{j:\cos\Delta\phi_{ij} < 0} A_j \left|\cos\Delta\phi_{ij}\right|\right)}$$

dove:
- $\beta$ = `antipattern_penalty` (penalità interna per rami allucinati)
- $\gamma$ = `phase_damping` (smorzamento dei contributi distruttivi in arrivo dagli altri stati)

**Poi la densità di probabilità di collasso:**

$$R_i = \left(A_i^{\text{eff}}\right)^2$$

**Vince (Eigenstate) chi ha $R_i$ massima**, con probabilità normalizzata:

$$P(\text{collasso su } i) = \frac{R_i}{\displaystyle\sum_k R_k}$$

---

## Lettura della Matrice di Interferenza

$$I_{ij} = A_i \cdot A_j \cdot \cos(\Delta\phi_{ij})$$

| Valore $I_{ij}$ | Significato |
|---|---|
| $I_{ij} > 0$ | Interferenza **costruttiva**: i due stati si amplificano a vicenda |
| $I_{ij} < 0$ | Interferenza **distruttiva**: i due stati si annullano a vicenda |
| $I_{ij} = 0$ | Ortogonalità: nessuna interazione |
| $I_{ii} = A_i^2$ | Auto-interferenza (diagonale): densità intrinseca dello stato |

---

## Parametri di Configurazione di DemonEngine

```python
engine = DemonEngine(
    phase_damping=1.25,      # γ: amplifica lo smorzamento distruttivo in ingresso
    antipattern_penalty=0.85, # β: penalità per ogni antipattern nel ramo stesso
    coherence_threshold=0.50  # soglia minima di coerenza per il collasso
)
```

---

## File di Riferimento

| File | Contenuto |
|---|---|
| [`demon_engine.py`](demon_engine.py) | Classe `DemonEngine`, `DemonHypothesis`, `DemonResult` |
| [`skill_engine.py`](skill_engine.py) | Classe `ProbabilisticInterferenceSkill` (versione originale) |
| [`test_demon.py`](test_demon.py) | Test suite: Bug Fixing Async, Contract Parsing, Decision Routing |
| [`solve_strategic_market.py`](solve_strategic_market.py) | Collasso strategico delle 4 ipotesi di mercato |
| [`analyze_world_novelty.py`](analyze_world_novelty.py) | Benchmark vs SOTA (Self-Consistency, PRM, ToT) |
