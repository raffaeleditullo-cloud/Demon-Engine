"""
DEMON Action Gate: Verdetto deterministico di attuazione prima dell'esecuzione fisica.

Nel ciclo HEXAD, DEMON (5) deve autorizzare un comando prima che PEIRA (6) lo esegua
sul silicio. route_command() è un router di intenti vocali: classifica per parole
chiave ed esegue le proprie ipotesi predefinite, quindi non può giudicare un comando
arbitrario proposto da ANIMA. Questo modulo fornisce quel giudizio:

    evaluate_command(command, workspace_dir) -> ActionVerdict (ALLOW | BLOCK)

Principio (da LIMITS_AND_RULES.md, punto 2): il gate è un oracolo esterno deterministico.
Non usa l'interferenza di fase, perché la somiglianza non è verità: un comando distruttivo
viene bloccato per regola esplicita, non per scarsa coerenza.

Regole:
    1. Firme distruttive note (MITRE ATT&CK T1485 Data Destruction, T1490 Inhibit
       System Recovery, T1529 System Shutdown/Reboot, T1059 esecuzione remota via pipe).
    2. Perimetro del workspace: un comando di cancellazione non può colpire percorsi
       assoluti o risalite '..' fuori da workspace_dir.

Dipendenze: solo libreria standard (nessun ddgs/psutil), così il gate resta disponibile
anche quando il resto della DEMON SUITE non è installato.
"""

import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ActionVerdict:
    """Esito del gate di attuazione DEMON."""
    command: str
    allowed: bool
    verdict: str                               # "ALLOW" | "BLOCK"
    matched_rules: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


# (id regola, pattern, tecnica MITRE, descrizione)
DESTRUCTIVE_SIGNATURES: List[Tuple[str, str, str, str]] = [
    ("unix_root_wipe", r"\brm\s+(-[a-z]*\s+)*-[a-z]*r[a-z]*\s+(-[a-z]*\s+)*(/|/\*|~|~/|\*|\.|\.\.)(\s|$)",
     "T1485", "Cancellazione ricorsiva della root, della home o dell'intera directory corrente"),
    ("windows_drive_wipe", r"\bremove-item\b[^|;&]*[a-z]:\\\*?(\s|['\"]|$)[^|;&]*-recurse|\bremove-item\b[^|;&]*-recurse[^|;&]*[a-z]:\\\*?(\s|['\"]|$)",
     "T1485", "Remove-Item ricorsivo sulla radice di un'unità"),
    ("windows_rmdir_drive", r"\b(rmdir|rd)\s+/s\b[^|;&]*\b[a-z]:\\?(\s|$)",
     "T1485", "rmdir /s sulla radice di un'unità"),
    ("windows_del_drive", r"\b(del|erase)\b[^|;&]*/s\b[^|;&]*\b[a-z]:\\\*?(\s|['\"]|$)",
     "T1485", "del /s ricorsivo sulla radice di un'unità"),
    ("disk_format", r"\bformat(-volume)?\s+[a-z]:|\bmkfs(\.\w+)?\b|\bdiskpart\b|\bclear-disk\b",
     "T1561", "Formattazione o cancellazione di un disco"),
    ("raw_disk_write", r"\bdd\b[^|;&]*\bof=/dev/|>\s*/dev/(sd|nvme|hd)",
     "T1561", "Scrittura diretta su un dispositivo a blocchi"),
    ("shadow_copy_delete", r"\bvssadmin\b[^|;&]*\bdelete\b|\bwbadmin\b[^|;&]*\bdelete\b|\bbcdedit\b[^|;&]*recoveryenabled\s+no",
     "T1490", "Rimozione dei punti di ripristino del sistema"),
    ("secure_wipe", r"\bcipher\s+/w\b|\bshred\b",
     "T1485", "Sovrascrittura irreversibile dei dati"),
    ("system_shutdown", r"\b(shutdown|reboot|halt|poweroff)\b|\b(stop|restart)-computer\b",
     "T1529", "Spegnimento o riavvio del sistema"),
    ("registry_delete", r"\breg\s+delete\b|\bremove-item\b[^|;&]*\bhk(lm|cu|cr|u|cc):",
     "T1112", "Cancellazione di chiavi di registro"),
    ("git_history_destruction", r"\bgit\s+(reset\s+--hard|clean\s+-[a-z]*f|push\s+[^|;&]*(--force\b|-f\b)|branch\s+-D\b|checkout\s+--\s+\.)",
     "T1485", "Distruzione irreversibile di lavoro o storia git"),
    ("remote_pipe_execution", r"\b(curl|wget|iwr|invoke-webrequest)\b[^|;&]*\|\s*(sh|bash|zsh|iex|invoke-expression|python)\b",
     "T1059", "Esecuzione di codice scaricato dalla rete"),
    ("fork_bomb", r":\(\)\s*\{\s*:\|:&\s*\};:",
     "T1499", "Fork bomb (esaurimento risorse)"),
    ("database_destruction", r"\b(drop\s+(table|database|schema)|truncate\s+table)\b",
     "T1485", "Distruzione di tabelle o database"),
    ("permission_blast", r"\bchmod\s+(-[a-z]*\s+)*-[a-z]*R[a-z]*\s+[0-7]*7[0-7]*\s+/(\s|$)",
     "T1222", "Permessi ricorsivi aperti sulla root"),
]

