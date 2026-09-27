"""
demon_agent_filter: API di valutazione della coerenza per assistenti AI basata su DemonEngine.

Un agente AI produce più ipotesi di ragionamento per la stessa domanda (campionamento
multiplo, prompt diversi, agenti diversi). Questo modulo:

    1. NORMALIZZA le ipotesi in un formato unico (stringhe, dict o AgentHypothesis).
    2. RILEVA gli antipattern logici nascosti nel testo di ciascuna ipotesi:
         - errore_aritmetico          un calcolo scritto nel testo non torna ("6/20 / 18/20 = 1/2")
         - contraddizione_interna     la stessa affermazione compare affermata e negata
         - conclusione_non_supportata la risposta finale non compare nel ragionamento
         - certezza_non_giustificata  "sicuramente", "garantito"... senza alcuna motivazione
         - appello_all_autorita       "come tutti sanno", "fidati"... al posto delle prove
         - esitazione_eccessiva       troppi "forse", "potrebbe", "non sono sicuro"
         - ragionamento_circolare     la conclusione ripete una premessa
         - ragionamento_assente       risposta senza alcun passaggio a sostegno
       più quelli segnalati da validatori esterni (test, linter, policy: gli "oracoli").
    3. ESTRAE gli invarianti: i valori numerici dei calcoli verificati come corretti.
    4. RAGGRUPPA per verdetto: ipotesi con la stessa risposta finale si rafforzano,
       ipotesi con risposte diverse si annullano.
    5. COLLASSA con DemonEngine ed elegge la risposta a massima coerenza.
    6. VALUTA l'affidabilità: quota di consenso del gruppo vincente e avvisi.

Principio (da LIMITS_AND_RULES.md): la somiglianza non è verità. Il filtro premia la
coerenza tra ipotesi e punisce i difetti riconoscibili; non conosce la verità del mondo.
Per decisioni importanti affiancalo a validatori esterni deterministici (parametro
`validators`).

Esempio base
------------
>>> from demon_agent_filter import demon_filter
>>> result = demon_filter([
...     {"id": "bayes", "final_answer": "1/3",
...      "reasoning": ["P(RR) = 3/5 * 2/4 = 6/20",
...                    "P(almeno una R) = 1 - 2/20 = 18/20",
...                    "P(RR | almeno una R) = (6/20) / (18/20) = 1/3"]},
...     {"id": "combinatoria", "final_answer": "1/3",
...      "reasoning": ["Coppie totali: 10", "Coppie con almeno una rossa: 10 - 1 = 9",
...                    "Coppie entrambe rosse: 3, quindi 3/9 = 1/3"]},
...     {"id": "scorciatoia", "final_answer": "1/2",
...      "reasoning": ["P(RR | almeno una R) = (6/20) / (18/20) = 1/2"]},
... ])
>>> result.winner.id
'bayes'
>>> result.answer
'1/3'
>>> result.antipatterns_of("scorciatoia")
['errore_aritmetico']
>>> result.is_reliable
True

Ipotesi come semplici stringhe (nessuna risposta finale esplicita)
------------------------------------------------------------------
>>> result = demon_filter([
...     "Sicuramente è la soluzione migliore, fidati.",
...     "Conviene usare asyncio.Lock perché threading.Lock blocca l'event loop.",
... ])
>>> result.winner.id
'H2'
>>> result.antipatterns_of("H1")
['appello_all_autorita', 'certezza_non_giustificata', 'ragionamento_assente']

Validatore esterno (oracolo): ad esempio l'esito di una test suite
-------------------------------------------------------------------
>>> def tests_oracle(h):
...     # In un caso reale: esegui pytest sul codice proposto da h.content
...     return ["test_falliti"] if "time.sleep" in h.content else []
>>> result = demon_filter(
...     [{"id": "sleep", "content": "Aggiungo time.sleep(1) prima della fetch perché riduce le chiamate."},
...      {"id": "lock", "content": "Uso asyncio.Lock per chiave perché serializza le fetch concorrenti."}],
...     validators=[tests_oracle],
... )
>>> result.winner.id
'lock'
>>> result.antipatterns_of("sleep")
['test_falliti']

Esecuzione della demo completa: python demon_agent_filter.py
Esecuzione degli esempi qui sopra: python -m doctest demon_agent_filter.py -v
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Union

# DemonEngine vive nella cartella superiore: la rendiamo importabile anche se questo
# file viene eseguito direttamente da skill_demon_demo/.
try:
    from demon_engine import DemonEngine, DemonHypothesis, DemonResult
except ImportError:  # pragma: no cover - dipende da come viene lanciato lo script
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from demon_engine import DemonEngine, DemonHypothesis, DemonResult

__all__ = [
    "AgentHypothesis",
    "RankedHypothesis",
    "FilterResult",
    "Validator",
    "demon_filter",
    "detect_antipatterns",
    "format_report",
]


# =====================================================================================
# Strutture dati pubbliche
# =====================================================================================

@dataclass
class AgentHypothesis:
    """Un'ipotesi di ragionamento prodotta dall'agente.

    :param id: identificativo univoco (assegnato in automatico se manca).
    :param content: testo libero della risposta.
    :param reasoning: passaggi del ragionamento, uno per elemento.
    :param final_answer: risposta finale sintetica; decide il gruppo di verdetto.
    :param confidence: fiducia iniziale in (0, 1]; diventa l'ampiezza dell'onda.
    :param invariants: proprietà corrette già note (es. controlli superati).
    :param antipatterns: difetti già noti, dichiarati da chi chiama.
    """
    id: str
    content: str = ""
    reasoning: List[str] = field(default_factory=list)
    final_answer: Optional[str] = None
    confidence: float = 1.0
    invariants: Set[str] = field(default_factory=set)
    antipatterns: Set[str] = field(default_factory=set)

    @property
    def full_text(self) -> str:
        """Tutto il testo analizzabile: contenuto più passaggi del ragionamento."""
        return "\n".join([self.content, *self.reasoning]).strip()


@dataclass
class RankedHypothesis:
    """Posizione di un'ipotesi dopo il collasso."""
    id: str
    probability: float          # quota percentuale della risonanza totale
    resonance: float            # R_i = (A_eff)^2 calcolata da DemonEngine
    verdict: Optional[str]      # risposta finale normalizzata (gruppo)
    antipatterns: List[str]     # difetti rilevati o dichiarati


