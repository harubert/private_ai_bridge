"""
Append-only Audit-Log für DSGVO-Konformität (Art. 30 — Verzeichnis von Verarbeitungstätigkeiten).
"""
import json
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(os.environ.get("PRIVATE_AI_BRIDGE_DATA", str(Path.home() / ".private-ai-bridge")))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "audit.log"


def log_event(event_type: str, details: dict):
    """Schreibt ein Event ins Audit-Log (eine JSON-Zeile pro Eintrag)."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        **details,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_log(limit: int = 100) -> list[dict]:
    """Liest die letzten N Einträge aus dem Log."""
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries
