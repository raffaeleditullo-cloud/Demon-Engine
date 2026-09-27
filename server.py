"""
Server Flask minimale per DemonEngine.

Espone:
- GET  /         -> dashboard.html
- POST /analyze  -> collasso di uno scenario tramite DemonEngine

Payload di esempio per /analyze:
{
    "scenario_name": "Posizionamento di mercato",
    "phase_damping": 1.4,            # opzionale (gamma)
    "antipattern_penalty": 1.0,      # opzionale (beta)
    "hypotheses": [
        {"id": "A", "name": "Chat & copywriting", "antipatterns": 5,
         "amplitude": 0.75, "verdict": "commodity", "invariants": ["text_generation"]},
        ...
    ]
}

Avvio: python server.py  (porta 5000)
"""

from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory

from demon_engine import DemonEngine, DemonHypothesis

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)


class PayloadError(ValueError):
    pass


@app.after_request
def add_cors_headers(response):
    # Consente di aprire dashboard.html anche direttamente da file:// o da un'altra porta
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def _parse_float(raw: Any, field_name: str, default: float, low: float, high: float) -> float:
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise PayloadError(f"'{field_name}' deve essere un numero.")
    if not (low < value <= high):
        raise PayloadError(f"'{field_name}' deve essere compreso tra {low} (escluso) e {high}.")
    return value


def _parse_hypotheses(items: Any) -> List[DemonHypothesis]:
    if not isinstance(items, list) or len(items) < 2:
        raise PayloadError("Servono almeno 2 ipotesi in 'hypotheses'.")

    hypotheses: List[DemonHypothesis] = []
    seen_ids = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise PayloadError(f"L'ipotesi {index} non è un oggetto JSON.")

        name = str(item.get("name", "")).strip()
        if not name:
            raise PayloadError(f"L'ipotesi {index} non ha un nome.")

        hyp_id = str(item.get("id") or f"H{index}").strip()
        if hyp_id in seen_ids:
            raise PayloadError(f"ID duplicato: '{hyp_id}'.")
        seen_ids.add(hyp_id)

        raw_ap = item.get("antipatterns", 0)
        if isinstance(raw_ap, bool) or not isinstance(raw_ap, (int, float, str)):
            raise PayloadError(f"Antipattern dell'ipotesi {index}: serve un numero intero.")
        try:
            ap_count = int(raw_ap)
        except ValueError:
            raise PayloadError(f"Antipattern dell'ipotesi {index}: serve un numero intero.")
        if ap_count < 0 or ap_count > 50 or ap_count != float(raw_ap):
            raise PayloadError(f"Antipattern dell'ipotesi {index}: intero tra 0 e 50.")

        amplitude = _parse_float(item.get("amplitude"), f"amplitude (ipotesi {index})", 1.0, 0.0, 1.0)

        # Senza verdetto esplicito ogni ipotesi forma un gruppo a sé (come negli script strategici)
        verdict = str(item.get("verdict") or "").strip() or f"verdict_{hyp_id}"

        raw_inv = item.get("invariants") or []
        if isinstance(raw_inv, str):
            raw_inv = raw_inv.split(",")
        invariants = {str(v).strip() for v in raw_inv if str(v).strip()}

        hypotheses.append(
            DemonHypothesis(
                id=hyp_id,
                name=name,
                content=str(item.get("content", "")),
                invariants=invariants,
                # Il motore usa solo la cardinalità degli antipattern: bastano etichette sintetiche
                antipatterns={f"{hyp_id}_antipattern_{k + 1}" for k in range(ap_count)},
                amplitude=amplitude,
                metadata={"verdict": verdict},
            )
        )
    return hypotheses


@app.get("/")
def dashboard():
    return send_from_directory(BASE_DIR, "dashboard.html")


@app.get("/logo.png")
def logo():
    return send_from_directory(BASE_DIR, "logo.png")


@app.post("/analyze")
def analyze():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    try:
        scenario_name = str(payload.get("scenario_name", "")).strip() or "Scenario senza nome"
        engine = DemonEngine(
            phase_damping=_parse_float(payload.get("phase_damping"), "phase_damping", 1.4, 0.0, 10.0),
            antipattern_penalty=_parse_float(
                payload.get("antipattern_penalty"), "antipattern_penalty", 1.0, 0.0, 10.0
            ),
        )
        hypotheses = _parse_hypotheses(payload.get("hypotheses"))
    except PayloadError as exc:
        return jsonify({"error": str(exc)}), 400

    result = engine.collapse(scenario_name, hypotheses)
    total = sum(h.resonance_score for h in result.hypotheses)

    return jsonify(
        {
            "scenario_name": result.scenario_name,
            "eigenstate": {"id": result.eigenstate.id, "name": result.eigenstate.name},
            "coherence_percentage": result.coherence_percentage,
            "constructive_resonances": result.constructive_resonances,
            "destructive_neutralizations": result.destructive_neutralizations,
            "execution_time_ms": result.execution_time_ms,
            "interference_matrix": result.interference_matrix,
            "hypotheses": [
                {
                    "id": h.id,
                    "name": h.name,
                    "amplitude": h.amplitude,
                    "antipatterns": len(h.antipatterns),
                    "verdict": h.metadata.get("verdict"),
                    "resonance": h.resonance_score,
                    "probability": (h.resonance_score / total * 100.0) if total > 0 else 0.0,
                    "is_eigenstate": h.is_collapsed,
                }
                for h in result.hypotheses
            ],
            "audit_trail": result.audit_trail,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
