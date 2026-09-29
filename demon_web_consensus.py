"""
DEMON Web Consensus: Fase 1 dello Sciame di Ricerca
Esegue una ricerca web live con DuckDuckGo, estrae 3 fonti e
applica la formula di interferenza di fase di DEMON per isolare la risposta coerente.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from duckduckgo_search import DDGS
from demon_engine import DemonEngine, DemonHypothesis

def run_web_consensus(query: str):
    print("=" * 75)
    print(f" DEMON WEB CONSENSUS: RICERCA E COLLASSO FONTI SUL WEB ".center(75))
    print("=" * 75)
    print(f"\n[QUERY DIGITATA]: \"{query}\"\n")

    # 1. Ricerca sul Web live con DuckDuckGo (ddgs)
    print("--> Interrogazione DuckDuckGo in corso per raccogliere 3 fonti live...")
    results = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=5))
            for idx, r in enumerate(raw_results[:3]):
                results.append({
                    "id": f"FONTE_{chr(65 + idx)}",
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
    except Exception as e:
        print(f"[!] Errore connessione web: {e}")
        return

    if len(results) < 2:
        print("[!] Trovate meno di 2 fonti. Impossibile fare consenso.")
        return

    print(f"[OK] Raccolte {len(results)} fonti dal web con successo!\n")

    # Mostra cosa dicono le fonti
    for r in results:
        print(f"  [{r['id']}] {r['title']}")
        print(f"         URL: {r['url']}")
        print(f"         Snippet: {r['snippet'][:120]}...\n")

    # 2. Modellazione delle Ipotesi per DEMON
    # Estraiamo gli invarianti (parole chiave rilevanti di ciascuno)
    stop_words = {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in", "con", "su", "per", "tra", "fra", "e", "o", "che", "del", "della", "dei", "delle", "al", "alla", "ai", "alle", "è", "sono", "ha", "hanno", "se", "come", "cosa", "perché", "the", "and", "is", "of", "to", "in", "for", "on", "with"}

    hypotheses = []
    for r in results:
        # Estrai parole chiave significative come invarianti
        words = set()
        for token in (r["title"] + " " + r["snippet"]).lower().split():
            clean = "".join(ch for ch in token if ch.isalnum())
            if len(clean) > 3 and clean not in stop_words:
                words.add(clean)

        hypotheses.append(DemonHypothesis(
            id=r["id"],
            name=r["title"][:50],
            content=r["snippet"],
            invariants=words,
            antipatterns=set(),
            amplitude=0.85,
            metadata={"url": r["url"]}
        ))

    # Aggiungiamo un'ipotesi "Fake / Allucinata" di controllo per testare lo smorzamento distruttivo
    fake_hypothesis = DemonHypothesis(
        id="FONTE_FAKE_SPAM",
        name="Articolo Spam / Fake News con Clickbait",
        content="Clamoroso: la risposta non esiste ed è tutta una cospirazione aliena!",
        invariants={"alieni", "clickbait", "complotto"},
        antipatterns={"dati_non_verificati_web", "clickbait_bias", "assenza_fonti_primarie"},
        amplitude=0.90,
        metadata={"url": "https://fake-spam-news.com/hoax"}
    )
    hypotheses.append(fake_hypothesis)

    print("-" * 75)
    print(" AVVIO COLLASSO MATEMATICO CON DEMON ENGINE (Formula di Fase) ".center(75))
    print("-" * 75)

    engine = DemonEngine(phase_damping=1.2, antipattern_penalty=0.85)
    result = engine.collapse(f"Consenso Web: {query[:30]}", hypotheses)

    for line in result.audit_trail:
        print(f"  {line}")

    print("\n" + "=" * 75)
    print(" VERDETTO DI COERENZA FINALE ".center(75))
    print("=" * 75)
    print(f"  EIGENSTATE ELETTO: [{result.eigenstate.id}] {result.eigenstate.name}")
    print(f"  Percentuale di Coerenza: {result.coherence_percentage:.2f}%")
    print(f"  Tempo di Calcolo:        {result.execution_time_ms:.3f} ms")
    print(f"  URL Autentico:           {result.eigenstate.metadata.get('url', 'N/A')}")
    print(f"\n  [ESTRATTO VERIFICATO DAL WEB]:")
    print(f"  \"{result.eigenstate.content}\"")
    print("=" * 75)

if __name__ == "__main__":
    # Test su un fatto oggettivo reale per verificare la convergenza
    test_query = "Python 3.12 nuove funzionalita caratteristiche"
    run_web_consensus(test_query)
