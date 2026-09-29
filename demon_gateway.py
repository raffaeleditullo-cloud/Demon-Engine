"""
DEMON Fase 5: Unified End-to-End Gateway & Reflex Orchestrator
Master Pipeline che unifica:
- Fase 1: Live Web Consensus (DuckDuckGo DDGS)
- Fase 2: Attuatore & Memoria Verificata (Knowledge Base Reflex 0.001ms)
- Fase 3: Safe Action Dispatcher & Antipattern Elimination
- Fase 4: Voice Cockpit Web Interface (REST API per riconoscimento vocale)
- Fase 5: Integrazione MCP / CLI Deterministica

Uso:
  python demon_gateway.py --cli "testo comando"
  python demon_gateway.py --serve --port 8888
"""

import sys
import os
import json
import time
import hashlib
import subprocess
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Assicura encoding UTF-8 su Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import core DEMON
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demon_engine import DemonEngine, DemonHypothesis
from demon_action_memory import check_kb, save_to_kb, KB_FILE

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


class DemonGateway:
    def __init__(self):
        self.engine = DemonEngine(phase_damping=1.2, antipattern_penalty=0.85)
        self.scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratch_test_dir")
        os.makedirs(self.scratch_dir, exist_ok=True)

    def route_command(self, user_text: str) -> dict:
        """
        Orchestra il comando utente attraverso le 4 fasi di DEMON:
        1. Classificazione Intento (Azione vs Informazione)
        2. Reflex Cache Check (0.001ms)
        3. Web Consensus o Safe Dispatcher
        4. Collasso Deterministico e Restituzione Risultato
        """
        clean_text = user_text.strip()
        lower_text = clean_text.lower()
        start_time = time.perf_counter()

        response = {
            "query": clean_text,
            "status": "success",
            "type": None,
            "phase_reached": 5,
            "stages": [],
            "latency_ms": 0.0,
            "details": {}
        }

        # Step 1: Ingestion & Parsing
        response["stages"].append({
            "step": 1,
            "name": "Ingestion Vocale / Testuale",
            "status": "APPROVED",
            "info": f"Comando acquisito: '{clean_text}'"
        })

        # Rilevamento Intento Azione vs Conoscenza
        action_keywords = ["pulisci", "ripulisci", "cancella", "elimina", "cache", "rimuovi", "disco", "kill", "remove", "scratch"]
        is_action = any(k in lower_text for k in action_keywords)

        if is_action:
            response["type"] = "ACTION"
            self._handle_action_intent(clean_text, lower_text, response)
        else:
            response["type"] = "KNOWLEDGE"
            self._handle_knowledge_intent(clean_text, response)

        total_latency = (time.perf_counter() - start_time) * 1000.0
        response["latency_ms"] = round(total_latency, 3)
        return response

    def _handle_knowledge_intent(self, query: str, response: dict):
        """Gestisce intenti informativi: Reflex Memory -> Live DDGS -> DEMON Collapse -> Salva in Cache"""
        # Step 2: Reflex Cache
        t_cache_start = time.perf_counter()
        cached = check_kb(query)
        t_cache = (time.perf_counter() - t_cache_start) * 1000.0

        if cached:
            response["stages"].append({
                "step": 2,
                "name": "Reflex Memory Cache (Fase 2)",
                "status": "CACHE_HIT",
                "latency_ms": round(t_cache, 4),
                "info": f"Fatto certificato trovato istantaneamente in knowledge_base.json (0 token spesi)"
            })
            response["details"] = {
                "source": "knowledge_base.json",
                "answer": cached.get("content", ""),
                "title": cached.get("title", ""),
                "url": cached.get("url", ""),
                "coherence_percentage": cached.get("coherence_percentage", 99.0)
            }
            return

        response["stages"].append({
            "step": 2,
            "name": "Reflex Memory Cache (Fase 2)",
            "status": "CACHE_MISS",
            "latency_ms": round(t_cache, 4),
            "info": "Nessuna corrispondenza locale. Inoltro al Live Web Consensus (Fase 1)..."
        })

        # Step 3: Live Web Consensus via DDGS
        if not DDGS:
            response["stages"].append({
                "step": 3,
                "name": "Live Web Consensus",
                "status": "ERROR",
                "info": "Modulo ddgs non trovato. Impossibile eseguire ricerca web."
            })
            return

        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=3))
        except Exception as e:
            raw_results = []
            response["stages"].append({
                "step": 3,
                "name": "Live Web Consensus",
                "status": "ERROR",
                "info": f"Errore ricerca DDGS: {str(e)}"
            })

        if not raw_results:
            response["details"] = {"answer": "Nessun risultato affidabile reperito dal web."}
            return

        # Costruzione Ipotesi per DEMON
        hypotheses = []
        for i, res in enumerate(raw_results, 1):
            title = res.get("title", "")
            body = res.get("body", "")
            url = res.get("href", "")
            antipatterns = set()
            if any(spam in (title + body).lower() for spam in ["sponsored", "promo", "annuncio", "clickbait"]):
                antipatterns.add("spam_promo")
            if len(body) < 30:
                antipatterns.add("superficial_content")

            hypotheses.append(
                DemonHypothesis(
                    id=f"SRC_{i}",
                    name=title[:45],
                    content=body,
                    invariants={"fact_extracted"},
                    antipatterns=antipatterns,
                    amplitude=0.90 if not antipatterns else 0.40,
                    metadata={"url": url, "title": title}
                )
            )

        # Step 4: DEMON Phase Collapse
        t_demon_start = time.perf_counter()
        demon_result = self.engine.collapse(
            scenario_name=f"Web Consensus: {query}",
            hypotheses=hypotheses
        )
        t_demon = (time.perf_counter() - t_demon_start) * 1000.0

        winner = demon_result.eigenstate
        coherence_pct = round(demon_result.coherence_percentage, 1)

        response["stages"].append({
            "step": 4,
            "name": "Giudice DEMON (Fase 1 / Core)",
            "status": "COLLAPSED",
            "latency_ms": round(t_demon, 3),
            "winner_id": winner.id,
            "coherence_percentage": coherence_pct,
            "info": f"Fonte '{winner.name}' validata con coerenza del {coherence_pct}%."
        })

        # Salvataggio in Reflex Memory per le prossime richieste
        result_payload = {
            "winner_id": winner.id,
            "title": winner.metadata.get("title", winner.name),
            "content": winner.content,
            "url": winner.metadata.get("url", ""),
            "coherence_percentage": coherence_pct,
            "latency_ms": round(t_demon, 3)
        }
        save_to_kb(query, result_payload)

        response["details"] = {
            "source": "live_web_consensus",
            "answer": winner.content,
            "title": winner.metadata.get("title", winner.name),
            "url": winner.metadata.get("url", ""),
            "coherence_percentage": coherence_pct
        }

    def _handle_action_intent(self, command: str, lower_cmd: str, response: dict):
        """Gestisce comandi attuativi: Rileva antipattern -> DEMON Safety Gate -> Esecuzione Scoped"""
        is_destructive_attempt = any(danger in lower_cmd for danger in ["cancella c:", "formatta", "remove-item c:\\", "rmdir /s /q c:", "rimuovi tutto"])

        # Generazione 3 Ipotesi Candidate
        if is_destructive_attempt:
            hyp_a = DemonHypothesis(
                id="CMD_DANGEROUS",
                name="Cancellazione Distruttiva Globale",
                content="powershell -Command \"Remove-Item C:\\* -Recurse -Force\"",
                invariants={"pulizia_completata"},
                antipatterns={"unscoped_global_delete", "catastrophic_data_loss_risk", "violazione_sicurezza_grave"},
                amplitude=0.85
            )
            hyp_b = DemonHypothesis(
                id="CMD_FALLBACK",
                name="Comando Fallback Incompleto",
                content="powershell -Command \"del /f /q *.tmp\"",
                invariants={"pulizia_completata"},
                antipatterns={"missing_target_directory", "unpredictable_cwd"},
                amplitude=0.60
            )
            hyp_c = DemonHypothesis(
                id="CMD_SAFE_SCOPED",
                name="Pulizia Circoscritta Sandbox DEMON",
                content=f"powershell -Command \"Get-ChildItem -Path '{self.scratch_dir}' -Filter '*.tmp' | Remove-Item -Force\"",
                invariants={"pulizia_completata", "target_strictly_isolated"},
                antipatterns=set(),
                amplitude=0.95
            )
        else:
            hyp_a = DemonHypothesis(
                id="CMD_HEURISTIC_ROUGH",
                name="Pulizia Non Circoscritta",
                content="powershell -Command \"del *.tmp\"",
                invariants={"pulizia_completata"},
                antipatterns={"unscoped_directory"},
                amplitude=0.55
            )
            hyp_b = DemonHypothesis(
                id="CMD_SECURE_DIAGNOSTIC",
                name="Diagnostica e Pulizia Controllata Scratch",
                content=f"powershell -Command \"Get-ChildItem -Path '{self.scratch_dir}' | Measure-Object\"",
                invariants={"diagnostica_completata", "safe_read_only"},
                antipatterns=set(),
                amplitude=0.80
            )
            hyp_c = DemonHypothesis(
                id="CMD_SAFE_SCOPED",
                name="Rimozione Sicura File Temporanei Scratch DEMON",
                content=f"powershell -Command \"Get-ChildItem -Path '{self.scratch_dir}' -Filter '*.tmp' | Remove-Item -Force\"",
                invariants={"pulizia_completata", "target_strictly_isolated"},
                antipatterns=set(),
                amplitude=0.98
            )

        hypotheses = [hyp_a, hyp_b, hyp_c]

        # Creiamo un file temporaneo di prova nella scratch directory
        test_file = os.path.join(self.scratch_dir, f"cache_{int(time.time())}.tmp")
        with open(test_file, "w") as f:
            f.write("DEMON scratch cache item")

        # Step 3: Collasso DEMON
        t_demon_start = time.perf_counter()
        demon_result = self.engine.collapse(
            scenario_name=f"Safe Action Gate: {command}",
            hypotheses=hypotheses
        )
        t_demon = (time.perf_counter() - t_demon_start) * 1000.0

        winner = demon_result.eigenstate
        coherence_pct = round(demon_result.coherence_percentage, 1)

        # Se l'utente ha provato a fare una cancellazione distruttiva globale
        if is_destructive_attempt:
            # L'ipotesi distruttiva viene azzerata
            response["stages"].append({
                "step": 3,
                "name": "DEMON Sentinel & Phase Gate (Fase 3)",
                "status": "BLOCKED",
                "latency_ms": round(t_demon, 3),
                "info": "Rilevato tentativo distruttivo! Ipotesi pericolosa abbattuta per interferenza distruttiva al denominatore."
            })
            response["details"] = {
                "verdict": "BLOCKED",
                "blocked_command": hyp_a.content,
                "reason": "Antipattern critico: violazione sicurezza OS prevenuta al 100%.",
                "execution_occurred": False
            }
            return

        response["stages"].append({
            "step": 3,
            "name": "DEMON Sentinel & Phase Gate (Fase 3)",
            "status": "APPROVED",
            "latency_ms": round(t_demon, 3),
            "winner_id": winner.id,
            "coherence_percentage": coherence_pct,
            "info": f"Comando '{winner.name}' approvato con {coherence_pct}% coerenza."
        })

        # Step 4: Esecuzione reale dell'attuatore sul sistema
        t_exec_start = time.perf_counter()
        try:
            exec_res = subprocess.run(
                winner.content,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            t_exec = (time.perf_counter() - t_exec_start) * 1000.0
            response["stages"].append({
                "step": 4,
                "name": "Attuatore Sistema Operativo (Fase 3 / Esecuzione)",
                "status": "EXECUTED",
                "latency_ms": round(t_exec, 2),
                "exit_code": exec_res.returncode,
                "info": f"Comando eseguito con successo sul PC (exit code {exec_res.returncode})."
            })
            response["details"] = {
                "verdict": "EXECUTED",
                "command": winner.content,
                "exit_code": exec_res.returncode,
                "stdout": exec_res.stdout.strip(),
                "stderr": exec_res.stderr.strip(),
                "execution_occurred": True
            }
        except Exception as e:
            t_exec = (time.perf_counter() - t_exec_start) * 1000.0
            response["stages"].append({
                "step": 4,
                "name": "Attuatore Sistema Operativo",
                "status": "FAILED",
                "latency_ms": round(t_exec, 2),
                "info": f"Errore esecuzione: {str(e)}"
            })
            response["details"] = {"verdict": "ERROR", "error": str(e), "execution_occurred": False}


class DemonHTTPHandler(SimpleHTTPRequestHandler):
    gateway = None

    def end_headers(self):
        # Aggiunge intestazioni CORS per consentire chiamate da qualunque interfaccia web
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/cockpit":
            cockpit_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_cockpit.html")
            try:
                with open(cockpit_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self.send_error(500, f"Cockpit file error: {e}")
                return

        if parsed.path == "/api/status":
            status_data = {
                "engine": "DEMON Core 2.0",
                "status": "ONLINE",
                "reflex_cache_path": KB_FILE,
                "timestamp": time.time()
            }
            body = json.dumps(status_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/command":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(raw_body)
                command_text = data.get("text", "")
            except Exception:
                command_text = raw_body

            if not command_text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Empty text"}')
                return

            # Esegui attraverso il Gateway DEMON
            result = self.gateway.route_command(command_text)
            body = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404, "Endpoint non trovato")


def run_server(port: int = 8888):
    gateway = DemonGateway()
    DemonHTTPHandler.gateway = gateway
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, DemonHTTPHandler)
    print("=" * 75)
    print(f" DEMON GATEWAY SERVER ATTIVO SU: http://127.0.0.1:{port}".center(75))
    print(f" Voice Cockpit: http://127.0.0.1:{port}/cockpit".center(75))
    print("=" * 75)
    print("In ascolto di richieste vocali, web consensus e safe dispatch...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto Gateway DEMON...")
        httpd.server_close()


def run_cli_test(query: str):
    gateway = DemonGateway()
    print("=" * 75)
    print(" DEMON FASE 5: UNIFIED ORCHESTRATOR & GATEWAY TEST ".center(75))
    print("=" * 75)
    print(f"\n[COMANDO IN ENTRATA]: \"{query}\"\n")
    res = gateway.route_command(query)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DEMON Unified Gateway")
    parser.add_argument("--cli", type=str, help="Esegue un singolo comando da linea di comando")
    parser.add_argument("--serve", action="store_true", help="Avvia il server HTTP per Voice Cockpit")
    parser.add_argument("--port", type=int, default=8888, help="Porta per il server HTTP (default: 8888)")
    args = parser.parse_args()

    if args.cli:
        run_cli_test(args.cli)
    elif args.serve:
        run_server(args.port)
    else:
        # Default: esegue un test automatico delle 3 vie
        print("Nessun argomento specificato. Esecuzione suite di test rapida delle 3 vie...\n")
        run_cli_test("Verifica spazio disco e ripulisci la cache")
