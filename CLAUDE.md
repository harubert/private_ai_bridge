# private-ai-bridge — Hinweise für Claude Code

Dieses Projekt stellt einen MCP-Server bereit, der personenbezogene Daten lokal verarbeitet, bevor sie zur Cloud (zu mir) gelangen.

## Wichtigste Regel

**Wenn du eine Datei mit personenbezogenen Daten (Namen, Adressen, Emails, Telefonnummern) verarbeiten sollst, nutze IMMER zuerst das `gemma_query` Tool.**

Lies solche Dateien NICHT direkt mit `Read`. Stattdessen:

```
gemma_query(
  file_path="<pfad>",
  task="<was Gemma extrahieren soll, OHNE PII zurückzugeben>"
)
```

## Verfügbare Tools (via MCP-Server `private-ai-bridge`)

- `gemma_query(file, task)` — Lokale Verarbeitung mit Gemma
- `pseudonymize(text, persons=[], emails=[], ...)` — Tokens setzen
- `depseudonymize(text)` — Tokens auflösen
- `show_mappings()` — Aktuelle Zuordnungstabelle
- `show_audit_log(limit)` — Audit-Log
- `system_status()` — Ollama-Status

## Beispiel-Workflow

User: "Schreibe Zeugnisbemerkungen für die Schüler in examples/schueler/schueler.json"

Du:
1. Erkenne: schueler.json enthält PII (Namen, Adressen, Email, Tel)
2. Rufe auf: `gemma_query(file_path="examples/schueler/schueler.json", task="Gib für jeden Schüler nur id, geschlecht, noten und bemerkungen zurück. KEINE Namen, Adressen, Emails.")`
3. Mit der anonymisierten Antwort: schreibe individuelle Bemerkungen, referenziere nur über `id`
4. Ausgabe: Liste mit `id` → Bemerkung
5. User mappt lokal über die ID auf die echten Namen

## Was du NIEMALS tun darfst

- Eine Datei mit PII direkt mit `Read` lesen
- Klarnamen aus dem User-Prompt in deine Antwort übernehmen, ohne zu pseudonymisieren
- Tokens wie `[PERS_xxx]` erfinden — diese werden nur vom Pseudonymizer-Tool erzeugt