@dataclass
class FilterResult:
    """Esito della valutazione di coerenza."""
    answer: str                         # risposta finale (o contenuto) dell'ipotesi eletta
    winner: AgentHypothesis             # ipotesi eletta
    coherence: float                    # quota % del solo vincitore
    consensus_share: float              # quota % di tutto il gruppo con lo stesso verdetto
    is_reliable: bool                   # consenso sufficiente e vincitore senza difetti
    ranking: List[RankedHypothesis]     # tutte le ipotesi, dalla più coerente
    warnings: List[str]                 # avvisi da leggere prima di fidarsi del risultato
    audit_trail: List[str]              # registro completo del collasso
    engine_result: DemonResult          # risultato grezzo di DemonEngine

    def antipatterns_of(self, hypothesis_id: str) -> List[str]:
        """Antipattern (ordinati) di un'ipotesi, dato il suo id."""
        for ranked in self.ranking:
            if ranked.id == hypothesis_id:
                return ranked.antipatterns
        raise KeyError(hypothesis_id)


# Un validatore riceve l'ipotesi e restituisce le etichette degli antipattern trovati.
Validator = Callable[[AgentHypothesis], Iterable[str]]
HypothesisInput = Union[str, Dict[str, Any], AgentHypothesis]


# =====================================================================================
# Lessico per il rilevamento degli antipattern (italiano e inglese)
# =====================================================================================

_CERTAINTY = [
    "certamente", "sicuramente", "senza dubbio", "ovviamente", "garantito", "al 100%",
    "definitely", "obviously", "certainly", "guaranteed", "without a doubt",
]
_JUSTIFICATION = [
    "perché", "perche", "poiché", "poiche", "quindi", "dunque", "infatti", "dato che",
    "siccome", "because", "since", "therefore", "thus", "hence", "=",
]
_AUTHORITY = [
    "come tutti sanno", "è noto che", "e' noto che", "fidati", "lo dicono gli esperti",
    "everyone knows", "trust me", "experts agree", "it is well known",
]
_HEDGING = [
    "forse", "potrebbe", "probabilmente", "non sono sicuro", "credo che", "non so",
    "maybe", "perhaps", "might", "i think", "not sure",
]
_NEGATIONS = {"non", "not", "no", "mai", "never"}

