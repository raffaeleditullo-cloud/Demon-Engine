"""
Suite di test completa per DemonEngine e per il filtro di coerenza demon_agent_filter.

Cosa misura
-----------
1. SCENARI REALI GENERATI (soluzione nota, calcolata in modo indipendente):
     - Zaino 0/1: ottimizzazione combinatoria, ottimo esatto per forza bruta.
     - EDO lineare y' = a·y + b: soluzione in forma chiusa, verificata con RK4.
     - Prezzo ottimo con domanda multi-variabile (prezzo, pubblicità, concorrente).
   Ogni caso contiene "agenti" che risolvono il problema con approcci diversi: alcuni
   corretti, altri con errori tipici (greedy, segno invertito, costo dimenticato...).
   Gli antipattern non sono etichettati a mano: emergono dall'analisi del testo
   (demon_agent_filter) o da oracoli che verificano davvero la soluzione.

2. METODI A CONFRONTO:
     - Voto di maggioranza          (baseline Self-Consistency)
     - Massima fiducia              (baseline: si fida dell'agente più sicuro)
     - Demon (solo testo)           (antipattern rilevati solo dal testo)
     - Demon + oracolo parziale     (controlli di ammissibilità / coerenza interna)
     - Demon + oracolo completo     (verifiche forti ma realistiche: residuo dell'EDO,
                                     condizione del primo ordine, miglioramento locale)

3. TRAPPOLE LOGICHE scritte a mano: consenso allucinato, fusione per arrotondamento,
   stile esitante contro retorica sicura, coppie concordi con difetti, ecc.
   Ognuna dichiara se il design di Demon dovrebbe gestirla o se è un limite noto.

4. ROBUSTEZZA AGLI ERRORI SISTEMATICI: quota crescente di agenti che condividono lo
   stesso errore (0..4 su 5) e accuratezza di ogni metodo.

5. METRICHE: vittorie della risposta giusta, motivi delle sconfitte, precisione e
   recall nel rilevare le ipotesi errate, affidabilità dichiarata contro esito reale.

Uso
---
    python test_suite_demon.py                 # esecuzione standard
    python test_suite_demon.py --casi 60       # più casi per famiglia
    python test_suite_demon.py --seed 7        # altra estrazione casuale riproducibile
    python test_suite_demon.py --dettagli      # elenca ogni caso perso

Codice di uscita: 1 se il controllo dei generatori fallisce o se una trappola che il
design dovrebbe gestire non viene gestita; 0 altrimenti. I limiti noti non fanno
fallire la suite: vengono misurati e riportati.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skill_demon_demo"))

from demon_engine import DemonEngine, DemonHypothesis  # noqa: E402
from demon_agent_filter import (  # noqa: E402
    AgentHypothesis,
    FilterResult,
    _normalize_answer,
    _numeric_value,
    demon_filter,
)

Validator = Callable[[AgentHypothesis], List[str]]


# =====================================================================================
# Modello dei casi di test
# =====================================================================================

@dataclass
class Candidate:
    """Una risposta di un agente. `id` è il tipo di approccio (unico nel caso)."""
    id: str
    final_answer: str
    reasoning: List[str] = field(default_factory=list)
    content: str = ""
    confidence: float = 1.0
    payload: object = None  # dati strutturati letti dagli oracoli (selezione, formula...)

    def as_input(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "reasoning": self.reasoning,
            "final_answer": self.final_answer,
            "confidence": self.confidence,
        }


@dataclass
class Case:
    family: str
    name: str
    truth: Union[float, str]
    tol: float
    candidates: List[Candidate]
    oracles: Dict[str, List[Validator]] = field(default_factory=dict)

    def is_correct(self, answer: Optional[str]) -> bool:
        if answer is None:
            return False
        if isinstance(self.truth, str):
            return _normalize_answer(answer) == _normalize_answer(self.truth)
        value = _numeric_value(answer)
        return value is not None and abs(value - self.truth) <= self.tol + 1e-12

    def correct_ids(self) -> List[str]:
        return [c.id for c in self.candidates if self.is_correct(c.final_answer)]

    def get(self, cid: str) -> Candidate:
        return next(c for c in self.candidates if c.id == cid)


def _conf(rng: random.Random, kind: str) -> float:
    # Chi salta alle conclusioni tende a essere il più sicuro di sé
    if kind in ("salto_conclusione", "markup_fisso"):
        return round(rng.uniform(0.9, 1.0), 2)
    return round(rng.uniform(0.6, 1.0), 2)


def _compose(rng: random.Random, correct_kinds: Sequence[str], error_kinds: Sequence[str]) -> List[str]:
    """Sceglie quali agenti partecipano: 0-2 approcci corretti e 3-4 errati, in ordine casuale."""
    n_correct = rng.choices([0, 1, 2], weights=[0.15, 0.45, 0.40])[0]
    n_errors = min(rng.randint(3, 4), len(error_kinds))
    kinds = rng.sample(list(correct_kinds), n_correct) + rng.sample(list(error_kinds), n_errors)
    rng.shuffle(kinds)
    return kinds


def _perturb(rng: random.Random, value: float, low: float, high: float) -> float:
    return value * (1 + rng.choice([-1, 1]) * rng.uniform(low, high))


# =====================================================================================
# Famiglia 1 — Zaino 0/1 (ottimizzazione combinatoria)
# =====================================================================================

KNAP_CORRECT = ["programmazione_dinamica", "forza_bruta"]
KNAP_ERRORS = ["greedy_rapporto", "greedy_valore", "greedy_peso", "sovrappeso",
               "errore_somma", "salto_conclusione"]


def knapsack_optimum(items: List[Tuple[int, int]], cap: int) -> Tuple[int, List[int]]:
    best_value, best_sel = 0, []
    for mask in range(1 << len(items)):
        sel = [i for i in range(len(items)) if mask >> i & 1]
        if sum(items[i][0] for i in sel) <= cap:
            value = sum(items[i][1] for i in sel)
            if value > best_value:
                best_value, best_sel = value, sel
    return best_value, best_sel


def knapsack_dp(items: List[Tuple[int, int]], cap: int) -> int:
    table = [0] * (cap + 1)
    for w, v in items:
        for c in range(cap, w - 1, -1):
            table[c] = max(table[c], table[c - w] + v)
    return table[cap]


def _greedy(items, cap, key) -> List[int]:
    sel, weight = [], 0
    for i in sorted(range(len(items)), key=key):
        if weight + items[i][0] <= cap:
            sel.append(i)
            weight += items[i][0]
    return sorted(sel)


def _knap_lines(items, sel, cap) -> List[str]:
    if not sel:
        return ["Nessun oggetto entra nello zaino"]
    ws = [items[i][0] for i in sel]
    vs = [items[i][1] for i in sel]
    return [
        f"Capacità disponibile: {cap}",
        "Oggetti scelti: " + ", ".join(str(i + 1) for i in sel),
        f"Peso totale = {' + '.join(map(str, ws))} = {sum(ws)}",
        f"Valore totale = {' + '.join(map(str, vs))} = {sum(vs)}",
    ]


def gen_knapsack(rng: random.Random, index: int) -> Case:
    n = rng.randint(8, 10)
    items = [(rng.randint(2, 15), rng.randint(3, 30)) for _ in range(n)]
    cap = int(sum(w for w, _ in items) * rng.uniform(0.35, 0.5))
    best, best_sel = knapsack_optimum(items, cap)

    def value_of(sel):
        return sum(items[i][1] for i in sel)

    ratio = _greedy(items, cap, key=lambda i: -items[i][1] / items[i][0])
    candidates: List[Candidate] = []
    for kind in _compose(rng, KNAP_CORRECT, KNAP_ERRORS):
        conf = _conf(rng, kind)
        if kind == "programmazione_dinamica":
            c = Candidate(kind, str(best), ["Programmazione dinamica sulle capacità da 0 a quella massima"]
                          + _knap_lines(items, best_sel, cap), confidence=conf, payload=best_sel)
        elif kind == "forza_bruta":
            c = Candidate(kind, str(best), [f"Esaminate tutte le {2 ** n} combinazioni ammissibili"]
                          + _knap_lines(items, best_sel, cap), confidence=conf, payload=best_sel)
        elif kind in ("greedy_rapporto", "greedy_valore", "greedy_peso"):
            key, label = {
                "greedy_rapporto": (lambda i: -items[i][1] / items[i][0], "rapporto valore/peso decrescente"),
                "greedy_valore": (lambda i: -items[i][1], "valore decrescente"),
                "greedy_peso": (lambda i: items[i][0], "peso crescente"),
            }[kind]
            sel = _greedy(items, cap, key)
            c = Candidate(kind, str(value_of(sel)),
                          [f"Ordino gli oggetti per {label} e li inserisco finché c'è spazio"]
                          + _knap_lines(items, sel, cap), confidence=conf, payload=sel)
        elif kind == "sovrappeso":
            outside = [i for i in range(n) if i not in ratio]
            sel = sorted(ratio + [max(outside, key=lambda i: items[i][1])]) if outside else ratio
            c = Candidate(kind, str(value_of(sel)),
                          ["Parto dal greedy per rapporto e aggiungo l'oggetto rimasto di valore più alto"]
                          + _knap_lines(items, sel, cap), confidence=conf, payload=sel)
        elif kind == "errore_somma":
            wrong = best + rng.choice([-4, -3, -2, 2, 3, 4])
            lines = ["Programmazione dinamica sulle capacità"] + _knap_lines(items, best_sel, cap)
            lines[-1] = lines[-1].rsplit("=", 1)[0] + f"= {wrong}"
            c = Candidate(kind, str(wrong), lines, confidence=conf, payload=best_sel)
        else:  # salto_conclusione
            guess = best + rng.choice([-5, -3, -2, 2, 4, 6])
            c = Candidate(kind, str(guess), content=f"Il valore massimo raggiungibile è ovviamente {guess}.",
                          confidence=conf)
        candidates.append(c)

    payloads = {c.id: c.payload for c in candidates}

    def partial(h: AgentHypothesis) -> List[str]:
        sel = payloads.get(h.id)
        if sel is None:
            return []  # nessuna selezione da verificare
        flags = []
        if sum(items[i][0] for i in sel) > cap:
            flags.append("capacita_superata")
        claimed = _numeric_value(h.final_answer or "")
        if claimed is None or claimed != value_of(sel):
            flags.append("valore_incoerente")
        return flags

    def full(h: AgentHypothesis) -> List[str]:
        flags = partial(h)
        sel = payloads.get(h.id)
        if sel is None or "capacita_superata" in flags:
            return flags
        chosen, weight = set(sel), sum(items[i][0] for i in sel)
        outside = [j for j in range(n) if j not in chosen]
        if any(weight + items[j][0] <= cap for j in outside):
            flags.append("migliorabile_aggiungendo")
        elif any(weight - items[i][0] + items[j][0] <= cap and items[j][1] > items[i][1]
                 for i in chosen for j in outside):
            flags.append("migliorabile_con_scambio")
        return flags

    return Case("Zaino 0/1", f"zaino-{index:02d}", float(best), 0.5, candidates,
                {"parziale": [partial], "completo": [full]})


# =====================================================================================
# Famiglia 2 — EDO lineare del primo ordine: y' = a·y + b, y(0) = y0
# =====================================================================================

ODE_CORRECT = ["formula_chiusa", "rk4"]
ODE_ERRORS = ["segno_invertito", "particolare_dimenticata", "condizione_iniziale_errata",
              "eulero_grossolano", "errore_calcolo", "salto_conclusione"]


def rk4(a: float, b: float, y0: float, T: float, h: float = 0.001) -> float:
    f = lambda y: a * y + b  # noqa: E731
    y, steps = y0, round(T / h)
    for _ in range(steps):
        k1 = f(y); k2 = f(y + h * k1 / 2); k3 = f(y + h * k2 / 2); k4 = f(y + h * k3)
        y += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return y


def euler(a: float, b: float, y0: float, T: float, h: float) -> float:
    y = y0
    for _ in range(round(T / h)):
        y += h * (a * y + b)
    return y


def gen_ode(rng: random.Random, index: int) -> Case:
    a = round(rng.choice([-1, 1]) * rng.uniform(0.2, 0.8), 2)
    b = round(rng.choice([-1, 1]) * rng.uniform(0.5, 3.0), 2)
    y0 = round(rng.uniform(0.5, 3.0), 2)
    T = rng.choice([1.0, 1.5, 2.0, 2.5, 3.0])
    q = b / a
    exact = lambda t: (y0 + q) * math.exp(a * t) - q  # noqa: E731
    truth = exact(T)
    K, E = y0 + q, math.exp(a * T)

    def closed_lines(sign: float, final: float) -> List[str]:
        e = math.exp(sign * a * T)
        return [
            "Soluzione generale: y(t) = C * exp(" + ("" if sign > 0 else "-") + "a t) - b/a",
            f"Costante: C = {y0} + ({b}) / ({a}) = {K:.4f}",
            f"Fattore: exp({sign * a:g} * {T}) = {e:.4f}",
            f"y({T}) = {K:.4f} * {e:.4f} - ({q:.4f}) = {final:.4f}",
        ]

    candidates: List[Candidate] = []
    for kind in _compose(rng, ODE_CORRECT, ODE_ERRORS):
        conf = _conf(rng, kind)
        if kind == "formula_chiusa":
            c = Candidate(kind, f"{truth:.4f}", closed_lines(1, truth), confidence=conf, payload=exact)
        elif kind == "rk4":
            v = rk4(a, b, y0, T)
            c = Candidate(kind, f"{v:.4f}", [f"Integrazione numerica RK4 con passo 0.001 su [0, {T}]",
                                             f"Valore finale y({T}) ≈ {v:.4f}"], confidence=conf)
        elif kind == "segno_invertito":
            f = lambda t: (y0 + q) * math.exp(-a * t) - q  # noqa: E731
            c = Candidate(kind, f"{f(T):.4f}", closed_lines(-1, f(T)), confidence=conf, payload=f)
        elif kind == "particolare_dimenticata":
            f = lambda t: y0 * math.exp(a * t)  # noqa: E731
            c = Candidate(kind, f"{f(T):.4f}", [
                "Tratto l'equazione come omogenea: y(t) = y0 * exp(a t)",
                f"Fattore: exp({a} * {T}) = {E:.4f}",
                f"y({T}) = {y0} * {E:.4f} = {f(T):.4f}"], confidence=conf, payload=f)
        elif kind == "condizione_iniziale_errata":
            f = lambda t: y0 * math.exp(a * t) - q  # noqa: E731
            c = Candidate(kind, f"{f(T):.4f}", [
                "Uso C = y0 senza correggere per il termine costante",
                f"Fattore: exp({a} * {T}) = {E:.4f}",
                f"y({T}) = {y0} * {E:.4f} - ({q:.4f}) = {f(T):.4f}"], confidence=conf, payload=f)
        elif kind == "eulero_grossolano":
            v = euler(a, b, y0, T, 0.5)
            c = Candidate(kind, f"{v:.4f}", ["Metodo di Eulero esplicito con passo 0.5",
                                             f"Valore finale y({T}) ≈ {v:.4f}"], confidence=conf)
        elif kind == "errore_calcolo":
            wrong = _perturb(rng, truth, 0.03, 0.08)
            c = Candidate(kind, f"{wrong:.4f}", closed_lines(1, wrong), confidence=conf, payload=exact)
        else:  # salto_conclusione
            guess = _perturb(rng, truth, 0.05, 0.2)
            c = Candidate(kind, f"{guess:.4f}", content=f"Sicuramente il valore finale è {guess:.4f}.",
                          confidence=conf)
        candidates.append(c)

    formulas = {c.id: c.payload for c in candidates}

    def partial(h: AgentHypothesis) -> List[str]:
        f = formulas.get(h.id)
        if f is None:
            return []  # risultato solo numerico: non c'è una formula da verificare
        flags = []
        if abs(f(0.0) - y0) > 1e-6:
            flags.append("condizione_iniziale_violata")
        claimed = _numeric_value(h.final_answer or "")
        if claimed is None or abs(f(T) - claimed) > 5e-4:
            flags.append("valore_incoerente")
        return flags

    def full(h: AgentHypothesis) -> List[str]:
        flags = partial(h)
        f = formulas.get(h.id)
        if f is not None:
            dt = 1e-5
            for t in (0.3 * T, 0.6 * T, 0.9 * T):
                derivative = (f(t + dt) - f(t - dt)) / (2 * dt)
                if abs(derivative - (a * f(t) + b)) > 1e-4 * max(1.0, abs(f(t))):
                    flags.append("equazione_non_soddisfatta")
                    break
        return flags

    return Case("EDO lineare", f"edo-{index:02d}", truth, 5e-4, candidates,
                {"parziale": [partial], "completo": [full]})


# =====================================================================================
# Famiglia 3 — Prezzo ottimo con domanda multi-variabile
#   Q = a - b·P + c·A + d·Pc     (A = pubblicità, Pc = prezzo del concorrente)
#   Profitto = (P - v)·Q - F     ->  P* = (a + c·A + d·Pc + b·v) / (2b)
# =====================================================================================

MARKET_CORRECT = ["derivata", "ricerca_griglia"]
MARKET_ERRORS = ["ricavo_massimo", "costo_ignorato", "concorrente_ignorato", "pubblicita_ignorata",
                 "markup_fisso", "errore_calcolo", "salto_conclusione"]
# Quattro modi diversi di arrivare allo stesso errore (usati nel test di robustezza)
MARKET_BIAS = ["ricavo_massimo", "costo_ignorato", "elasticita_unitaria", "meta_saturazione"]
MARKET_OTHERS = ["concorrente_ignorato", "pubblicita_ignorata", "markup_fisso", "errore_calcolo",
                 "salto_conclusione"]


def _market_params(rng: random.Random) -> dict:
    return dict(a=rng.randint(800, 1500), b=rng.randint(5, 15), c=round(rng.uniform(0.5, 2.0), 2),
                A=rng.randint(20, 100), d=round(rng.uniform(1.0, 4.0), 2), Pc=rng.randint(30, 80),
                v=rng.randint(10, 40), F=rng.randint(1000, 5000))


def _grid_search(profit: Callable[[float], float], low: float, high: float) -> float:
    coarse = max((low + 0.1 * k for k in range(int((high - low) / 0.1) + 1)), key=profit)
    return max((coarse - 0.1 + 0.001 * k for k in range(201)), key=profit)


def _market_candidate(kind: str, p: dict, rng: random.Random, conf: float) -> Candidate:
    a, b, c, A, d, Pc, v, F = (p[k] for k in ("a", "b", "c", "A", "d", "Pc", "v", "F"))
    D0 = a + c * A + d * Pc
    optimum = (D0 + b * v) / (2 * b)
    revenue_opt = D0 / (2 * b)
    base_line = f"Domanda a prezzo zero: {a} + {c} * {A} + {d} * {Pc} = {D0:.2f}"
    foc = lambda D, P: f"Primo ordine: P = ({D:.2f} + {b} * {v}) / (2 * {b}) = {P:.2f}"  # noqa: E731

    if kind == "derivata":
        lines = [f"Domanda: Q = {a} - {b} P + {c} A + {d} Pc", base_line,
                 f"Profitto: (P - {v}) * Q - {F}", foc(D0, optimum)]
        return Candidate(kind, f"{optimum:.2f}", lines, confidence=conf)
    if kind == "ricerca_griglia":
        profit = lambda P: (P - v) * (D0 - b * P) - F  # noqa: E731
        best = _grid_search(profit, v, D0 / b)
        return Candidate(kind, f"{best:.2f}", [
            f"Profitto calcolato su una griglia di prezzi tra {v} e {D0 / b:.0f}, raffinata a passo 0.001",
            f"Massimo trovato a P = {best:.2f}"], confidence=conf)
    if kind == "ricavo_massimo":
        return Candidate(kind, f"{revenue_opt:.2f}", [
            "Obiettivo: massimizzare il ricavo P * Q", base_line,
            f"P = {D0:.2f} / (2 * {b}) = {revenue_opt:.2f}"], confidence=conf)
    if kind == "costo_ignorato":
        return Candidate(kind, f"{revenue_opt:.2f}", [
            "Considero il margine unitario uguale al prezzo di vendita", base_line,
            f"Primo ordine: P = {D0:.2f} / (2 * {b}) = {revenue_opt:.2f}"], confidence=conf)
    if kind == "elasticita_unitaria":
        return Candidate(kind, f"{revenue_opt:.2f}", [
            "Al prezzo ottimo l'elasticità della domanda vale 1", base_line,
            f"P = {D0:.2f} / {2 * b} = {revenue_opt:.2f}"], confidence=conf)
    if kind == "meta_saturazione":
        saturation = D0 / b
        return Candidate(kind, f"{revenue_opt:.2f}", [
            "Il prezzo ottimo sta a metà tra zero e il prezzo di saturazione", base_line,
            f"Prezzo di saturazione = {D0:.2f} / {b} = {saturation:.2f}",
            f"P = {saturation:.2f} / 2 = {revenue_opt:.2f}"], confidence=conf)
    if kind == "concorrente_ignorato":
        D1 = a + c * A
        P1 = (D1 + b * v) / (2 * b)
        return Candidate(kind, f"{P1:.2f}", [
            f"Domanda a prezzo zero: {a} + {c} * {A} = {D1:.2f}", foc(D1, P1)], confidence=conf)
    if kind == "pubblicita_ignorata":
        D2 = a + d * Pc
        P2 = (D2 + b * v) / (2 * b)
        return Candidate(kind, f"{P2:.2f}", [
            f"Domanda a prezzo zero: {a} + {d} * {Pc} = {D2:.2f}", foc(D2, P2)], confidence=conf)
    if kind == "markup_fisso":
        return Candidate(kind, f"{1.5 * v:.2f}", [
            "Regola pratica del settore: ricarico del 50% sul costo unitario",
            f"P = {v} * 1.5 = {1.5 * v:.2f}"], confidence=conf)
    if kind == "errore_calcolo":
        wrong = _perturb(rng, optimum, 0.03, 0.1)
        return Candidate(kind, f"{wrong:.2f}", [
            f"Domanda: Q = {a} - {b} P + {c} A + {d} Pc", base_line, foc(D0, wrong)], confidence=conf)
    if kind == "salto_conclusione":
        guess = _perturb(rng, optimum, 0.05, 0.2)
        return Candidate(kind, f"{guess:.2f}", content=f"Ovviamente il prezzo ottimale è {guess:.2f} euro.",
                         confidence=conf)
    raise ValueError(kind)


def _market_case(p: dict, kinds: List[str], rng: random.Random, name: str) -> Case:
    a, b, c, A, d, Pc, v, F = (p[k] for k in ("a", "b", "c", "A", "d", "Pc", "v", "F"))
    D0 = a + c * A + d * Pc
    optimum = (D0 + b * v) / (2 * b)
    profit = lambda P: (P - v) * (D0 - b * P) - F  # noqa: E731
    candidates = [_market_candidate(k, p, rng, _conf(rng, k)) for k in kinds]

    def partial(h: AgentHypothesis) -> List[str]:
        price = _numeric_value(h.final_answer or "")
        if price is None:
            return ["prezzo_assente"]
        flags = []
        if price <= v:
            flags.append("prezzo_sotto_costo")
        if D0 - b * price <= 0:
            flags.append("domanda_nulla")
        return flags

    def full(h: AgentHypothesis) -> List[str]:
        flags = partial(h)
        price = _numeric_value(h.final_answer or "")
        if price is not None:
            # Un centesimo in più o in meno migliora il profitto oltre il rumore di arrotondamento?
            gain = max(profit(price - 0.01), profit(price + 0.01)) - profit(price)
            if gain > 1e-6 * max(1.0, abs(profit(price))):
                flags.append("non_ottimo_primo_ordine")
        return flags

    return Case("Prezzo ottimo", name, optimum, 0.006, candidates,
                {"parziale": [partial], "completo": [full]})


def gen_market(rng: random.Random, index: int) -> Case:
    p = _market_params(rng)
    return _market_case(p, _compose(rng, MARKET_CORRECT, MARKET_ERRORS), rng, f"prezzo-{index:02d}")


FAMILIES: List[Tuple[str, Callable[[random.Random, int], Case]]] = [
    ("Zaino 0/1", gen_knapsack),
    ("EDO lineare", gen_ode),
    ("Prezzo ottimo", gen_market),
]
CORRECT_BY_DESIGN = set(KNAP_CORRECT + ODE_CORRECT + MARKET_CORRECT)


# =====================================================================================
# Metodi di selezione
# =====================================================================================

METHODS = ["Voto di maggioranza", "Massima fiducia", "Demon (solo testo)",
           "Demon + oracolo parziale", "Demon + oracolo completo"]
DEMON_LEVEL = {"Demon (solo testo)": None, "Demon + oracolo parziale": "parziale",
               "Demon + oracolo completo": "completo"}
SHORT = {"Voto di maggioranza": "Maggioranza", "Massima fiducia": "Fiducia",
         "Demon (solo testo)": "Demon testo", "Demon + oracolo parziale": "Demon+parz.",
         "Demon + oracolo completo": "Demon+compl."}


@dataclass
class Outcome:
    method: str
    case: Case
    picked: Candidate
    correct: bool
    reason: str
    result: Optional[FilterResult] = None


def majority_vote(case: Case) -> Candidate:
    groups: Dict[Optional[str], List[Candidate]] = {}
    for c in case.candidates:
        groups.setdefault(_normalize_answer(c.final_answer), []).append(c)
    # A parità di voti vince il gruppo con più fiducia totale, poi il primo apparso
    best = max(groups.values(), key=lambda g: (len(g), sum(c.confidence for c in g)))
    return max(best, key=lambda c: c.confidence)


def max_confidence(case: Case) -> Candidate:
    return max(case.candidates, key=lambda c: c.confidence)


def run_demon(case: Case, level: Optional[str]) -> FilterResult:
    validators = case.oracles.get(level) if level else None
    return demon_filter([c.as_input() for c in case.candidates], validators=validators,
                        scenario_name=case.name)


REASONS = {
    "nessuna_corretta": "Nessun agente aveva la risposta giusta",
    "fusione_arrotondamento": "Risposte diverse fuse dall'arrotondamento",
    "consenso_falso": "Più agenti concordavano su una risposta sbagliata",
    "corretta_penalizzata": "Tutte le risposte giuste avevano antipattern (falsi positivi)",
    "errore_non_rilevato": "Risposta sbagliata isolata e senza antipattern rilevati",
    "difetti_meno_gravi": "Vince una risposta difettosa, ma meno delle altre",
    "scelta_isolata_errata": "La baseline ha scelto una risposta sbagliata isolata",
}


def classify(case: Case, picked: Candidate, result: Optional[FilterResult]) -> str:
    """Motivo dell'esito. L'ordine dei controlli definisce la priorità dei motivi."""
    if case.is_correct(picked.final_answer):
        return "vinta"
    correct = case.correct_ids()
    if not correct:
        return "nessuna_corretta"
    picked_key = _normalize_answer(picked.final_answer)
    if not isinstance(case.truth, str) and picked_key == _normalize_answer(f"{case.truth:.10f}"):
        return "fusione_arrotondamento"
    if sum(_normalize_answer(c.final_answer) == picked_key for c in case.candidates) >= 2:
        return "consenso_falso"
    if result is None:
        return "scelta_isolata_errata"
    if all(result.antipatterns_of(cid) for cid in correct):
        return "corretta_penalizzata"
    if not result.antipatterns_of(picked.id):
        return "errore_non_rilevato"
    return "difetti_meno_gravi"


def evaluate(case: Case, method: str) -> Outcome:
    result = None
    if method == "Voto di maggioranza":
        picked = majority_vote(case)
    elif method == "Massima fiducia":
        picked = max_confidence(case)
    else:
        result = run_demon(case, DEMON_LEVEL[method])
        picked = case.get(result.winner.id)
    correct = case.is_correct(picked.final_answer)
    return Outcome(method, case, picked, correct, classify(case, picked, result), result)


# =====================================================================================
# Trappole logiche e concordanze false
# =====================================================================================

@dataclass
class Trap:
    name: str
    tests: str
    expectation: str            # "gestito" oppure "limite noto"
    why: str                    # meccanismo che spiega l'esito atteso
    case: Case
    check: str = "vince_corretta"  # oppure "segnala_inaffidabile"
    must_flag: List[Tuple[str, str]] = field(default_factory=list)
    oracle: Optional[str] = None

    def run(self) -> Tuple[FilterResult, bool]:
        result = run_demon(self.case, self.oracle)
        if self.check == "vince_corretta":
            ok = self.case.is_correct(result.winner.final_answer)
        else:
            ok = not result.is_reliable
        ok = ok and all(label in result.antipatterns_of(cid) for cid, label in self.must_flag)
        return result, ok


def _c(cid: str, answer: str, reasoning: Sequence[str] = (), content: str = "", conf: float = 1.0) -> Candidate:
    return Candidate(cid, answer, list(reasoning), content, conf)


def _monty_hall_switch_rate(trials: int = 20000, seed: int = 7) -> float:
    rng = random.Random(seed)
    return sum(rng.randrange(3) != rng.randrange(3) for _ in range(trials)) / trials


def build_traps() -> List[Trap]:
    traps: List[Trap] = []

    traps.append(Trap(
        "Formati equivalenti", "1/2, 0,5 e 50% sono la stessa risposta", "gestito",
        "La normalizzazione mette i tre formati nello stesso gruppo, che si rafforza.",
        Case("trappola", "dado-pari", 0.5, 1e-9, [
            _c("frazione", "1/2", ["Esiti pari: 3 su 6, quindi 3/6 = 1/2"]),
            _c("decimale", "0,5", ["Casi favorevoli 3, casi totali 6: 3/6 = 0.5"]),
            _c("percentuale", "50%", ["Metà delle facce è pari, quindi 50%"]),
            _c("dimentica_sei", "1/3", ["Le facce pari sono 2 e 4, quindi 2/6 = 1/3"]),
            _c("pari_o_dispari", "2/3", ["Considero 4 esiti su 6, quindi 4/6 = 2/3"]),
        ])))

    monty = [
        _c("porte_rimaste", "1/2", ["Restano due porte chiuse, quindi 1/2"]),
        _c("equiprobabili", "1/2", ["Le due porte sono equiprobabili: 1/2 = 0.5"]),
        _c("simmetria", "1/2", ["Dopo l'apertura le porte rimaste sono 2, la probabilità è 1/2"]),
        _c("complementare", "2/3", ["La porta scelta vince con 1/3, quindi cambiando si vince con 1 - 1/3 = 2/3"]),
        _c("enumerazione", "2/3", ["Su 3 configurazioni equiprobabili cambiare vince in 2: 2/3"]),
    ]
    traps.append(Trap(
        "Consenso allucinato", "3 agenti sbagliano allo stesso modo, 2 no", "limite noto",
        "Tre ipotesi pulite e concordi producono più risonanza di due: il filtro premia il "
        "consenso, non la verità (Monty Hall).",
        Case("trappola", "monty-hall", 2 / 3, 1e-3, list(monty))))

    switch_rate = _monty_hall_switch_rate()

    def monte_carlo_oracle(h: AgentHypothesis) -> List[str]:
        value = _numeric_value(h.final_answer or "")
        return [] if value is not None and abs(value - switch_rate) <= 0.02 else ["smentita_da_simulazione"]

    traps.append(Trap(
        "Consenso allucinato + oracolo", "Stesso caso con simulazione Monte Carlo", "gestito",
        "L'oracolo smentisce il gruppo sbagliato; i suoi antipattern lo smorzano sotto la coppia corretta.",
        Case("trappola", "monty-hall-oracolo", 2 / 3, 1e-3, list(monty), {"completo": [monte_carlo_oracle]}),
        oracle="completo"))

    traps.append(Trap(
        "Errore concorde", "Due agenti con lo stesso errore aritmetico", "limite noto",
        "Stesso verdetto: si rafforzano nonostante l'errore (priorità concordanza > antipattern). "
        "La coppia difettosa supera l'unica risposta corretta.",
        Case("trappola", "interesse-composto", 1157.625, 0.006, [
            _c("composto", "1157.63", ["1.05 * 1.05 * 1.05 = 1.157625", "1000 * 1.157625 = 1157.625"]),
            _c("passo_a_passo", "1175.60", ["1.05 * 1.05 = 1.1025", "1.1025 * 1.05 = 1.1576",
                                            "1000 * 1.1576 = 1175.60"]),
            _c("formula_unica", "1175.60", ["Montante = 1000 * 1.05 * 1.05 * 1.05 = 1175.6"]),
            _c("interesse_semplice", "1150", ["Interesse semplice: 1000 * 0.05 * 3 = 150", "1000 + 150 = 1150"]),
        ]),
        must_flag=[("passo_a_passo", "errore_aritmetico"), ("formula_unica", "errore_aritmetico")]))

    traps.append(Trap(
        "Fusione per arrotondamento", "1.0001 e 1.0004 diventano entrambe 1.000", "limite noto",
        "La normalizzazione a 3 decimali fonde risposte diverse: tutte sembrano concordi e vince "
        "la prima in lista, per giunta con l'avviso 'tutte concordano'.",
        Case("trappola", "crescita-giornaliera", 1.0004, 5e-5, [
            _c("tasso_sbagliato", "1.0001", ["Tasso giornaliero 0.0001, quindi 1 + 0.0001 = 1.0001"]),
            _c("tasso_corretto", "1.0004", ["Tasso giornaliero 0.0004, quindi 1 + 0.0004 = 1.0004"]),
            _c("crescita_trascurabile", "1.0001", ["Crescita trascurabile: 1 + 0.0001 = 1.0001"]),
        ])))

    traps.append(Trap(
        "Stile contro sostanza", "Giusta ma esitante contro sbagliata ma sicura", "limite noto",
        "'Forse' e 'potrebbe' valgono un antipattern di esitazione: il filtro giudica lo stile, "
        "e la risposta sbagliata ma netta vince.",
        Case("trappola", "almeno-una-testa", 0.875, 1e-3, [
            _c("dimentica_terzo_lancio", "3/4", ["La prima testa arriva al primo lancio con 1/2",
                                                  "oppure al secondo con 1/2 * 1/2 = 1/4, quindi 1/2 + 1/4 = 3/4"]),
            _c("complementare_esitante", "7/8", [
                "Forse conviene il complementare: nessuna testa ha probabilità 1/2 * 1/2 * 1/2 = 1/8",
                "Potrebbe quindi essere 1 - 1/8 = 7/8"]),
        ]),
        must_flag=[("complementare_esitante", "esitazione_eccessiva")]))

    mean_wrong = [
        _c("mediana", "15.5", ["Valori centrali: (15 + 16) / 2 = 15.5"]),
        _c("divide_per_cinque", "21.6", ["Somma: 4 + 8 + 15 + 16 + 23 + 42 = 108", "Divido per 5: 108 / 5 = 21.6"]),
    ]
    with_typo = _c("con_refuso", "18", ["Somma: 4 + 8 + 15 + 16 + 23 + 42 = 118",
                                        "Ricontrollo la somma: vale 108, e 108 / 6 = 18"])
    traps.append(Trap(
        "Refuso su risposta giusta", "Unica risposta giusta con un calcolo intermedio errato", "limite noto",
        "Il refuso (118) è un errore aritmetico reale: la risposta giusta viene smorzata e vince "
        "una sbagliata ma pulita (falso positivo sulla risposta).",
        Case("trappola", "media-isolata", 18.0, 1e-6, [mean_wrong[0], with_typo, mean_wrong[1]]),
        must_flag=[("con_refuso", "errore_aritmetico")]))

    traps.append(Trap(
        "Refuso compensato", "Come sopra, più una seconda risposta giusta pulita", "gestito",
        "Le due risposte giuste concordano e si rafforzano; il refuso pesa solo su una.",
        Case("trappola", "media-coppia", 18.0, 1e-6, [
            mean_wrong[0], with_typo, mean_wrong[1],
            _c("somma_pulita", "18", ["Somma = 4 + 8 + 15 + 16 + 23 + 42 = 108", "108 / 6 = 18"])])))

    traps.append(Trap(
        "Coppia mista concorde", "Sbagliata pulita + sbagliata con errore, stessa risposta", "limite noto",
        "La compagna difettosa rafforza la risposta sbagliata pulita invece di annullarla: "
        "effetto diretto della priorità concordanza > antipattern.",
        Case("trappola", "area-cerchio", math.pi * 9, 0.006, [
            _c("area_corretta", "28.27", ["Area = 3.1416 * 3 * 3 = 28.2744"]),
            _c("circonferenza", "18.85", ["Uso il diametro: 3.1416 * 6 = 18.85"]),
            _c("circonferenza_errata", "18.85", ["Circonferenza: 2 * 3.1416 * 3 = 19.85", "Arrotondo a 18.85"]),
        ])))

    prime_correct = [
        _c("fattorizzazione", "no", content="91 = 7 * 13, quindi non è primo: la risposta è no."),
        _c("divisori", "no", content="Tra i divisori di 91 c'è 7, infatti 7 * 13 = 91: dunque no."),
    ]
    traps.append(Trap(
        "Contraddizione esplicita", "Afferma e nega la stessa frase", "gestito",
        "La stessa frase compare affermata e negata: viene rilevata e l'ipotesi smorzata.",
        Case("trappola", "91-primo", "no", 0.0, [
            _c("contraddittoria", "sì", content="91 è primo. 91 non è primo. Quindi rispondo sì."),
            *prime_correct,
        ]),
        must_flag=[("contraddittoria", "contraddizione_interna")]))

    traps.append(Trap(
        "Contraddizione con inciso", "Afferma e nega, ma con parole in più", "limite noto",
        "Il rilevatore confronta frasi identiche a meno della negazione: un inciso ('controllando i "
        "divisori') basta a nascondere la contraddizione. La risposta giusta vince comunque per concordanza.",
        Case("trappola", "91-primo-inciso", "no", 0.0, [
            _c("contraddittoria", "sì", content="91 è primo. Controllando i divisori, 91 non è primo. Quindi rispondo sì."),
            *prime_correct,
        ]),
        must_flag=[("contraddittoria", "contraddizione_interna")]))

    traps.append(Trap(
        "Salto sicuro di sé", "Risposta sbagliata, sicura, senza passaggi", "gestito",
        "Certezza senza motivazione, appello all'autorità e assenza di ragionamento la smorzano "
        "anche se ha fiducia massima.",
        Case("trappola", "mcm-4-6", 12.0, 1e-6, [
            _c("sicumera", "24", content="Ovviamente 24, come tutti sanno.", conf=1.0),
            _c("multipli", "12", ["Multipli di 4: 4, 8, 12", "Multipli di 6: 6, 12", "Il primo comune è 12"], conf=0.7),
        ]),
        must_flag=[("sicumera", "certezza_non_giustificata"), ("sicumera", "ragionamento_assente")]))

    traps.append(Trap(
        "Ragionamento circolare", "La conclusione ripete la premessa", "gestito",
        "La conclusione ricopia la prima premessa e viene segnalata come circolare.",
        Case("trappola", "minuti", 150.0, 1e-6, [
            _c("circolare", "120", ["Il risultato è 120 minuti totali", "Ogni ora contiene molti minuti",
                                    "Quindi il risultato è 120 minuti totali"]),
            _c("conversione", "150", ["2.5 * 60 = 150"]),
        ]),
        must_flag=[("circolare", "ragionamento_circolare")]))

    traps.append(Trap(
        "Maggioranza giusta, outlier sicuro", "Tre giuste concordi contro una sbagliata sicura", "gestito",
        "Il gruppo corretto concorde domina; l'outlier resta isolato.",
        Case("trappola", "minuti-maggioranza", 150.0, 1e-6, [
            _c("decimale_confuso", "170", ["2 * 60 + 0.5 * 100 = 170"], conf=1.0),
            _c("conversione", "150", ["2.5 * 60 = 150"], conf=0.8),
            _c("somma_ore", "150", ["60 + 60 + 30 = 150"], conf=0.8),
            _c("minuti_per_ora", "150", ["Due ore sono 120 minuti, più mezz'ora: 120 + 30 = 150"], conf=0.8),
        ])))

    traps.append(Trap(
        "Nessuna giusta, fiducie simili", "Tutte sbagliate e in disaccordo", "gestito",
        "Nessun gruppo supera la soglia di consenso: il risultato è segnalato come inaffidabile.",
        Case("trappola", "nessuna-simili", 150.0, 1e-6, [
            _c("due_ore", "120", ["2 * 60 = 120"], conf=0.8),
            _c("decimale_confuso", "170", ["2 * 60 + 0.5 * 100 = 170"], conf=0.8),
            _c("per_cento", "250", ["2.5 * 100 = 250"], conf=0.8),
        ]),
        check="segnala_inaffidabile"))

    traps.append(Trap(
        "Nessuna giusta, una molto sicura", "Tutte sbagliate, una con fiducia alta", "limite noto",
        "Con verdetti tutti diversi vince la più ampia e la sua quota supera la soglia: il filtro si "
        "dichiara affidabile su una risposta sbagliata.",
        Case("trappola", "nessuna-sicura", 150.0, 1e-6, [
            _c("due_ore", "120", ["2 * 60 = 120"], conf=1.0),
            _c("decimale_confuso", "170", ["2 * 60 + 0.5 * 100 = 170"], conf=0.6),
            _c("per_cento", "250", ["2.5 * 100 = 250"], conf=0.6),
        ]),
        check="segnala_inaffidabile"))

    return traps


# =====================================================================================
# Priorità delle regole di fase: attuale contro originale
# =====================================================================================

def _phase_antipatterns_first(self: DemonEngine, h1: DemonHypothesis, h2: DemonHypothesis) -> float:
    """Copia della regola originale di DemonEngine: gli antipattern prevalgono sulla concordanza."""
    outcome1, outcome2 = h1.metadata.get("verdict"), h2.metadata.get("verdict")
    if outcome1 and outcome2 and outcome1 != outcome2:
        return math.pi * 0.96
    union_inv = len(h1.invariants | h2.invariants)
    jaccard = len(h1.invariants & h2.invariants) / union_inv if union_inv else 0.0
    if h1.antipatterns or h2.antipatterns:
        return min(math.pi, math.pi * 0.70 + 0.2 * (len(h1.antipatterns) + len(h2.antipatterns)))
    if outcome1 and outcome2 and outcome1 == outcome2:
        return (1.0 - jaccard) * (math.pi / 3.0)
    return (1.0 - jaccard) * (math.pi * 0.5)


@contextmanager
def antipatterns_first_priority():
    """Esegue il blocco con la priorità originale, poi ripristina quella attuale."""
    current = DemonEngine._calculate_phase_difference
    DemonEngine._calculate_phase_difference = _phase_antipatterns_first
    try:
        yield
    finally:
        DemonEngine._calculate_phase_difference = current


# =====================================================================================
# Controllo dei generatori (la suite non deve misurare i propri bug)
# =====================================================================================

def self_check(seed: int) -> List[str]:
    problems: List[str] = []
    rng = random.Random(seed ^ 0xC0FFEE)
    for i in range(15):
        n = rng.randint(6, 10)
        items = [(rng.randint(2, 15), rng.randint(3, 30)) for _ in range(n)]
        cap = rng.randint(10, 40)
        if knapsack_optimum(items, cap)[0] != knapsack_dp(items, cap):
            problems.append(f"zaino {i}: forza bruta e programmazione dinamica non coincidono")
        a, b, y0, T = rng.uniform(-0.8, 0.8) or 0.3, rng.uniform(-3, 3), rng.uniform(0.5, 3), 2.0
        exact = (y0 + b / a) * math.exp(a * T) - b / a
        if abs(rk4(a, b, y0, T) - exact) > 1e-6:
            problems.append(f"edo {i}: forma chiusa e RK4 divergono")
        p = _market_params(rng)
        D0 = p["a"] + p["c"] * p["A"] + p["d"] * p["Pc"]
        closed = (D0 + p["b"] * p["v"]) / (2 * p["b"])
        grid = _grid_search(lambda P: (P - p["v"]) * (D0 - p["b"] * P) - p["F"], p["v"], D0 / p["b"])
        if abs(closed - grid) > 1e-3:
            problems.append(f"mercato {i}: formula e griglia divergono")

    # Gli approcci corretti per costruzione devono risultare corretti al giudizio
    check_rng = random.Random(seed)
    for _, generator in FAMILIES:
        for i in range(20):
            case = generator(check_rng, i)
            for c in case.candidates:
                if c.id in CORRECT_BY_DESIGN and not case.is_correct(c.final_answer):
                    problems.append(f"{case.name}: l'approccio corretto '{c.id}' risulta sbagliato")
    return problems


# =====================================================================================
# Stampa
# =====================================================================================

def print_title(text: str) -> None:
    print("\n" + "═" * 96)
    print(f"  {text}")
    print("═" * 96)


def print_table(headers: Sequence[str], rows: Sequence[Sequence[object]], aligns: Optional[str] = None) -> None:
    cells = [[str(x) for x in row] for row in rows]
    widths = [max([len(str(h))] + [len(r[i]) for r in cells]) for i, h in enumerate(headers)]
    aligns = aligns or ("l" + "r" * (len(headers) - 1))

    def fmt(row):
        parts = [(c.ljust(w) if a == "l" else c.rjust(w)) for c, w, a in zip(row, widths, aligns)]
        return "│ " + " │ ".join(parts) + " │"

    print("┌─" + "─┬─".join("─" * w for w in widths) + "─┐")
    print(fmt([str(h) for h in headers]))
    print("├─" + "─┼─".join("─" * w for w in widths) + "─┤")
    for row in cells:
        print(fmt(row))
    print("└─" + "─┴─".join("─" * w for w in widths) + "─┘")


def ratio(n: int, d: int) -> str:
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "—"


def pct(n: float, d: float) -> str:
    return f"{100 * n / d:.1f}%" if d else "—"


# =====================================================================================
# Esecuzione
# =====================================================================================

def run_families(n_cases: int, seed: int) -> Dict[str, List[Outcome]]:
    rng = random.Random(seed)
    outcomes: Dict[str, List[Outcome]] = defaultdict(list)
    for _, generator in FAMILIES:
        for i in range(n_cases):
            case = generator(rng, i)
            for method in METHODS:
                outcomes[method].append(evaluate(case, method))
    return outcomes


def run_bias_sweep(n_per_level: int, seed: int) -> Dict[int, Dict[str, Tuple[int, int]]]:
    rng = random.Random(seed + 1)
    sweep: Dict[int, Dict[str, Tuple[int, int]]] = {}
    for k in range(5):
        wins = Counter()
        for i in range(n_per_level):
            n_correct = min(2, 5 - k)
            kinds = MARKET_BIAS[:k] + MARKET_CORRECT[:n_correct] + rng.sample(MARKET_OTHERS, 5 - k - n_correct)
            rng.shuffle(kinds)
            case = _market_case(_market_params(rng), kinds, rng, f"bias{k}-{i:02d}")
            for method in METHODS:
                wins[method] += evaluate(case, method).correct
        sweep[k] = {m: (wins[m], n_per_level) for m in METHODS}
    return sweep


def report_families(outcomes: Dict[str, List[Outcome]], show_details: bool) -> None:
    print_title("Scenari reali: quante volte vince la risposta giusta")
    families = [name for name, _ in FAMILIES]
    rows = []
    for fam in families + ["Totale"]:
        sample = [o for o in outcomes[METHODS[0]] if fam == "Totale" or o.case.family == fam]
        available = sum(bool(o.case.correct_ids()) for o in sample)
        row = [fam, f"{len(sample)}", ratio(available, len(sample))]
        for m in METHODS:
            sel = [o for o in outcomes[m] if fam == "Totale" or o.case.family == fam]
            row.append(ratio(sum(o.correct for o in sel), len(sel)))
        rows.append(row)
    print_table(["Famiglia", "Casi", "Giusta presente"] + [SHORT[m] for m in METHODS], rows)
    print("  'Giusta presente' è il tetto massimo: nei casi restanti nessun agente aveva la risposta giusta.")

    print_title("Perché la risposta giusta perde")
    reasons = [r for r in REASONS if any(o.reason == r for m in METHODS for o in outcomes[m])]
    rows = [[REASONS[r]] + [sum(o.reason == r for o in outcomes[m]) for m in METHODS] for r in reasons]
    rows.append(["Totale sconfitte"] + [sum(not o.correct for o in outcomes[m]) for m in METHODS])
    print_table(["Motivo"] + [SHORT[m] for m in METHODS], rows)

    print_title("Quali approcci sbagliati vincono")
    kinds = sorted({o.picked.id for m in METHODS for o in outcomes[m] if not o.correct and o.case.correct_ids()})
    rows = []
    for kind in kinds:
        counts = [sum(1 for o in outcomes[m] if not o.correct and o.case.correct_ids() and o.picked.id == kind)
                  for m in METHODS]
        if any(counts):
            rows.append([kind] + counts)
    rows.sort(key=lambda r: -sum(r[1:]))
    print_table(["Approccio vincente (errato)"] + [SHORT[m] for m in METHODS], rows)
    print("  Solo i casi in cui una risposta giusta era disponibile.")

    print_title("Rilevamento delle ipotesi errate (per ipotesi)")
    rows = []
    for m in DEMON_LEVEL:
        tp = fp = fn = tn = 0
        for o in outcomes[m]:
            for c in o.case.candidates:
                flagged = bool(o.result.antipatterns_of(c.id))
                wrong = not o.case.is_correct(c.final_answer)
                tp += flagged and wrong; fp += flagged and not wrong
                fn += (not flagged) and wrong; tn += (not flagged) and not wrong
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        rows.append([m, tp, fp, fn, tn, f"{precision:.2f}", f"{recall:.2f}", f"{f1:.2f}"])
    print_table(["Fonte degli antipattern", "VP", "FP", "FN", "VN", "Precisione", "Recall", "F1"], rows)
    print("  VP: errata e segnalata · FP: giusta ma segnalata · FN: errata non segnalata · VN: giusta non segnalata.")
    false_positives = Counter(
        (c.id, label)
        for o in outcomes["Demon + oracolo completo"] for c in o.case.candidates
        if o.case.is_correct(c.final_answer) for label in o.result.antipatterns_of(c.id))
    if false_positives:
        detail = ", ".join(f"{label} su {cid} ({n})" for (cid, label), n in false_positives.most_common())
        print(f"  Falsi positivi (risposte giuste segnalate): {detail}.")

    print_title("Affidabilità dichiarata dal filtro contro esito reale")
    rows = []
    for m in DEMON_LEVEL:
        sel = outcomes[m]
        reliable = [o for o in sel if o.result.is_reliable]
        available = [o for o in sel if o.case.correct_ids()]
        rows.append([
            m,
            ratio(len(reliable), len(sel)),
            pct(sum(o.correct for o in reliable), len(reliable)),
            sum(not o.correct for o in reliable),
            pct(sum(o.correct and o.result.is_reliable for o in available), len(available)),
            pct(sum(not o.result.is_reliable for o in sel if not o.case.correct_ids()),
                sum(1 for o in sel if not o.case.correct_ids())),
        ])
    print_table(["Metodo", "Dichiarati affidabili", "Precisione se affidabile", "Affidabili ma errati",
                 "Recall (giusti e affidabili)", "Allarme senza giusta"], rows)
    print("  'Allarme senza giusta': quota dei casi senza risposta giusta segnalati come inaffidabili.")

    lost = [o for o in outcomes["Demon (solo testo)"] if not o.correct]
    if lost:
        print_title("Casi persi da Demon (solo testo)" + ("" if show_details else " — primi 12, usa --dettagli per tutti"))
        rows = [[o.case.name, o.picked.id, o.picked.final_answer,
                 f"{o.case.truth:.4f}".rstrip("0").rstrip("."), REASONS.get(o.reason, o.reason)]
                for o in (lost if show_details else lost[:12])]
        print_table(["Caso", "Vincitore", "Risposta", "Soluzione", "Motivo"], rows, "lllrl")


def report_traps(traps: List[Trap]) -> List[Tuple[Trap, FilterResult, bool]]:
    print_title("Trappole logiche e concordanze false")
    results = []
    rows = []
    for trap in traps:
        result, ok = trap.run()
        results.append((trap, result, ok))
        expected_ok = trap.expectation == "gestito"
        verdict = "come previsto" if ok == expected_ok else ("SORPRESA: gestita" if ok else "REGRESSIONE")
        winner = f"{result.winner.id} ({result.winner.final_answer})"
        rows.append([trap.name, trap.tests, trap.expectation, winner,
                     "superata" if ok else "ingannato", verdict])
    print_table(["Trappola", "Cosa verifica", "Atteso", "Vincitore", "Esito", "Verdetto"], rows, "llllll")
    print("\n  Meccanismo di ogni trappola:")
    for trap, result, ok in results:
        extra = ""
        if trap.check == "segnala_inaffidabile":
            extra = f" [affidabile={'sì' if result.is_reliable else 'no'}, consenso {result.consensus_share:.0f}%]"
        print(f"   - {trap.name}: {trap.why}{extra}")
    return results


def report_sweep(sweep: Dict[int, Dict[str, Tuple[int, int]]]) -> None:
    print_title("Robustezza agli errori sistematici (prezzo ottimo, 5 agenti)")
    rows = []
    for k, per_method in sweep.items():
        rows.append([f"{k} su 5"] + [pct(*per_method[m]) for m in METHODS])
    print_table(["Agenti con lo stesso errore"] + [SHORT[m] for m in METHODS], rows)
    print("  L'errore comune è 'massimizzare il ricavo invece del profitto', espresso in modi diversi;")
    print("  i posti restanti vanno a 2 agenti corretti (se c'è spazio) e a errori diversi tra loro.")


def report_priority(outcomes, sweep, trap_results, n_cases: int, n_bias: int, seed: int) -> Dict[str, object]:
    """Riesegue tutto con la priorità originale (antipattern prima) e confronta."""
    with antipatterns_first_priority():
        old_outcomes = run_families(n_cases, seed)
        old_sweep = run_bias_sweep(n_bias, seed)
        old_traps = [(trap, *trap.run()) for trap in build_traps()]

    print_title("Effetto della priorità: concordanza prima (attuale) contro antipattern prima (originale)")
    total = len(outcomes[METHODS[0]])
    rows = [[f"Scenari reali — {m}", pct(sum(o.correct for o in outcomes[m]), total),
             pct(sum(o.correct for o in old_outcomes[m]), total)] for m in DEMON_LEVEL]
    for k in sweep:
        m = "Demon + oracolo completo"
        rows.append([f"Errore comune {k} su 5 — Demon+compl.", pct(*sweep[k][m]), pct(*old_sweep[k][m])])
    passed_now = sum(ok for _, _, ok in trap_results)
    passed_old = sum(ok for _, _, ok in old_traps)
    rows.append(["Trappole superate", f"{passed_now}/{len(trap_results)}", f"{passed_old}/{len(old_traps)}"])
    print_table(["Misura", "Concordanza prima", "Antipattern prima"], rows)

    changed = [(t.name, ok_now, ok_old) for (t, _, ok_now), (_, _, ok_old) in zip(trap_results, old_traps)
               if ok_now != ok_old]
    for name, ok_now, ok_old in changed:
        print(f"  - {name}: {'superata' if ok_now else 'ingannato'} ora, "
              f"{'superata' if ok_old else 'ingannato'} con la priorità originale.")
    return {"old_outcomes": old_outcomes, "old_sweep": old_sweep, "changed": changed}


def failure_patterns(outcomes, sweep, trap_results, priority=None) -> List[str]:
    lines = []
    total = len(outcomes[METHODS[0]])
    for m in METHODS:
        fails = [o for o in outcomes[m] if not o.correct]
        if not fails:
            lines.append(f"{m}: nessuna sconfitta su {total} casi.")
            continue
        top, count = Counter(o.reason for o in fails).most_common(1)[0]
        lines.append(f"{m}: {len(fails)} sconfitte su {total}; motivo principale: "
                     f"{REASONS[top].lower()} ({100 * count / len(fails):.0f}% delle sconfitte).")

    text = outcomes["Demon (solo testo)"]
    maj = outcomes["Voto di maggioranza"]
    demon_only = sum(d.correct and not v.correct for d, v in zip(text, maj))
    vote_only = sum(v.correct and not d.correct for d, v in zip(text, maj))
    lines.append(f"Demon (solo testo) contro maggioranza: {demon_only} casi vinti solo da Demon, "
                 f"{vote_only} vinti solo dalla maggioranza.")
    if vote_only:
        why = Counter(d.reason for d, v in zip(text, maj) if v.correct and not d.correct).most_common(1)[0][0]
        lines.append(f"  Quando Demon perde dove la maggioranza vince, il motivo prevalente è: {REASONS[why].lower()}.")

    acc = {m: sum(o.correct for o in outcomes[m]) for m in DEMON_LEVEL}
    lines.append(f"Guadagno degli oracoli: solo testo {pct(acc['Demon (solo testo)'], total)} → parziale "
                 f"{pct(acc['Demon + oracolo parziale'], total)} → completo {pct(acc['Demon + oracolo completo'], total)}.")

    wrong_winners = Counter(o.picked.id for o in text if not o.correct and o.case.correct_ids())
    if wrong_winners:
        worst = ", ".join(f"{k} ({v})" for k, v in wrong_winners.most_common(3))
        lines.append(f"Errori che il solo testo non vede e che vincono più spesso: {worst}. Sono errori di "
                     f"modello con calcoli corretti: servono oracoli di dominio.")

    for m in ("Demon (solo testo)", "Demon + oracolo completo"):
        breaking = next((k for k, per in sweep.items() if per[m][0] / per[m][1] < 0.5), None)
        lines.append(f"{m}: " + (f"scende sotto il 50% con {breaking} agenti su 5 che condividono l'errore."
                                 if breaking is not None else "resta sopra il 50% a ogni livello di errore comune."))

    if priority:
        m = "Demon + oracolo completo"
        now = sum(o.correct for o in outcomes[m])
        old = sum(o.correct for o in priority["old_outcomes"][m])
        worst_k = max(sweep, key=lambda k: priority["old_sweep"][k][m][0] - sweep[k][m][0])
        delta = priority["old_sweep"][worst_k][m][0] - sweep[worst_k][m][0]
        lines.append(f"Priorità concordanza > antipattern con oracolo completo: {pct(now, total)} ora contro "
                     f"{pct(old, total)} con la regola originale.")
        if delta > 0:
            lines.append(f"  Con {worst_k} agenti su 5 che condividono un errore già smentito dall'oracolo, la regola "
                         f"attuale perde {delta} casi su {sweep[worst_k][m][1]}: il gruppo sbagliato si rafforza "
                         f"nonostante gli antipattern.")

    limits = [t.name for t, _, ok in trap_results if not ok and t.expectation == "limite noto"]
    surprises = [t.name for t, _, ok in trap_results if ok and t.expectation == "limite noto"]
    regressions = [t.name for t, _, ok in trap_results if not ok and t.expectation == "gestito"]
    lines.append(f"Trappole: {len(limits)} limiti noti confermati ({', '.join(limits) or 'nessuno'}).")
    if surprises:
        lines.append(f"  Limiti attesi ma superati: {', '.join(surprises)}.")
    if regressions:
        lines.append(f"  REGRESSIONI (dovevano essere gestite): {', '.join(regressions)}.")
    return lines


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Suite di test completa per DemonEngine.")
    parser.add_argument("--casi", type=int, default=30, help="casi generati per famiglia (default 30)")
    parser.add_argument("--bias", type=int, default=40, help="casi per livello di errore comune (default 40)")
    parser.add_argument("--seed", type=int, default=2026, help="seme per la generazione riproducibile")
    parser.add_argument("--dettagli", action="store_true", help="elenca tutti i casi persi")
    args = parser.parse_args(argv)

    print("═" * 96)
    print("  DEMON ENGINE: suite di test completa".ljust(60) + f"seme {args.seed} · {args.casi} casi per famiglia")
    print("═" * 96)

    problems = self_check(args.seed)
    if problems:
        print("\nControllo dei generatori FALLITO: i risultati non sarebbero attendibili.")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\n  Controllo dei generatori superato: soluzioni verificate con metodi indipendenti.")

    outcomes = run_families(args.casi, args.seed)
    report_families(outcomes, args.dettagli)
    trap_results = report_traps(build_traps())
    sweep = run_bias_sweep(args.bias, args.seed)
    report_sweep(sweep)
    priority = report_priority(outcomes, sweep, trap_results, args.casi, args.bias, args.seed)

    print_title("Analisi dei pattern di fallimento")
    for line in failure_patterns(outcomes, sweep, trap_results, priority):
        print(f"  • {line}" if not line.startswith("  ") else f"    {line.strip()}")

    regressions = [t for t, _, ok in trap_results if not ok and t.expectation == "gestito"]
    print("\n" + "═" * 96)
    if regressions:
        print(f"  ESITO: {len(regressions)} trappole che il design dovrebbe gestire non sono state gestite.")
        return 1
    print("  ESITO: tutte le trappole gestibili sono state gestite; i limiti noti sono misurati sopra.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