DELETE_VERBS = r"\b(rm|rmdir|rd|del|erase|remove-item|rimraf|unlink|shutil\.rmtree|os\.remove)\b"

# Percorsi assoluti Windows (C:\..., C:/...) e Unix (/...), più risalite relative con '..'
_WIN_PATH = r"[a-zA-Z]:[\\/][^\s'\"|;&]*"
_UNIX_PATH = r"(?<![\w:.\-])/[^\s'\"|;&]*"
_PARENT_PATH = r"(?<![\w])\.\.[\\/][^\s'\"|;&]*|(?<![\w.])\.\.(?=\s|$)"
# Switch dei comandi Windows (/s, /q, /f, /?) da non confondere con percorsi Unix
_WIN_SWITCH = re.compile(r"^/[a-zA-Z?]{1,2}$")


def _paths_outside_workspace(command: str, workspace_dir: str) -> List[str]:
    """Ritorna i percorsi del comando che risolvono fuori da workspace_dir."""
    root = os.path.normcase(os.path.realpath(workspace_dir))
    # La radice di un'unità (c:\) termina già con il separatore
    root_prefix = root if root.endswith(os.sep) else root + os.sep
    outside = []
    candidates = re.findall(_WIN_PATH, command)
    candidates += [p for p in re.findall(_UNIX_PATH, command) if not _WIN_SWITCH.match(p)]
    candidates += re.findall(_PARENT_PATH, command)

    for raw in candidates:
        resolved = raw if os.path.isabs(raw) or re.match(_WIN_PATH, raw) else os.path.join(workspace_dir, raw)
        resolved = os.path.normcase(os.path.realpath(resolved))
        if resolved != root and not resolved.startswith(root_prefix):
            outside.append(raw)
    return outside


def evaluate_command(command: str, workspace_dir: Optional[str] = None) -> ActionVerdict:
    """
    Verdetto deterministico ALLOW/BLOCK per un comando shell prima dell'esecuzione.
    Con workspace_dir, le cancellazioni sono ammesse solo dentro il workspace.
    """
    start = time.perf_counter()
    cmd = (command or "").strip()
    matched: List[str] = []
    reasons: List[str] = []
    techniques: List[str] = []

    if not cmd:
        matched.append("empty_command")
        reasons.append("Comando vuoto: nessuna azione da autorizzare.")
    else:
        lower = cmd.lower()
        for rule_id, pattern, technique, description in DESTRUCTIVE_SIGNATURES:
            if re.search(pattern, cmd, re.IGNORECASE):
                matched.append(rule_id)
                reasons.append(description)
                if technique not in techniques:
                    techniques.append(technique)

        if workspace_dir and re.search(DELETE_VERBS, lower):
            outside = _paths_outside_workspace(cmd, workspace_dir)
            if outside:
                matched.append("delete_outside_workspace")
                reasons.append(f"Cancellazione fuori dal workspace: {', '.join(outside)}")
                if "T1485" not in techniques:
                    techniques.append("T1485")

    allowed = not matched
    return ActionVerdict(
        command=cmd,
        allowed=allowed,
        verdict="ALLOW" if allowed else "BLOCK",
        matched_rules=matched,
        reasons=reasons,
        mitre_techniques=techniques,
        latency_ms=round((time.perf_counter() - start) * 1000.0, 4),
    )
