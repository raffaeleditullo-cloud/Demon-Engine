"""
Risoluzione Strategica Globale tramite DemonEngine:
Collasso ondulatorio delle 4 ipotesi di mercato per l'architettura Demon.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from demon_engine import DemonEngine, DemonHypothesis, DemonResult

def run_strategic_collapse():
    engine = DemonEngine(phase_damping=1.4, antipattern_penalty=1.0)

    hypotheses = [
        DemonHypothesis(
            id="HYP-A-CHAT-COPY",
            name="Assistente Chat / Copywriting per Email e Marketing",
            content=(
                "POSIZIONAMENTO: Consumer/B2B Chat & Generative Copywriting Tool.\n"
                "FUNZIONAMENTO: Genera N varianti di email o testi promozionali e collassa sulla versione stilisticamente migliore.\n"
                "MERCATO: Competizione diretta con ChatGPT, Jasper, Notion AI, copywriter freelance.\n"
                "TOLLERANZA ALL'ERRORE: Altissima (una bozza imperfetta non produce danni irreversibili).\n"
                "LATENZA RICHIESTA: Umana (1-5 secondi accettabili).\n"
            ),
            invariants={"text_generation"},
            antipatterns={
                "commodity_red_ocean",
                "high_error_tolerance",
                "human_latency_acceptable",
                "trial_and_error_cheap",
                "vanity_application"
            },
            amplitude=0.75,
            metadata={"verdict": "superficial_commodity"}
        ),

        DemonHypothesis(
            id="HYP-B-VSCODE-WRAPPER",
            name="Plugin VS Code / Framework per Agenti di Sviluppo",
            content=(
                "POSIZIONAMENTO: Developer Tooling / IDE Extension / Agentic Framework wrapper.\n"
                "FUNZIONAMENTO: Genera N snippet o refactor e usa l'interferenza per scegliere il commit migliore.\n"
                "MERCATO: Competizione con Cursor, GitHub Copilot, Continue, LangChain, CrewAI.\n"
                "TOLLERANZA ALL'ERRORE: Media (lo sviluppatore o il linter/test eseguono il retry sequenziale senza drammi).\n"
                "LATENZA RICHIESTA: 500ms - 5s.\n"
            ),
            invariants={"code_synthesis", "local_tooling"},
            antipatterns={
                "saturated_dev_market",
                "tolerates_sequential_retries",
                "non_fatal_runtime",
                "wrapper_fragility"
            },
            amplitude=0.85,
            metadata={"verdict": "developer_commodity"}
        ),

        DemonHypothesis(
            id="HYP-C-HFT-QUANT-FINANCE",
            name="High-Frequency Trading (HFT) e Arbitraggio Finanziario",
            content=(
                "POSIZIONAMENTO: Motore decisionale per HFT su mercati azionari e crypto liquidi.\n"
                "FUNZIONAMENTO: Valuta N strategie probabilistiche in book di ordini ad alta frequenza.\n"
                "MERCATO: Fondi quantitativi, market makers proprietari.\n"
                "CRITICITA: I mercati liquidi sono ambienti avversari dominati da execution ASIC/FPGA a nanosecondi su fibra dedicata. "
                "L'interferenza probabilistica non elimina il crollo di liquidità o il front-running fisico e soffre di jitter algoritmico.\n"
            ),
            invariants={"high_speed_execution", "probabilistic_risk"},
            antipatterns={
                "fpga_submicrosecond_mismatch",
                "adversarial_market_regime_shift",
                "liquidity_black_hole_unhedged"
            },
            amplitude=0.88,
            metadata={"verdict": "misaligned_domain"}
        ),

        DemonHypothesis(
            id="HYP-D-SWARM-CRITICAL-SAFETY",
            name="Layer di Coerenza Deterministica & Decisione a Zero Tentativi per Sciami Robotici, Guida Autonoma e Sistemi Critici",
            content=(
                "POSIZIONAMENTO: Real-Time Deterministic Coherence & Instant Decision Engine per Embodied AI & Mission-Critical Swarms.\n"
                "PROBLEMA IRRISOLTO NEL MONDO: Nei sistemi fisici critici (droni in sciame a 80 km/h, robot chirurgici, veicoli autonomi a bivi ciechi, controllo reattori): "
                "IL RETRY SEQUENZIALE E' MORTE. Non esiste il lusso del 'tentativo a vuoto' o del ciclo di riprova da 2 secondi.\n"
                "ARCHITETTURA DEMON:\n"
                "1. Sovrapposizione biologica istantanea: proietta contemporaneamente tutte le traiettorie cinematiche e vettori di sicurezza.\n"
                "2. Interferenza distruttiva istantanea: tutte le traiettorie che violano leggi di conservazione della quantità di moto, quote di sicurezza o prossimità di sciami collassano ad ampiezza zero per opposizione di fase.\n"
                "3. Collasso sull'Eigenstate vincente in <0.05ms: un'unica decisione deterministica, pulita, priva di allucinazioni e priva di tentativi a vuoto.\n"
                "UNILATERALITA': Nessun LLM o rule-engine convenzionale può garantire convergenza istantanea a zero tentativi in ambienti fisici tempo-critici.\n"
            ),
            invariants={
                "zero_retry_physical_necessity",
                "hard_realtime_submillisecond",
                "swarm_distributed_phase_resonance",
                "biological_conservation_laws",
                "mission_critical_eigenstate",
                "unforgiving_physical_consequences",
                "monopoly_of_deterministic_collapse"
            },
            antipatterns=set(),
            amplitude=1.0,
            metadata={"verdict": "unmatched_physical_monopoly"}
        )
    ]

    print("\n" + "#" * 80)
    print(" COLLASSO STRATEGICO GLOBALE: POSIZIONAMENTO DI MERCATO MOTORE DEMON ".center(80))
    print("#" * 80)

    result = engine.collapse("Strategia Globale e Destinazione Industriale Demon", hypotheses)

    print("\n" + "=" * 80)
    print(" TRACCIA AUDIT DEL COLLASSO ONDULATORIO ".center(80, "="))
    print("=" * 80)
    for line in result.audit_trail:
        print(f" {line}")

    print("\n" + "=" * 80)
    print(" MATRICE DI INTERFERENZA STRATEGICA (I_ij) ".center(80, "="))
    print("=" * 80)
    headers = "               " + " ".join([f"{h.id[:10]:>11}" for h in result.hypotheses])
    print(headers)
    for i, row in enumerate(result.interference_matrix):
        row_str = f" {result.hypotheses[i].id[:13]:<13} |"
        for val in row:
            row_str += f" {val:>+11.3f}"
        print(row_str)

    print("\n" + "=" * 80)
    print(" EIGENSTATE STRATEGICO COLLASSATO (IL VERDETTO DEL DEMONE) ".center(80, "="))
    print("=" * 80)
    print(f"  Vincitore Assoluto:     [{result.eigenstate.id}]")
    print(f"  Nome Architettura:      {result.eigenstate.name}")
    print(f"  Grado di Coerenza Netta:{result.coherence_percentage:.2f}%")
    print(f"  Cancellazioni Distruttive: {result.destructive_neutralizations}")
    print(f"  Risonanze Costruttive:     {result.constructive_resonances}")
    print(f"  Tempo di Risoluzione:   {result.execution_time_ms:.2f} ms")

    print("\n  [ANALISI ENERGETICA DEI SINGOLI STATI]")
    for h in result.hypotheses:
        prob = (h.resonance_score / sum(x.resonance_score for x in result.hypotheses)) * 100.0
        status = ">>> DOMINANTE <<<" if h.is_collapsed else "DISTRUTTO/DECOERENTE"
        print(f"   * {h.id:<26} -> Risonanza: {h.resonance_score:8.5f} | Quota di Mercato Spaziale: {prob:5.1f}% [{status}]")

    print("\n" + "=" * 80)
    print(" CONTENUTO DELLA TESI COLLASSATA ".center(80, "="))
    print("=" * 80)
    for line in result.eigenstate.content.strip().split("\n"):
        print(f"   | {line}")

if __name__ == "__main__":
    run_strategic_collapse()
