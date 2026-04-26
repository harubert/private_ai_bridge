"""
private-ai-bridge MCP-Server

Stellt Claude Code Tools zur Verfügung, die sensible Daten lokal mit
einem LLM (Gemma 4 via Ollama) verarbeiten, ohne dass die Daten je
in die Cloud gelangen.

Tools:
- gemma_query   — Lässt Gemma eine Datei lokal verarbeiten
- pseudonymize  — Erstellt anonymisierte Tokens für sensible Daten
- depseudonymize — Wandelt Tokens zurück in Klartext
- show_mappings — Zeigt aktuelle Pseudonym-Zuordnungen
- audit_log     — Zeigt das Verarbeitungsprotokoll
- system_status — Status von Ollama und Modellen
"""
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from . import gemma_client
from .pseudonymizer import Pseudonymizer, PII_CATEGORIES
from .audit_log import log_event, read_log

mcp = FastMCP("private-ai-bridge", version="1.0.0")
pseudo = Pseudonymizer()


@mcp.tool()
async def gemma_query(file_path: str, task: str, return_format: str = "text") -> str:
    """Lässt das lokale LLM (Gemma 4) eine Datei verarbeiten.

    NUTZE DIESES TOOL, WENN:
    - Eine Datei personenbezogene Daten enthält (Namen, Adressen, Emails)
    - Du die Datei nicht direkt lesen darfst (Permission-Deny)
    - Der User sensible Daten verarbeiten lassen will

    WIE ES FUNKTIONIERT:
    1. Gemma liest die Datei lokal (verlässt nie den Rechner)
    2. Gemma führt die Aufgabe aus
    3. Du bekommst nur das Ergebnis (sollte keine PII enthalten)

    Args:
        file_path: Absoluter Pfad zur Datei
        task: Was Gemma mit den Daten tun soll. Sei explizit:
              "Berechne den Notendurchschnitt pro Klasse, gib KEINE Namen zurück"
        return_format: "text" oder "json" (Hinweis für Gemma)

    Returns:
        Das Ergebnis von Gemma (idealerweise ohne PII)
    """
    path = Path(file_path)
    if not path.exists():
        log_event("gemma_query_failed", {"file": file_path, "reason": "not_found"})
        return f"Fehler: Datei nicht gefunden: {file_path}"

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        log_event("gemma_query_failed", {"file": file_path, "reason": str(e)})
        return f"Fehler beim Lesen: {e}"

    prompt = f"""Du bist ein Datenschutz-Filter. Du erhältst Daten und eine Aufgabe.

WICHTIG:
- Gib NIEMALS personenbezogene Daten zurück (Namen, Emails, Telefonnummern, Adressen)
- Falls Namen erwähnt werden müssen, ersetze sie durch [PERSON_1], [PERSON_2], etc.
- Antworte {'in JSON' if return_format == 'json' else 'in Klartext'}, präzise und knapp

DATEN:
{content}

AUFGABE:
{task}

ANTWORT:"""

    log_event("gemma_query", {"file": file_path, "task": task, "size": len(content)})

    try:
        result = await gemma_client.generate(prompt, temperature=0.3)
    except gemma_client.LocalLLMError as e:
        log_event("gemma_query_failed", {"file": file_path, "reason": str(e)})
        return f"Lokales LLM nicht verfügbar: {e}"

    # Sicherheits-Check: hat Gemma versehentlich PII rausgegeben?
    leaks = pseudo.find_leaked_pii(result)
    if leaks:
        log_event("pii_leak_blocked", {"leaks": [{"value_hash": hash(v), "category": c} for v, c in leaks]})
        return (
            f"BLOCKIERT: Gemmas Antwort enthielt {len(leaks)} bekannte PII. "
            f"Überarbeite die Aufgabe so, dass Gemma keine Klarnamen zurückgibt."
        )

    log_event("gemma_query_success", {"file": file_path, "result_size": len(result)})
    return result


@mcp.tool()
def pseudonymize(text: str, persons: list[str] = None, emails: list[str] = None,
                 phones: list[str] = None, addresses: list[str] = None) -> str:
    """Pseudonymisiert personenbezogene Daten in einem Text.

    Ersetzt echte Werte durch stabile Tokens wie [PERS_a3f2], [EMAIL_b7c1].
    Die Zuordnung wird lokal gespeichert und kann mit depseudonymize wieder
    aufgelöst werden.

    Args:
        text: Der Originaltext
        persons: Liste von Personennamen ("Anna Bauer", "Max Huber", ...)
        emails: Liste von E-Mail-Adressen
        phones: Liste von Telefonnummern
        addresses: Liste von Adressen
    """
    replacements = {}
    if persons: replacements["PERS"] = persons
    if emails: replacements["EMAIL"] = emails
    if phones: replacements["TEL"] = phones
    if addresses: replacements["ADDR"] = addresses

    if not replacements:
        return "Hinweis: Keine Werte zu pseudonymisieren angegeben."

    result = pseudo.pseudonymize_text(text, replacements)
    log_event("pseudonymize", {
        "text_size": len(text),
        "categories": list(replacements.keys()),
        "tokens_in_result": len(pseudo.detect_pii_in(result)),
    })
    return result


@mcp.tool()
def depseudonymize(text: str) -> str:
    """Wandelt Pseudonym-Tokens [PERS_xxx] zurück in Klartext.

    Nutze dieses Tool um Claudes Antwort wieder lesbar zu machen.
    """
    result = pseudo.depseudonymize(text)
    tokens_resolved = len(pseudo.detect_pii_in(text)) - len(pseudo.detect_pii_in(result))
    log_event("depseudonymize", {"text_size": len(text), "tokens_resolved": tokens_resolved})
    return result


@mcp.tool()
def show_mappings() -> str:
    """Zeigt die aktuelle Pseudonym-Zuordnungstabelle."""
    mappings = pseudo.get_mappings()
    if not mappings:
        return "Keine Zuordnungen vorhanden."

    lines = ["Aktuelle Zuordnungen:", ""]
    for category, items in mappings.items():
        cat_label = PII_CATEGORIES.get(category, category)
        lines.append(f"== {category} ({cat_label}) ==")
        for real, token in items.items():
            lines.append(f"  {real:30s} → [{token}]")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def show_audit_log(limit: int = 20) -> str:
    """Zeigt die letzten Einträge aus dem Audit-Log."""
    entries = read_log(limit)
    if not entries:
        return "Audit-Log ist leer."

    lines = [f"Letzte {len(entries)} Einträge:", ""]
    for e in entries:
        ts = e.get("timestamp", "")[:19].replace("T", " ")
        ev = e.get("event", "?")
        details = {k: v for k, v in e.items() if k not in ("timestamp", "event")}
        lines.append(f"{ts}  {ev}  {json.dumps(details, ensure_ascii=False)}")
    return "\n".join(lines)


@mcp.tool()
async def system_status() -> str:
    """Status der lokalen LLM-Infrastruktur."""
    try:
        models = await gemma_client.list_available_models()
        default = gemma_client.DEFAULT_MODEL
        installed = any(default.split(":")[0] in m for m in models)
        return (
            f"Ollama: erreichbar\n"
            f"Default-Modell: {default} ({'installiert' if installed else 'NICHT installiert'})\n"
            f"Verfügbare Modelle:\n" + "\n".join(f"  - {m}" for m in models)
        )
    except gemma_client.LocalLLMError as e:
        return f"Ollama nicht erreichbar: {e}"


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
