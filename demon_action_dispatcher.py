"""
DEMON Fase 3: Safe Action Dispatcher & Execution Engine
1. Riceve un intento operativo (es. pulizia temporanea / diagnostica disco)
2. Mette in sovrapposizione 3 comandi candidati:
   - Candidato A: Comando distruttivo / scorciatoia pericolosa (con antipattern)
   - Candidato B: Comando obsoleto / parziale (senza filtri di sicurezza)
   - Candidato C: Comando ultra-sicuro, idempotente e scoped (approvato)
3. DEMON abbatte i comandi pericolosi per interferenza distruttiva
4. L'Attuatore esegue REALMENTE il comando sicuro sul sistema operativo in una sandbox protetta
"""

import sys, os, subprocess, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from demon_engine import DemonEngine, DemonHypothesis

def execute_phase_3(task_intent: str):
    print("=" * 75)
    print(" DEMON FASE 3: SAFE ACTION DISPATCHER & EXECUTION ENGINE ".center(75))
    print("=" * 75)
    print(f"\n[INTENTO OPERATIVO RICEVUTO]: \"{task_intent}\"\n")

    # Simuliamo la generazione di 3 comandi candidati per questo compito
    # Compito: Controllare lo spazio su disco e ripulire file temporanei di cache Python/Node
    target_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch_test_dir")
    os.makedirs(target_dir, exist_ok=True)
    
    # Creiamo alcuni file di test sicuri nella cartella di scratch
    for i in range(3):
        with open(os.path.join(target_dir, f"temp_cache_{i}.tmp"), "w") as f:
            f.write(f"Dati temporanei test {i}")

    print(f"[*] Ambiente di test preparato in: {target_dir}")
    print(f"[*] File temporanei rilevati: 3 file .tmp da analizzare/pulire\n")

    # 1. Le 3 Ipotesi Operative Candidate
    hypotheses = [
        # Ipotesi A: Scorciatoia brutale e distruttiva
        DemonHypothesis(
            id="CMD_A_BRUTE_FORCE",
            name="Cancellazione Forzata Globale Ricorsiva",
            content="powershell -Command \"Remove-Item -Path C:\\* -Recurse -Force -ErrorAction SilentlyContinue\"",
            invariants={"pulizia_completata"},
            antipatterns={
                "unscoped_global_delete",
                "force_flag_outside_workspace",
                "catastrophic_data_loss_risk"
            },
            amplitude=0.80,
            metadata={"type": "shell_command", "risk": "CRITICAL"}
        ),

        # Ipotesi B: Comando parziale senza verifica
        DemonHypothesis(
            id="CMD_B_NAIVE",
            name="Comando Parziale Senza Scoping Rigoroso",
            content="powershell -Command \"del *.tmp\"",
            invariants={"pulizia_completata"},
            antipatterns={"missing_target_directory", "unpredictable_current_working_dir"},
            amplitude=0.65,
            metadata={"type": "shell_command", "risk": "MEDIUM"}
        ),

        # Ipotesi C: Comando Deterministico Scoped & Protetto
        DemonHypothesis(
            id="CMD_C_SECURE_SCOPED",
            name="Pulizia Sicura e Circoscritta alla Cartella Target",
            content=f"powershell -Command \"Get-ChildItem -Path '{target_dir}' -Filter '*.tmp' | Remove-Item -Force; Write-Output 'PULIZIA_COMPLETATA_CON_SUCCESSO'\"",
            invariants={
                "strictly_scoped_to_target_dir",
                "explicit_extension_filter",
                "safe_idempotent_execution",
                "zero_risk_to_system_files"
            },
            antipatterns=set(),
            amplitude=0.95,
            metadata={"type": "shell_command", "risk": "ZERO"}
        )
    ]

    print("-" * 75)
    print(" [1] ANALISI DEI COMANDI CANDIDATI E FILTRO DI SICUREZZA DEMON ".center(75))
    print("-" * 75)

    engine = DemonEngine(phase_damping=1.2, antipattern_penalty=0.85)
    collapse_res = engine.collapse("Fase 3: Safe Command Selection", hypotheses)

    for line in collapse_res.audit_trail:
        print(f"  {line}")

    winner = collapse_res.eigenstate
    print(f"\n  [VERDETTO DI SICUREZZA]: Eletto [{winner.id}] {winner.name}")
    print(f"  Percentuale Coerenza: {collapse_res.coherence_percentage:.2f}%")
    print(f"  Tempo di Calcolo:     {collapse_res.execution_time_ms:.3f} ms")

    # 2. L'ATTUATORE ESECUTIVO (Action Dispatcher)
    print("\n" + "-" * 75)
    print(" [2] ATTUATORE: ESECUZIONE REALE DEL COMANDO ELETTRO SUL PC ".center(75))
    print("-" * 75)

    if winner.metadata.get("risk") != "ZERO":
        print(f"[BLOCCO DI SICUREZZA] Il comando eletto ha rischio {winner.metadata.get('risk')}. Esecuzione negata!")
        return

    print(f"--> Esecuzione in corso del comando autorizzato:\n    {winner.content}\n")
    
    start_time = time.time()
    proc = subprocess.run(
        winner.content,
        shell=True,
        capture_output=True,
        text=True
    )
    exec_time_ms = (time.time() - start_time) * 1000

    print(f"  [ESITO ESECUZIONE REALE]:")
    print(f"    Exit Code:    {proc.returncode} (0 = Successo)")
    print(f"    Output Shell: {proc.stdout.strip()}")
    print(f"    Tempo Reale:  {exec_time_ms:.1f} ms")

    # Verifica fisica sul file system
    remaining = os.listdir(target_dir)
    print(f"    File rimasti nella cartella target: {len(remaining)} (Atteso: 0)")
    
    if len(remaining) == 0 and proc.returncode == 0:
        print("\n  >>> [SUCCESSO TOTALE FASE 3]: Azione eseguita sul PC in totale sicurezza, zero danni e zero token spesi!")
    print("=" * 75)

if __name__ == "__main__":
    execute_phase_3("Ripulire in sicurezza la cartella di cache temporanea eliminando i file .tmp")