# Caratteri ammessi in un'espressione aritmetica scritta nel testo
_ARITH_CHARS = r"[\d\.\s\+\-\*/\(\)]"
_TRAILING_EXPR = re.compile(rf"{_ARITH_CHARS}*$")
_LEADING_EXPR = re.compile(rf"^{_ARITH_CHARS}*")
_NUMBER_TOKEN = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?\s*%?")


def _contains_phrase(text: str, phrases: Sequence[str]) -> List[str]:
    """Restituisce le frasi del lessico presenti nel testo (a parola intera)."""
    found = []
    for phrase in phrases:
        if phrase == "=":
            if "=" in text:
                found.append(phrase)
            continue
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text):
            found.append(phrase)
    return found


# =====================================================================================
# Aritmetica sicura (nessun eval: solo numeri e + - * / con parentesi)
# =====================================================================================

def _safe_eval(expression: str) -> Optional[float]:
    """Valuta un'espressione puramente aritmetica; None se non lo è."""
    expression = expression.strip()
    if not expression or not re.search(r"\d", expression):
        return None
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return None

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = _eval(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = _eval(node.left), _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        raise ValueError("espressione non aritmetica")

    try:
        return _eval(tree)
    except (ValueError, ZeroDivisionError):
        return None


def _has_operator(expression: str) -> bool:
    # Il meno iniziale di un numero negativo non conta come operazione
    return bool(re.search(r"(?<=[\d\)\s])[\+\-\*/]", expression.strip()))


def _cut_unbalanced(expression: str) -> str:
    """Taglia una coda con parentesi aperta e non chiusa: '0.30 (30' -> '0.30'."""
    depth, last_open = 0, -1
    for index, char in enumerate(expression):
        if char == "(":
            depth += 1
            last_open = index if depth == 1 else last_open
        elif char == ")":
            depth -= 1
    return expression[:last_open] if depth > 0 and last_open >= 0 else expression


def _prepare_math_text(text: str) -> str:
    # Uniforma la notazione: virgola decimale, simboli di moltiplicazione e divisione
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    return text.replace("×", "*").replace("÷", "/").replace("≈", "=")


def _left_operand(segment: str) -> Optional[str]:
    """Espressione aritmetica in coda al segmento, se non fa parte di un nome (es. P(B))."""
    match = _TRAILING_EXPR.search(segment)
    expression = match.group(0) if match else ""
    start = len(segment) - len(expression)
    if start > 0 and segment[start - 1].isalpha():
        return None  # chiamata tipo C(5,2) o P(RR): non è un numero
    return expression if re.search(r"\d", expression) else None


def _right_operand(segment: str) -> Optional[str]:
    """Espressione aritmetica in testa al segmento, se non prosegue con lettere (es. 1 - P)."""
    match = _LEADING_EXPR.match(segment)
    expression = match.group(0) if match else ""
    rest = segment[len(expression):]
    if rest[:1].isalpha():
        return None  # l'espressione continua con un simbolo: non è verificabile
    expression = _cut_unbalanced(expression)
    return expression if re.search(r"\d", expression) else None


def _check_arithmetic(text: str) -> tuple[List[str], Set[float]]:
    """Verifica le catene 'a = b = c' scritte nel testo.

    Restituisce (errori trovati, valori dei calcoli corretti).
    """
    errors: List[str] = []
    verified_values: Set[float] = set()
    text = _prepare_math_text(text)

    # Frasi: a capo, oppure punto seguito da spazio e maiuscola (non spezza i decimali)
    for sentence in re.split(r"\n|(?<=[.!?;])\s+(?=[A-ZÀ-Ý])", text):
        segments = sentence.split("=")
        for left_seg, right_seg in zip(segments, segments[1:]):
            left_expr, right_expr = _left_operand(left_seg), _right_operand(right_seg)
            if not left_expr or not right_expr:
                continue
            if not (_has_operator(left_expr) or _has_operator(right_expr)):
                continue  # "x = 5": nessun calcolo da verificare
            left_val, right_val = _safe_eval(left_expr), _safe_eval(right_expr)
            if left_val is None or right_val is None:
                continue
            tolerance = max(5e-3, 1e-2 * max(abs(left_val), abs(right_val)))
            if abs(left_val - right_val) > tolerance:
                errors.append(f"{left_expr.strip()} = {right_expr.strip()}")
            else:
                verified_values.update({round(left_val, 3), round(right_val, 3)})
    return errors, verified_values


def _numeric_value(raw: str) -> Optional[float]:
    """Interpreta '1/3', '0,333', '33.3%' come numero; None se non è numerico."""
    cleaned = _prepare_math_text(raw).strip().rstrip(".")
    is_percent = cleaned.endswith("%")
    cleaned = cleaned.rstrip("%").strip()
    if not re.fullmatch(r"[\d\.\s/\+\-\*\(\)]+", cleaned):
        return None
    value = _safe_eval(cleaned)
    if value is None:
        return None
    return value / 100.0 if is_percent else value


def _normalize_answer(answer: Optional[str]) -> Optional[str]:
    """Chiave di verdetto: '1/3', '0,333' e '33.3%' finiscono nello stesso gruppo."""
    if answer is None or not str(answer).strip():
        return None
    value = _numeric_value(str(answer))
    if value is not None:
        return f"num:{value:.3f}"
    text = re.sub(r"[^\w\s]", " ", str(answer).lower())
    return "txt:" + " ".join(text.split())


# =====================================================================================
# FASE 2 — Rilevamento degli antipattern logici nascosti
# =====================================================================================

def detect_antipatterns(hypothesis: AgentHypothesis) -> tuple[Set[str], Set[str], List[str]]:
    """Analizza un'ipotesi e restituisce (antipattern, invarianti, dettagli leggibili).

    >>> h = AgentHypothesis(id="x", reasoning=["2 + 2 = 5"], final_answer="5")
    >>> sorted(detect_antipatterns(h)[0])
    ['errore_aritmetico']
    """
    text = hypothesis.full_text
    lowered = text.lower()
    antipatterns: Set[str] = set()
    invariants: Set[str] = set()
    details: List[str] = []

    # 2a. Calcoli sbagliati scritti nel ragionamento
    arithmetic_errors, verified_values = _check_arithmetic(text)
    if arithmetic_errors:
        antipatterns.add("errore_aritmetico")
        details.extend(f"calcolo errato: {e}" for e in arithmetic_errors)
    # I calcoli corretti diventano invarianti condivisibili con le altre ipotesi
    invariants.update(f"val:{v:.3f}" for v in verified_values)

    # 2b. Stessa affermazione presente sia affermata sia negata
    seen: Dict[str, bool] = {}
    for sentence in re.split(r"(?<=[.!?;])\s+|\n", lowered):
        words = re.findall(r"\w+", sentence)
        core = [w for w in words if w not in _NEGATIONS]
        if len(core) < 3:
            continue
        key, negated = " ".join(core), len(core) != len(words)
        if key in seen and seen[key] != negated:
            antipatterns.add("contraddizione_interna")
            details.append(f"affermato e negato: '{key}'")
        seen.setdefault(key, negated)

    # 2c. Risposta finale che non compare da nessuna parte nel ragionamento
    if hypothesis.final_answer and hypothesis.full_text:
        final_value = _numeric_value(hypothesis.final_answer)
        if final_value is not None:
            mentioned = {_numeric_value(tok) for tok in _NUMBER_TOKEN.findall(_prepare_math_text(text))}
            mentioned.discard(None)
            mentioned |= verified_values
            supported = any(abs(final_value - v) <= 5e-3 for v in mentioned)
        else:
            answer_key = " ".join(re.findall(r"\w+", hypothesis.final_answer.lower()))
            supported = len(answer_key) > 60 or answer_key in " ".join(re.findall(r"\w+", lowered))
        if not supported:
            antipatterns.add("conclusione_non_supportata")
            details.append(f"la risposta '{hypothesis.final_answer}' non deriva dal ragionamento")

    # 2d. Certezza assoluta senza alcuna motivazione
    certainty = _contains_phrase(lowered, _CERTAINTY)
    if certainty and not _contains_phrase(lowered, _JUSTIFICATION):
        antipatterns.add("certezza_non_giustificata")
        details.append(f"certezza senza motivazione: {', '.join(certainty)}")

    # 2e. Autorità invocata al posto delle prove
    authority = _contains_phrase(lowered, _AUTHORITY)
    if authority:
        antipatterns.add("appello_all_autorita")
        details.append(f"appello all'autorità: {', '.join(authority)}")

    # 2f. Troppa esitazione: l'ipotesi non si impegna su nulla
    hedges = sum(len(re.findall(rf"(?<!\w){re.escape(p)}(?!\w)", lowered)) for p in _HEDGING)
    if hedges >= 2:
        antipatterns.add("esitazione_eccessiva")
        details.append(f"{hedges} espressioni di esitazione")

    # 2g. La conclusione ripete una premessa (ragionamento che gira in tondo)
    steps = [set(re.findall(r"\w+", s.lower())) for s in hypothesis.reasoning]
    if len(steps) >= 3 and len(steps[-1]) >= 4:
        for premise in steps[:-1]:
            union = premise | steps[-1]
            if union and len(premise & steps[-1]) / len(union) >= 0.85:
                antipatterns.add("ragionamento_circolare")
                details.append("la conclusione ripete una premessa")
                break

    # 2h. Nessun passaggio a sostegno della risposta
    has_justification = bool(_contains_phrase(lowered, _JUSTIFICATION))
    if not hypothesis.reasoning and not has_justification:
        antipatterns.add("ragionamento_assente")
        details.append("nessun passaggio o motivazione a sostegno")

    return antipatterns, invariants, details


# =====================================================================================
# FASE 1 — Normalizzazione dell'input
# =====================================================================================

def _coerce(item: HypothesisInput, index: int) -> AgentHypothesis:
    """Converte stringhe e dict in AgentHypothesis (con alias comuni per i campi)."""
    default_id = f"H{index}"
    if isinstance(item, AgentHypothesis):
        return AgentHypothesis(
            id=item.id or default_id, content=item.content, reasoning=list(item.reasoning),
            final_answer=item.final_answer, confidence=item.confidence,
            invariants=set(item.invariants), antipatterns=set(item.antipatterns),
        )
    if isinstance(item, str):
        return AgentHypothesis(id=default_id, content=item)
    if isinstance(item, dict):
        reasoning = item.get("reasoning", item.get("steps", []))
        if isinstance(reasoning, str):
            reasoning = [line for line in reasoning.splitlines() if line.strip()]
        answer = item.get("final_answer", item.get("answer"))
        return AgentHypothesis(
            id=str(item.get("id") or default_id),
            content=str(item.get("content", "")),
            reasoning=[str(step) for step in reasoning],
            final_answer=None if answer is None else str(answer),
            confidence=float(item.get("confidence", 1.0)),
            invariants=set(item.get("invariants", [])),
            antipatterns=set(item.get("antipatterns", [])),
        )
    raise TypeError(f"Ipotesi {index}: tipo non supportato ({type(item).__name__}).")


# =====================================================================================
# API principale
# =====================================================================================

def demon_filter(
    hypotheses: Sequence[HypothesisInput],
    *,
    validators: Optional[Sequence[Validator]] = None,
    phase_damping: float = 1.25,
    antipattern_penalty: float = 0.85,
    min_consensus: float = 60.0,
    scenario_name: str = "Valutazione coerenza agente",
) -> FilterResult:
    """Valuta le ipotesi di un agente ed elegge la risposta più coerente.

    :param hypotheses: ipotesi come stringhe, dict (chiavi: id, content, reasoning/steps,
        final_answer/answer, confidence, invariants, antipatterns) o AgentHypothesis.
    :param validators: oracoli esterni; ognuno riceve un'ipotesi e restituisce le
        etichette degli antipattern trovati (test falliti, errori di linter, policy violate).
    :param phase_damping: γ di DemonEngine, peso dell'opposizione tra ipotesi.
    :param antipattern_penalty: β di DemonEngine, peso di ogni antipattern.
    :param min_consensus: quota % minima del gruppo vincente per dirsi affidabile.
    :param scenario_name: nome riportato nel registro del collasso.
    :return: FilterResult con risposta eletta, classifica, avvisi e registro.

    >>> demon_filter(["Uso Decimal per gli importi perché float perde precisione."]).winner.id
    'H1'
    """
    if not hypotheses:
        raise ValueError("Serve almeno un'ipotesi da valutare.")

    # ---- FASE 1: normalizzazione -------------------------------------------------------
    agent_hyps = [_coerce(item, i) for i, item in enumerate(hypotheses, start=1)]
    ids = [h.id for h in agent_hyps]
    if len(set(ids)) != len(ids):
        raise ValueError(f"ID duplicati tra le ipotesi: {ids}")
    for h in agent_hyps:
        if not 0.0 < h.confidence <= 1.0:
            raise ValueError(f"Ipotesi {h.id}: confidence deve essere in (0, 1].")

    audit_prefix: List[str] = ["--- RILEVAMENTO ANTIPATTERN ---"]
    engine_hyps: List[DemonHypothesis] = []
    detected: Dict[str, List[str]] = {}

    for h in agent_hyps:
        # ---- FASE 2: antipattern nascosti (analisi del testo) --------------------------
        found, invariants, details = detect_antipatterns(h)

        # ---- FASE 2 bis: antipattern dagli oracoli esterni -----------------------------
        for validator in validators or []:
            found.update(str(label) for label in validator(h))

        all_antipatterns = found | h.antipatterns
        detected[h.id] = sorted(all_antipatterns)
        audit_prefix.append(
            f"  [{h.id}] antipattern: {', '.join(detected[h.id]) or 'nessuno'}"
            + (f" ({'; '.join(details)})" if details else "")
        )

        # ---- FASE 3: invarianti + FASE 4: gruppo di verdetto ---------------------------
        engine_hyps.append(
            DemonHypothesis(
                id=h.id,
                name=h.final_answer or (h.content[:60] or h.id),
                content=h.full_text,
                invariants=invariants | h.invariants,
                antipatterns=all_antipatterns,
                amplitude=h.confidence,
                metadata={"verdict": _normalize_answer(h.final_answer)},
            )
        )

    # ---- FASE 5: collasso ondulatorio --------------------------------------------------
    engine = DemonEngine(phase_damping=phase_damping, antipattern_penalty=antipattern_penalty)
    raw = engine.collapse(scenario_name, engine_hyps)

    total = sum(h.resonance_score for h in raw.hypotheses) or 1.0
    by_id = {h.id: h for h in agent_hyps}
    winner_engine = raw.eigenstate
    winner = by_id[winner_engine.id]
    winner_verdict = winner_engine.metadata.get("verdict")

    ranking = sorted(
        (
            RankedHypothesis(
                id=h.id,
                probability=h.resonance_score / total * 100.0,
                resonance=h.resonance_score,
                verdict=h.metadata.get("verdict"),
                antipatterns=detected[h.id],
            )
            for h in raw.hypotheses
        ),
        key=lambda r: r.resonance,
        reverse=True,
    )

    # ---- FASE 6: affidabilità ----------------------------------------------------------
    # La quota del solo vincitore si divide tra ipotesi "gemelle" corrette: per giudicare
    # l'affidabilità conta la quota dell'intero gruppo con lo stesso verdetto.
    if winner_verdict is None:
        consensus_share = raw.coherence_percentage
    else:
        consensus_share = sum(r.probability for r in ranking if r.verdict == winner_verdict)

    warnings: List[str] = []
    if detected[winner.id]:
        warnings.append(
            "La risposta eletta contiene antipattern: nessuna ipotesi è priva di difetti. "
            "Rigenera le ipotesi o verifica a mano."
        )
    if consensus_share < min_consensus:
        warnings.append(
            f"Consenso debole: il gruppo vincente pesa {consensus_share:.1f}% "
            f"(soglia {min_consensus:.0f}%)."
        )
    verdicts = {r.verdict for r in ranking}
    if len(agent_hyps) > 1 and len(verdicts) == 1 and None not in verdicts:
        warnings.append(
            "Tutte le ipotesi danno la stessa risposta: il consenso non garantisce la verità "
            "(possibile bias comune). Conferma con un validatore esterno."
        )
    if len(agent_hyps) == 1:
        warnings.append("Una sola ipotesi: nessun confronto possibile, solo i controlli sul testo.")

    return FilterResult(
        answer=winner.final_answer or winner.content or "\n".join(winner.reasoning),
        winner=winner,
        coherence=raw.coherence_percentage,
        consensus_share=consensus_share,
        is_reliable=not detected[winner.id] and consensus_share >= min_consensus,
        ranking=ranking,
        warnings=warnings,
        audit_trail=audit_prefix + raw.audit_trail,
        engine_result=raw,
    )


def format_report(result: FilterResult) -> str:
    """Riepilogo testuale leggibile di un FilterResult."""
    lines = [
        f"Risposta eletta:   {result.answer}",
        f"Ipotesi vincente:  {result.winner.id}",
        f"Coerenza:          {result.coherence:.1f}% (gruppo di consenso {result.consensus_share:.1f}%)",
        f"Affidabile:        {'sì' if result.is_reliable else 'no'}",
        "",
        "Classifica:",
    ]
    id_width = max(len(r.id) for r in result.ranking)
    for r in result.ranking:
        marker = "►" if r.id == result.winner.id else " "
        lines.append(
            f" {marker} {r.id:<{id_width}}  {r.probability:6.2f}%   "
            f"antipattern: {', '.join(r.antipatterns) or 'nessuno'}"
        )
    if result.warnings:
        lines += ["", "Avvisi:"] + [f" - {w}" for w in result.warnings]
    return "\n".join(lines)


# =====================================================================================
# Demo: quattro ipotesi di un agente sul problema dell'urna (test_interference.py)
# =====================================================================================

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    question = (
        "Un'urna contiene 3 palline rosse e 2 blu. Se ne estraggono due senza reinserimento. "
        "Sapendo che almeno una è rossa, qual è la probabilità che lo siano entrambe?"
    )

    agent_output = [
        {   # Tranello classico: "tolgo la rossa" — calcoli giusti, modello sbagliato
            "id": "rimozione",
            "final_answer": "1/2",
            "reasoning": [
                "Tolgo mentalmente la pallina rossa già nota.",
                "Restano 4 palline: 2 rosse e 2 blu, quindi 2/4 = 1/2.",
            ],
            "confidence": 0.9,
        },
        {   # Errore aritmetico nascosto nell'ultimo passaggio
            "id": "bayes_sbagliato",
            "final_answer": "1/2",
            "reasoning": [
                "P(RR) = 3/5 * 2/4 = 6/20",
                "P(almeno una R) = 1 - 2/20 = 18/20",
                "P(RR | almeno una R) = (6/20) / (18/20) = 1/2",
            ],
        },
        {   # Corretta, via teorema di Bayes
            "id": "bayes",
            "final_answer": "1/3",
            "reasoning": [
                "P(RR) = 3/5 * 2/4 = 6/20",
                "P(BB) = 2/5 * 1/4 = 2/20, quindi P(almeno una R) = 1 - 2/20 = 18/20",
                "P(RR | almeno una R) = (6/20) / (18/20) = 6/18 = 1/3",
            ],
        },
        {   # Corretta, via combinatoria: stessa risposta, strada diversa
            "id": "combinatoria",
            "final_answer": "0,333",
            "reasoning": [
                "Coppie possibili: 10. Coppie senza rosse: 1.",
                "Coppie con almeno una rossa: 10 - 1 = 9",
                "Coppie entrambe rosse: 3, quindi 3/9 = 0.333",
            ],
        },
        {   # Nessuna prova, solo sicurezza e autorità
            "id": "sicumera",
            "final_answer": "3/10",
            "content": "Sicuramente 3/10, come tutti sanno.",
            "confidence": 0.8,
        },
    ]

    print("=" * 78)
    print(" DEMON AGENT FILTER: valutazione di coerenza ".center(78, "="))
    print("=" * 78)
    print(f"\nDomanda: {question}\n")

    result = demon_filter(agent_output, scenario_name="Urna: probabilità condizionata")
    print(format_report(result))

    print("\n" + " Registro del collasso ".center(78, "-"))
    for line in result.audit_trail:
        print(line)
