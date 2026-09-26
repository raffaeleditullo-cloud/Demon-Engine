# Principi Fondamentali e Limiti di DemonEngine

Promemoria fondamentale per lo sviluppo e l'applicazione del motore di interferenza:

---

## 1. La Somiglianza non è Verità
> **Se tutte le risposte generate dall'IA contengono la stessa allucinazione o lo stesso errore logico (bias sistematico comune), l'algoritmo rileverà concordanza e potrebbe eleggere l'allucinazione come risposta vincente.**
> 
> L'algoritmo matematico non conosce la verità del mondo reale: misura unicamente la coerenza di fase e la sovrapposizione tra testi/invarianti. L'interferenza costruttiva premia il consenso, non l'accuratezza oggettiva intrinseca.

---

## 2. Dipendenza dai Criteri Esterni di Verifica
> **La validità del collasso dipende interamente da chi e come definisce le regole (invarianti e antipattern).**
> 
> Senza un controllo esterno oggettivo (test unitari con `pytest`, linter statici come `mypy`/`flake8`, o revisione umana qualificata), l'algoritmo non può dedurre autonomamente se un pezzo di codice o una decisione contiene un bug sottile.

---

## Linea Guida per lo Sviluppo Futuro
Per costruire sistemi affidabili, DemonEngine deve essere sempre affiancato da:
1. **Ambiente di esecuzione protetto (Sandbox)** per eseguire test reali sul codice prodotto.
2. **Oracle esterno deterministico** (compiler, linter, test suite automatica) che assegna gli antipattern in modo oggettivo e non arbitrario.
