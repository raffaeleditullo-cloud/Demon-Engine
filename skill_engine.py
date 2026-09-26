"""
Probabilistic Wave Interference & Superposition Engine for AI Agents.

Ispirato ai principi biologici e quantistici di calcolo a zero spreco:
- Superposition: Generazione parallela di N ipotesi / percorsi logici.
- Interference: Rafforzamento dei pattern invarianti e coerenti (costruttiva)
  e annullamento di allucinazioni e incongruenze (distruttiva).
- Wavefunction Collapse: Collasso deterministico/probabilistico sullo stato
  a minima entropia e massima verità coerente.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional, Tuple
import math
import re
import json
import time

@dataclass
class Hypothesis:
    id: str
    content: str
    reasoning_steps: List[str] = field(default_factory=list)
    key_claims: List[str] = field(default_factory=list)
    amplitude: float = 1.0        # Ampiezza iniziale della funzione d'onda
    phase: float = 0.0            # Fase d'onda [0, 2pi]
    resonance_score: float = 0.0  # Punteggio di interferenza accumulato
    decay_factor: float = 1.0     # Fattore di smorzamento (decoerenza)
    is_collapsed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InterferenceResult:
    hypotheses: List[Hypothesis]
    interference_matrix: List[List[float]]
    eigenstate: Hypothesis
    coherence_ratio: float
    destructive_cancellations: int
    constructive_reinforcements: int
    execution_time_ms: float
    audit_trail: List[str]

class ProbabilisticInterferenceSkill:
    """
    Skill modulare per agenti IA: esegue la sovrapposizione di N ipotesi
    e calcola l'interferenza costruttiva/distruttiva per il collasso dell'output.
    """
    
    def __init__(
        self,
        n_variants: int = 4,
        coherence_threshold: float = 0.65,
        phase_damping: float = 0.85,
        generator_fn: Optional[Callable[[str, int], List[Hypothesis]]] = None
    ):
        """
        :param n_variants: Numero di ipotesi nello stato di sovrapposizione (N).
        :param coherence_threshold: Soglia minima di risonanza per evitare il collasso a zero.
        :param phase_damping: Fattore di penalità per sfasamento/interferenza distruttiva.
        :param generator_fn: Funzione pluggabile per generare N ipotesi (LLM, prompt multi-temperature, ecc.).
        """
        self.n_variants = n_variants
        self.coherence_threshold = coherence_threshold
        self.phase_damping = phase_damping
        self.generator_fn = generator_fn

    def _extract_invariants(self, text: str) -> List[str]:
        """
        Estrae token/asserzioni invarianti (numeri, formule, keyword logiche, conclusioni).
        """
        invariants = []
        # Estrai numeri / frazioni / valori critici
        numbers = re.findall(r'\b\d+(?:[\./]\d+)?\b', text)
        invariants.extend([f"num:{n}" for n in numbers])
        
        # Estrai pattern logici/matematici chiave
        formula_matches = re.findall(r'(\b[A-Za-z_]+\s*=\s*[^,\n;]+)', text)
        invariants.extend([f"eq:{f.strip()}" for f in formula_matches])
        
        # Parole chiave deterministiche
        keywords = re.findall(r'\b(deadlock|race condition|monte carlo|condizionale|bayes|indipendente|combinatoria|campione|3/9|1/3|1/2|0\.333|0\.5)\b', text.lower())
        invariants.extend([f"kw:{kw}" for kw in keywords])
        
        return list(set(invariants))

    def _compute_phase_difference(self, h1: Hypothesis, h2: Hypothesis) -> float:
        """
        Calcola la differenza di fase tra due ipotesi in base alla sovrapposizione
        dei loro invarianti logici e delle conclusioni.
        - Se condividono le stesse conclusioni logiche: Delta phi -> 0 (In fase, interferenza costruttiva)
        - Se giungono a conclusioni mutuamente esclusive: Delta phi -> pi (Opposizione di fase, interferenza distruttiva)
        """
        s1 = set(h1.key_claims)
        s2 = set(h2.key_claims)
        
        if not s1 or not s2:
            return math.pi / 2  # Neutro / ortogonale

        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        jaccard = intersection / union if union > 0 else 0.0

        # Verifica di contraddizioni dirette sui risultati finali
        c1 = h1.metadata.get("final_answer")
        c2 = h2.metadata.get("final_answer")
        
        if c1 is not None and c2 is not None:
            if c1 == c2:
                # Fortissima coerenza di fase
                return (1.0 - jaccard) * 0.2 * math.pi
            else:
                # Opposizione di fase diretta (interferenza distruttiva netta)
                return math.pi * (0.8 + 0.2 * (1.0 - jaccard))

        # Altrimenti proporzionale alla sovrapposizione jaccard
        return (1.0 - jaccard) * math.pi

    def _cross_interference_scoring(self, hypotheses: List[Hypothesis], audit: List[str]) -> Tuple[List[List[float]], int, int]:
        """
        Calcola la matrice di interferenza quantistica:
        I_ij = A_i * A_j * cos(phi_i - phi_j)
        Interferenza costruttiva quando cos(delta) > 0, distruttiva quando cos(delta) < 0.
        """
        n = len(hypotheses)
        matrix = [[0.0] * n for _ in range(n)]
        destructive_count = 0
        constructive_count = 0

        audit.append(f"Calcolo della matrice di sovrapposizione su {n} stati simultanei...")

        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = hypotheses[i].amplitude ** 2
                else:
                    delta_phi = self._compute_phase_difference(hypotheses[i], hypotheses[j])
                    interference_term = (
                        hypotheses[i].amplitude * hypotheses[j].amplitude * math.cos(delta_phi)
                    )
                    matrix[i][j] = interference_term
                    
                    if i < j:
                        if interference_term > 0.1:
                            constructive_count += 1
                            audit.append(
                                f"  [+] Risonanza costruttiva tra H{hypotheses[i].id} e H{hypotheses[j].id} "
                                f"(cos(d_phi)={math.cos(delta_phi):+.3f}, term={interference_term:+.3f})"
                            )
                        elif interference_term < -0.1:
                            destructive_count += 1
                            audit.append(
                                f"  [-] Annullamento distruttivo tra H{hypotheses[i].id} e H{hypotheses[j].id} "
                                f"(cos(d_phi)={math.cos(delta_phi):+.3f}, term={interference_term:+.3f})"
                            )

        # Calcolo dell'Ampiezza Effettiva tramite equazione di interferenza ondulatoria:
        # A_eff_i = A_i * (1 + S_costruttivo) / (1 + phase_damping * S_distruttivo)
        # R_i = (A_eff_i)^2 (densità di probabilità quantistica |psi|^2)
        for i in range(n):
            s_plus = 0.0
            s_minus = 0.0
            for j in range(n):
                if i != j:
                    delta_phi = self._compute_phase_difference(hypotheses[i], hypotheses[j])
                    cos_val = math.cos(delta_phi)
                    if cos_val > 0.05:
                        s_plus += hypotheses[j].amplitude * cos_val
                    elif cos_val < -0.05:
                        s_minus += hypotheses[j].amplitude * abs(cos_val)

            effective_amplitude = (
                hypotheses[i].amplitude * (1.0 + s_plus) / (1.0 + self.phase_damping * s_minus)
            )
            # Intensità d'onda |psi|^2
            hypotheses[i].resonance_score = effective_amplitude ** 2

        return matrix, constructive_count, destructive_count

    def _collapse_wavefunction(
        self, hypotheses: List[Hypothesis], audit: List[str]
    ) -> Tuple[Hypothesis, float]:
        """
        Collasso della funzione d'onda:
        Seleziona lo stato autovettore (eigenstate) con la massima densità
        di probabilità coerente, eliminando le allucinazioni decoerenti.
        """
        total_resonance = sum(h.resonance_score for h in hypotheses)
        audit.append(f"Energia di risonanza complessiva: {total_resonance:.4f}")

        if total_resonance <= 0:
            # Fallback di sicurezza in caso di decoerenza totale
            audit.append("ATTENZIONE: Decoerenza totale rilevata. Selezione dello stato di base.")
            return hypotheses[0], 0.0

        # Normalizzazione delle probabilità di collasso
        normalized_probabilities = [
            h.resonance_score / total_resonance for h in hypotheses
        ]

        for idx, (h, prob) in enumerate(zip(hypotheses, normalized_probabilities)):
            audit.append(
                f"  Stato H{h.id}: probabilità di collasso = {prob*100:5.1f}% | "
                f"Risonanza netta = {h.resonance_score:.3f}"
            )

        # Selezione dell'autovettore dominante (massima probabilità coerente)
        best_hypothesis = max(hypotheses, key=lambda h: h.resonance_score)
        coherence_ratio = best_hypothesis.resonance_score / total_resonance
        best_hypothesis.is_collapsed = True

        audit.append(
            f"Collasso completato: Eletto stato H{best_hypothesis.id} "
            f"con grado di coerenza del {coherence_ratio*100:.1f}%."
        )

        return best_hypothesis, coherence_ratio

    def run(self, prompt: str) -> InterferenceResult:
        """
        Esegue il ciclo completo: Sovrapposizione -> Interferenza -> Collasso -> Output.
        """
        start_time = time.perf_counter()
        audit_trail: List[str] = []

        audit_trail.append("--- FASE 1: SOVRAPPOSIZIONE PROBABILISTICA (SUPERPOSITION) ---")
        if not self.generator_fn:
            raise ValueError("Nessun generator_fn specificato per la produzione di ipotesi.")

        # Genera le N ipotesi in parallelo / multivariante
        hypotheses = self.generator_fn(prompt, self.n_variants)
        audit_trail.append(f"Generate {len(hypotheses)} ipotesi parallele ad alta diversità.")

        # Estrazione degli atomi di conoscenza / asserzioni invarianti
        for h in hypotheses:
            if not h.key_claims:
                h.key_claims = self._extract_invariants(h.content)

        audit_trail.append("--- FASE 2: INTERFERENZA ONDULATORIA (INTERFERENCE) ---")
        matrix, const_count, dest_count = self._cross_interference_scoring(
            hypotheses, audit_trail
        )

        audit_trail.append("--- FASE 3: COLLASSO DELLA FUNZIONE D'ONDA (COLLAPSE) ---")
        eigenstate, coherence = self._collapse_wavefunction(hypotheses, audit_trail)

        exec_time = (time.perf_counter() - start_time) * 1000

        return InterferenceResult(
            hypotheses=hypotheses,
            interference_matrix=matrix,
            eigenstate=eigenstate,
            coherence_ratio=coherence,
            destructive_cancellations=dest_count,
            constructive_reinforcements=const_count,
            execution_time_ms=exec_time,
            audit_trail=audit_trail,
        )
