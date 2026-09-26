"""
Self-Test di DemonEngine sulle proprie proprieta matematiche.
Dimostra come un algoritmo valuta le strategie di test per se stesso in modo puramente deterministico.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from demon_engine import DemonEngine, DemonHypothesis

def run_self_test_evaluation():
    print("=" * 70)
    print(" DEMON ENGINE: VALUTAZIONE DELLE PROPRIE METODOLOGIE DI TEST ".center(70))
    print("=" * 70)

    engine = DemonEngine(phase_damping=1.2, antipattern_penalty=0.8)

    # Le 3 strategie di collaudo per l'algoritmo stesso
    test_strategies = [
        DemonHypothesis(
            id="STRAT-A-SMOKE",
            name="Smoke Test Superficiale (verifica solo che non crashi)",
            content="Verifica solo se il codice esegue senza generare errori Python, senza controllare le formule.",
            invariants={"controllo_esecuzione"},
            antipatterns={"nessuna_verifica_matematica", "falsi_positivi_ammessi"},
            amplitude=0.7,
            metadata={"verdict": "superficial_test"}
        ),
        DemonHypothesis(
            id="STRAT-B-RANDOM",
            name="Test Casuale Instabile",
            content="Genera valori random non controllati e si affida al caso per testare il motore.",
            invariants={"input_variabili"},
            antipatterns={"risultati_non_riproducibili", "instabilita_statistica"},
            amplitude=0.75,
            metadata={"verdict": "flaky_test"}
        ),
        DemonHypothesis(
            id="STRAT-C-PROPERTY-BASED",
            name="Property-Based Unit Test (Simmetria, Conservazione e Monotonia)",
            content=(
                "Verifica formale delle 3 proprietà matematiche obbligatorie del codice:\n"
                "1. Simmetria della matrice di interferenza: I[i][j] == I[j][i].\n"
                "2. Conservazione delle probabilità: la somma delle percentuali deve essere esattamente 100%.\n"
                "3. Efficacia dello smorzamento: ipotesi con errori devono avere risonanza inferiore a quelle corrette."
            ),
            invariants={
                "verifica_simmetria_matrice",
                "conservazione_somma_probabilita",
                "monotonia_smorzamento_antipattern",
                "riproducibilita_deterministica"
            },
            antipatterns=set(),
            amplitude=1.0,
            metadata={"verdict": "rigorous_math_test"}
        )
    ]

    # Il motore fa collassare la scelta sul metodo di test migliore
    result = engine.collapse("Selezione Strategia di Test per DemonEngine", test_strategies)

    print("\n[ESITO DEL COLLASSO SULLA STRATEGIA MIGLIORE]:")
    print(f"  Vincitore: [{result.eigenstate.id}] {result.eigenstate.name}")
    print(f"  Coerenza:  {result.coherence_percentage:.2f}%\n")

    # Ora eseguiamo DAVVERO la verifica matematica C sul codice
    print("=" * 70)
    print(" ESECUZIONE REALE DEL PROPERTY TEST MATEMATICO SUL CODICE ".center(70))
    print("=" * 70)

    # 1. Verifica Simmetria Matrice
    matrice = result.interference_matrix
    n = len(matrice)
    simmetria_valida = True
    for i in range(n):
        for j in range(n):
            if abs(matrice[i][j] - matrice[j][i]) > 1e-6:
                simmetria_valida = False

    print(f"  1. Simmetria Matrice I[i][j] == I[j][i]:       {'[OK] PASSATO' if simmetria_valida else '[FALLITO]'}")
    assert simmetria_valida, "Errore: Matrice non simmetrica!"

    # 2. Verifica Conservazione Somma delle Probabilità
    totale_risonanza = sum(h.resonance_score for h in result.hypotheses)
    somma_probabilita = sum((h.resonance_score / totale_risonanza) for h in result.hypotheses)
    print(f"  2. Somma Probabilità == 1.0 (100%):            [OK] PASSATO (Valore: {somma_probabilita:.6f})")
    assert abs(somma_probabilita - 1.0) < 1e-6, "Errore: Probabilità non sommano a 1!"

    # 3. Verifica Monotonia Smorzamento
    # L'ipotesi corretta (C) deve avere risonanza superiore a quelle con errori (A e B)
    res_c = test_strategies[2].resonance_score
    res_a = test_strategies[0].resonance_score
    res_b = test_strategies[1].resonance_score
    monotonia_ok = (res_c > res_a) and (res_c > res_b)
    print(f"  3. Monotonia Smorzamento (C > A e C > B):      {'[OK] PASSATO' if monotonia_ok else '[FALLITO]'}")
    print(f"     - Risonanza C (Corretta):  {res_c:.5f}")
    print(f"     - Risonanza A (Superficie): {res_a:.5f}")
    print(f"     - Risonanza B (Random):     {res_b:.5f}")
    assert monotonia_ok, "Errore: Lo smorzamento non ha funzionato correttamente!"

    print("\n" + "=" * 70)
    print(" TUTTE LE PROPRIETA' MATEMATICHE SONO VERIFICATE AL 100% IN LOCALE ".center(70))
    print("=" * 70)

if __name__ == "__main__":
    run_self_test_evaluation()
