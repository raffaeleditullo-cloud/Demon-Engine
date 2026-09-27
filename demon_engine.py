"""
DemonEngine: Motore di Sovrapposizione e Interferenza Ondulatoria per Agenti IA.

Ispirato al Demone di Maxwell e alla meccanica ondulatoria:
- Sovrapposizione: Esplorazione simultanea di N stati/ipotesi senza spreco sequenziale.
- Interferenza:
    * Costruttiva: Risonanza tra invarianti di correttezza, sicurezza e contratti.
    * Distruttiva: Cancellazione attiva di allucinazioni, antipattern e loop.
- Collasso: Estrazione deterministica dell'Eigenstate dominante con zero tentativi a vuoto.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
import math
import re
import time

@dataclass
class DemonHypothesis:
    id: str
    name: str
    content: str
    invariants: Set[str] = field(default_factory=set)
    antipatterns: Set[str] = field(default_factory=set)
    amplitude: float = 1.0
    phase: float = 0.0
    resonance_score: float = 0.0
    is_collapsed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DemonResult:
    scenario_name: str
    hypotheses: List[DemonHypothesis]
    interference_matrix: List[List[float]]
    eigenstate: DemonHypothesis
    coherence_percentage: float
    destructive_neutralizations: int
    constructive_resonances: int
    execution_time_ms: float
    audit_trail: List[str]

class DemonEngine:
    """
    Motore quantistico-probabilistico che filtra ipotesi parallele tramite interferenza ondulatoria.
    """
    # Soglia unica su |cos(d_phi)| sotto la quale una coppia è considerata ortogonale
    INTERFERENCE_THRESHOLD = 0.1

    def __init__(
        self,
        phase_damping: float = 1.2,
        coherence_threshold: float = 0.50,
        antipattern_penalty: float = 0.8
    ):
        self.phase_damping = phase_damping
        self.coherence_threshold = coherence_threshold
        self.antipattern_penalty = antipattern_penalty

    def _calculate_phase_difference(self, h1: DemonHypothesis, h2: DemonHypothesis) -> float:
        """
        Calcola la differenza di fase tra due onde di pensiero:
        Ordine di priorità:
        1. Verdetti diversi: opposizione di fase d_phi = 0.96*pi.
        2. Stesso verdetto: risonanza costruttiva d_phi in [0, pi/3], anche in presenza di antipattern.
        3. Nessun verdetto condiviso e antipattern presenti: sfasamento verso pi.
        4. Altrimenti: d_phi proporzionale alla distanza tra gli invarianti.
        """
        has_antipatterns = bool(h1.antipatterns or h2.antipatterns)
        total_antipatterns = len(h1.antipatterns) + len(h2.antipatterns)

        outcome1 = h1.metadata.get("verdict")
        outcome2 = h2.metadata.get("verdict")

        # 1. Opposizione ontologica di verdetto (es. safe vs dangerous)
        if outcome1 and outcome2 and outcome1 != outcome2:
            return math.pi * 0.96

        # Calcolo overlap invarianti Jaccard
        union_inv = len(h1.invariants.union(h2.invariants))
        inter_inv = len(h1.invariants.intersection(h2.invariants))
        jaccard = inter_inv / union_inv if union_inv > 0 else 0.0

        # 2. Concordanza di verdetto: fase costruttiva [0, pi/3].
        #    Valutata prima degli antipattern, così le risposte che concordano si rafforzano;
        #    i loro difetti restano penalizzati individualmente (internal_damping e diagonale).
        if outcome1 and outcome2 and outcome1 == outcome2:
            return (1.0 - jaccard) * (math.pi / 3.0)

        # 3. Senza verdetto condiviso, gli antipattern (allucinazioni, blocchi o loop)
        #    spingono la coppia verso l'opposizione di fase
        if has_antipatterns:
            # Sfasamento guidato verso pi (cancellazione distruttiva)
            penalty_shift = 0.2 * total_antipatterns
            return min(math.pi, (math.pi * 0.70) + penalty_shift)

        # Default proporzionale
        return (1.0 - jaccard) * (math.pi * 0.5)

    def compute_interference(
        self, hypotheses: List[DemonHypothesis], audit: List[str]
    ) -> Tuple[List[List[float]], int, int]:
        """
        Costruisce la matrice di interferenza quantistica:
        I_ij = A_i * A_j * cos(phi_i - phi_j)
        e calcola le ampiezze efficaci post-interferenza.

        La differenza di fase è calcolata una sola volta per coppia (i < j) e la stessa
        matrice dei coseni alimenta visualizzazione, contatori e punteggio, con un'unica
        soglia su cos(d_phi): l'audit descrive esattamente il calcolo che elegge il vincitore.
        """
        n = len(hypotheses)
        matrix = [[0.0] * n for _ in range(n)]
        constructive_count = 0
        destructive_count = 0

        audit.append(f"Avvio interferenza ondulatoria tra {n} stati simultanei...")

        # 1. Matrice dei coseni: d_phi è simmetrica, basta calcolarla per i < j
        cos_matrix = [[1.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                d_phi = self._calculate_phase_difference(hypotheses[i], hypotheses[j])
                cos_matrix[i][j] = cos_matrix[j][i] = math.cos(d_phi)

        # 2. Matrice di sovrapposizione mostrata e contatori
        for i in range(n):
            # Auto-interferenza scalata per eventuali antipattern intrinseci (solo visualizzazione)
            penalty = 1.0 - min(0.9, len(hypotheses[i].antipatterns) * self.antipattern_penalty * 0.5)
            matrix[i][i] = (hypotheses[i].amplitude ** 2) * penalty

            for j in range(i + 1, n):
                cos_factor = cos_matrix[i][j]
                term = hypotheses[i].amplitude * hypotheses[j].amplitude * cos_factor
                matrix[i][j] = matrix[j][i] = term

                if cos_factor > self.INTERFERENCE_THRESHOLD:
                    constructive_count += 1
                    audit.append(
                        f"  [+] Risonanza Costruttiva: {hypotheses[i].id} <-> {hypotheses[j].id} "
                        f"(cos(d_phi)={cos_factor:+.3f}, ampiezza={term:+.3f})"
                    )
                elif cos_factor < -self.INTERFERENCE_THRESHOLD:
                    destructive_count += 1
                    audit.append(
                        f"  [-] Annullamento Distruttivo: {hypotheses[i].id} <-> {hypotheses[j].id} "
                        f"(cos(d_phi)={cos_factor:+.3f}, ampiezza={term:+.3f})"
                    )

        # 3. Calcolo dell'Ampiezza Effettiva (Equazione del Demone)
        for i in range(n):
            s_plus = 0.0
            s_minus = 0.0
            for j in range(n):
                if i != j:
                    cos_factor = cos_matrix[i][j]
                    if cos_factor > self.INTERFERENCE_THRESHOLD:
                        s_plus += hypotheses[j].amplitude * cos_factor
                    elif cos_factor < -self.INTERFERENCE_THRESHOLD:
                        s_minus += hypotheses[j].amplitude * abs(cos_factor)

            # Penalità interna se l'ipotesi ha antipattern o allucinazioni
            internal_damping = 1.0 + (len(hypotheses[i].antipatterns) * self.antipattern_penalty)
            
            effective_amplitude = (
                hypotheses[i].amplitude * (1.0 + s_plus)
            ) / (internal_damping * (1.0 + self.phase_damping * s_minus))

            # Risonanza come densità di probabilità coerente |psi|^2
            hypotheses[i].resonance_score = effective_amplitude ** 2

        return matrix, constructive_count, destructive_count

    def collapse(
        self, scenario_name: str, hypotheses: List[DemonHypothesis]
    ) -> DemonResult:
        """
        Esegue il collasso della funzione d'onda nello stato dominante a minima entropia.
        """
        start_time = time.perf_counter()
        audit_trail: List[str] = [f"=== AVVIO CICLO DEMON: {scenario_name} ==="]

        # Fase di Interferenza
        matrix, const_count, dest_count = self.compute_interference(hypotheses, audit_trail)

        # Normalizzazione delle densità di probabilità
        total_energy = sum(h.resonance_score for h in hypotheses)
        audit_trail.append(f"Energia di coerenza residua del sistema: {total_energy:.4f}")

        if total_energy <= 0.0:
            audit_trail.append("CRITICO: Decoerenza totale. Collasso sullo stato a minima ampiezza di rumore.")
            eigenstate = hypotheses[0]
            coherence = 0.0
        else:
            for h in hypotheses:
                prob = (h.resonance_score / total_energy) * 100.0
                audit_trail.append(
                    f"  Stato [{h.id}] '{h.name}': Risonanza = {h.resonance_score:.4f} | Probabilità Collasso = {prob:5.1f}%"
                )
            
            # Eletto lo stato a massima densità di probabilità
            eigenstate = max(hypotheses, key=lambda h: h.resonance_score)
            coherence = (eigenstate.resonance_score / total_energy) * 100.0
            eigenstate.is_collapsed = True

        exec_time = (time.perf_counter() - start_time) * 1000.0
        audit_trail.append(
            f"Collasso completato in {exec_time:.2f}ms. Eigenstate eletto: [{eigenstate.id}] '{eigenstate.name}' ({coherence:.1f}% di coerenza)."
        )

        return DemonResult(
            scenario_name=scenario_name,
            hypotheses=hypotheses,
            interference_matrix=matrix,
            eigenstate=eigenstate,
            coherence_percentage=coherence,
            destructive_neutralizations=dest_count,
            constructive_resonances=const_count,
            execution_time_ms=exec_time,
            audit_trail=audit_trail,
        )
