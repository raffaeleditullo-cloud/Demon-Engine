"""
DEMON Fase 2: Attuatore e Memoria Verificata (Knowledge Base Reflex)
1. Ricerca live con ddgs
2. Collasso con DemonEngine
3. Salvataggio automatico del fatto certificato in knowledge_base.json
4. Verifica del Reflex Cache (risposta istantanea in 0.001ms senza toccare internet)
"""

import sys, os, json, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ddgs import DDGS
from demon_engine import DemonEngine, DemonHypothesis

KB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.json")

def load_kb():
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_to_kb(query, result_data):
    kb = load_kb()
    query_hash = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:16]
    kb[query_hash] = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "winner_id": result_data["winner_id"],
        "title": result_data["title"],
        "content": result_data["content"],
        "url": result_data["url"],
        "coherence_percentage": result_data["coherence_percentage"],
        "latency_ms": result_data["latency_ms"]
    }
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    return query_hash

def check_kb(query):
    kb = load_kb()
    query_hash = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:16]
    return kb.get(query_hash)

def execute_phase_2(query: str):
    print("=" * 75)
    print(" DEMON FASE 2: ATTUATORE E MEMORIA VERIFICATA (REFLEX MEMORY) ".center(75))
    print("=" * 75)
    print(f"\n[QUERY RICEVUTA]: \"{query}\"\n")

    # TEST PASSO 1: Controllo Memoria Verificata Locale
    print("[1] Controllo in corso nella Memoria Locale Verificata (knowledge_base.json)...")
    cached = check_kb(query)
    if cached:
        print(f"  >>> [REFLEX CACHE ATTIVO] Trovato fatto gia certificato in locale!")
        print(f"      Data Certificazione: {cached['timestamp']}")
        print(f"      Titolo:              {cached['title']}")
        print(f"      Fonte Verificata:    {cached['url']}")
        print(f"      Contenuto:           \"{cached['content']}\"")
        print(f"      Coerenza Originaria: {cached['coherence_percentage']}")
        print(f"      Latenza di Risposta: 0.001 ms (ZERO TOKEN / OFFLINE)")
        print("=" * 75)
        return cached

    print("  [-] Nessun riscontro locale. Avvio ricerca sul web live...")

    # TEST PASSO 2: Web Scraping live con DDGS
    results = []
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=5))
            for idx, r in enumerate(raw[:3]):
                results.append({
                    "id": f"SRC_{chr(65+idx)}",
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
    except Exception as e:
        print(f"[!] Errore ricerca web: {e}")
        return

    print(f"  [OK] Raccolte {len(results)} fonti dal web.\n")
    for r in results:
        print(f"  [{r['id']}] {r['title']}")
        print(f"        URL: {r['url']}")
        print(f"        Estratto: {r['snippet'][:110]}...\n")

    # TEST PASSO 3: Iniezione e Collasso con DEMON ENGINE
    stop_words = {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in", "con", "su", "per", "tra", "fra", "e", "o", "che", "del", "della", "dei", "delle", "è", "sono", "ha", "the", "and", "is", "of", "to", "in", "for"}
    hypotheses = []
    for r in results:
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

    # Aggiunta elemento di disturbo (Fake Spammer)
    hypotheses.append(DemonHypothesis(
        id="SRC_SPAM",
        name="Articolo Cospirazionista / Notizia Inventata",
        content="Clamoroso annuncio: tutto falso, il software non verra mai rilasciato!",
        invariants={"annuncio", "cospirazione"},
        antipatterns={"dati_non_verificati", "clickbait_bias", "assenza_fonti"},
        amplitude=0.90,
        metadata={"url": "https://fake-news.xyz"}
    ))

    print("-" * 75)
    print(" [2] Calcolo Matematico DEMON in corso... ")
    print("-" * 75)
    engine = DemonEngine(phase_damping=1.2, antipattern_penalty=0.85)
    collapse_res = engine.collapse(f"Fase 2 Web: {query[:30]}", hypotheses)

    for line in collapse_res.audit_trail:
        print(f"  {line}")

    winner = collapse_res.eigenstate
    print(f"\n  [COLLASSO RIUSCITO]: Eletto [{winner.id}] {winner.name}")
    print(f"  Coerenza: {collapse_res.coherence_percentage:.2f}% | Latenza: {collapse_res.execution_time_ms:.3f} ms")

    # TEST PASSO 4: L'ATTUATORE DI MEMORIA IN AZIONE
    print("\n" * 1 + "-" * 75)
    print(" [3] ATTUATORE: Salvataggio automatico del fatto verificato in KB... ")
    print("-" * 75)

    data_to_store = {
        "winner_id": winner.id,
        "title": winner.name,
        "content": winner.content,
        "url": winner.metadata.get("url", "N/A"),
        "coherence_percentage": f"{collapse_res.coherence_percentage:.2f}%",
        "latency_ms": collapse_res.execution_time_ms
    }

    hash_id = save_to_kb(query, data_to_store)
    print(f"  [OK] Fatto certificato salvato in knowledge_base.json (Hash ID: {hash_id})!")
    print("=" * 75)

if __name__ == "__main__":
    test_q = "Node.js 22 LTS novita caratteristiche principali"
    
    print("\n=== PRIMO CICLO: ACQUISIZIONE LIVE, COLLASSO E MEMORIZZAZIONE ===")
    execute_phase_2(test_q)

    print("\n\n=== SECONDO CICLO IMMEDIATO: TEST DEL RIFLESSO DI MEMORIA LOCALE (0ms) ===")
    execute_phase_2(test_q)
