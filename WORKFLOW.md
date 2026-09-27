# DEMON: Operational Workflow & Decision Framework

Guida operativa standard per l'utilizzo di **DEMON** come middleware di coerenza deterministica per agenti AI, refactoring di codice e decisioni architetturali critiche.

---

## 🔄 Il Flusso Operativo in 4 Fasi

```
           [ PROBLEMA O REQUISITO TECNICO COMPLESSO ]
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 1: MULTI-HYPOTHESIS MAPPING (Diagnostica 3 Vie)        │
│ Costringere l'AI a non dare una risposta singola pigra, ma: │
│ • Ipotesi A (Visione Nominale / Ideale da specifiche)       │
│ • Ipotesi B (Attrito Operativo / Antipattern e Bug reali)   │
│ • Ipotesi C (Evoluzione Resonante / Approccio Ottimo)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 2: DEMON ARBITRATION (Collasso di Fase a 0.05ms)       │
│ Calcolo della matrice in memoria locale:                    │
│ • Invarianti concordanti  --> Risonanza Costruttiva (+cos)  │
│ • Antipattern ed errori   --> Smorzamento al denominatore   │
│ • Elezione dell'Eigenstate dominante con quota di coerenza  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 3: SCOPED EXECUTION (Azione Mirata)                    │
│ L'agente applica chirurgicamente solo l'Eigenstate:         │
│ • Tag Git di rollback preventivo obbligatorio               │
│ • Perimetro ristretto ai soli file target                   │
│ • Divieto assoluto di modifiche fuori scope                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 4: CONTRACTUAL AUDIT (Verifica Empirica)               │
│ • Esecuzione dei test di sistema reali (es. npm test)       │
│ • Audit finale di DEMON per certificare zero regressioni.   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Il Prompt Universale per la Fase 1

Copia e incolla questo prompt nel tuo assistente (Claude, GPT, Gemini) quando affronti un problema complesso:

```text
Ho un problema tecnico/architetturale complesso:
[DESCRIVI QUI IL TUO PROBLEMA O OBIETTIVO]

Non darmi una risposta singola o discorsiva. Genera ESATTAMENTE 3 ipotesi distinte:
- IPOTESI A (Approccio Nominale / Standard): Come si farebbe sulla carta secondo le pratiche comuni.
- IPOTESI B (Attrito e Limiti Reali): Le insidie nascoste, i colli di bottiglia o le assunzioni fragili di questo scenario.
- IPOTESI C (Approccio Resonante / Ottimale): La soluzione robusta che risolve le criticità di B rispettando i vincoli di A.

Per ciascuna ipotesi estrai in formato strutturato:
1. Invariants: Set di 3-4 caratteristiche e garanzie oggettive.
2. Antipatterns: Set di difetti, rischi o violazioni reali (oppure set vuoto se assenti).
3. Initial Amplitude (A_0): Valore tra 0.1 e 1.0.
4. Verdict: Etichetta univoca della strategia.
```

---

## ⚖️ Matrice di Applicabilità: Quando Usare DEMON

DEMON è uno strumento di precisione ad alta affidabilità. Usalo in modo mirato:

| Scenario Operativo | Usare DEMON? | Motivazione Ingegneristica |
| :--- | :---: | :--- |
| **Bug Architetturali Complessi (Async, Memory, Race)** | **SÌ** | Evita tentativi ed errori alla cieca; smorza le soluzioni che causano regressioni. |
| **Decisioni su Database, Contratti e Sicurezza** | **SÌ** | La posta in gioco è alta: spendere più token all'inizio previene perdite catastrofiche. |
| **Routing e Coordinamento tra Agenti / Personas** | **SÌ** | Elimina le ambiguità decisionali in <0.05 ms senza chiamare modelli secondari lenti. |
| **Modifiche Grafiche Minori (Padding, Colori, Typo)** | **NO** | Overhead di token e latenza ingiustificati; procedi con risposta diretta. |
| **Brainstorming Esplorativo Libero** | **NO** | L'interferenza distruttiva eliminerebbe troppe idee eccentriche necessarie all'inizio. |

---

## ⚠️ I 5 Limiti Fondamentali (Regole di Prudenza)

1. **Overhead di Generazione**: Il calcolo di DEMON richiede 0.04 ms, ma l'AI a monte deve generare 3 ipotesi complete (costo token 3x).
2. **Principio GIGO (Garbage In, Garbage Out)**: DEMON valuta solo ciò che gli viene passato. Se un antipattern critico viene omesso dall'input, il motore non può vederlo.
3. **No Falsa Sicurezza**: Un indice di coerenza del 95% certifica la tenuta logica delle premesse, ma la conferma finale spetta sempre ai test contrattuali reali.
4. **Protezione delle Idee Solitarie**: Se una soluzione è geniale ma del tutto isolata, rischia l'opposizione di gruppo al denominatore a meno di un *Human Override* esplicito.
5. **Dipendenza dalla Struttura**: L'algoritmo richiede input strutturato (invarianti e antipattern ben delimitati) per calcolare la differenza di fase $\Delta\phi$.
