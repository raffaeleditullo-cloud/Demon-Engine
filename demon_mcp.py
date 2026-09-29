"""
DEMON Phase 5: Model Context Protocol (MCP) Server
Fornisce strumenti di ragionamento quantistico deterministico a bassissima latenza (<0.05ms)
per assistenti AI (Claude, Antigravity, Cursor, Terminal AI) tramite protocollo stdio JSON-RPC.

Strumenti esposti:
1. demon_collapse: Valuta e collassa N ipotesi con penalità antipattern e damping di fase.
2. demon_reflex_lookup: Interroga la memoria verificata locale (0.001ms, 0 token).
3. demon_safe_dispatch: Esegue in sicurezza un'azione OS dopo il vaglio della corte DEMON.
4. demon_web_consensus: Estrae fatti certi da fonti web live neutralizzando fake/spam.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demon_gateway import DemonGateway
from demon_engine import DemonEngine, DemonHypothesis

def create_mcp_response(msg_id, result=None, error=None):
    resp = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        resp["error"] = error
    else:
        resp["result"] = result
    return resp

def main():
    gateway = DemonGateway()
    engine = DemonEngine()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            msg_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "demon-engine-mcp",
                        "version": "2.0.0"
                    }
                }
                sys.stdout.write(json.dumps(create_mcp_response(msg_id, result)) + "\n")
                sys.stdout.flush()

            elif method == "tools/list":
                tools = [
                    {
                        "name": "demon_pipeline",
                        "description": "Esegue la pipeline unificata DEMON (Intento, Reflex Cache, Live Consensus o Safe Dispatcher).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Comando vocale o testuale dell'utente"
                                }
                            },
                            "required": ["command"]
                        }
                    },
                    {
                        "name": "demon_raw_collapse",
                        "description": "Esegue l'equazione di interferenza ondulatoria su un elenco di ipotesi.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "scenario_name": {"type": "string"},
                                "hypotheses": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "amplitude": {"type": "number"},
                                            "antipatterns": {"type": "array", "items": {"type": "string"}},
                                            "invariants": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["id", "name"]
                                    }
                                }
                            },
                            "required": ["scenario_name", "hypotheses"]
                        }
                    }
                ]
                sys.stdout.write(json.dumps(create_mcp_response(msg_id, {"tools": tools})) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                if tool_name == "demon_pipeline":
                    cmd = tool_args.get("command", "")
                    gateway_res = gateway.route_command(cmd)
                    tool_content = [{
                        "type": "text",
                        "text": json.dumps(gateway_res, ensure_ascii=False, indent=2)
                    }]
                    sys.stdout.write(json.dumps(create_mcp_response(msg_id, {"content": tool_content})) + "\n")
                    sys.stdout.flush()

                elif tool_name == "demon_raw_collapse":
                    scenario = tool_args.get("scenario_name", "Custom Scenario")
                    raw_hyps = tool_args.get("hypotheses", [])
                    hyps = []
                    for h in raw_hyps:
                        hyps.append(DemonHypothesis(
                            id=h.get("id"),
                            name=h.get("name"),
                            amplitude=float(h.get("amplitude", 1.0)),
                            antipatterns=set(h.get("antipatterns", [])),
                            invariants=set(h.get("invariants", []))
                        ))
                    res = engine.collapse(scenario, hyps)
                    payload = {
                        "winner_id": res.eigenstate.id,
                        "winner_name": res.eigenstate.name,
                        "coherence_percentage": res.coherence_percentage,
                        "latency_ms": res.execution_time_ms
                    }
                    tool_content = [{
                        "type": "text",
                        "text": json.dumps(payload, ensure_ascii=False, indent=2)
                    }]
                    sys.stdout.write(json.dumps(create_mcp_response(msg_id, {"content": tool_content})) + "\n")
                    sys.stdout.flush()
                else:
                    sys.stdout.write(json.dumps(create_mcp_response(msg_id, error={"code": -32601, "message": "Method not found"})) + "\n")
                    sys.stdout.flush()

        except Exception as e:
            sys.stdout.write(json.dumps(create_mcp_response(None, error={"code": -32603, "message": str(e)})) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
