# private-ai-bridge

> **Sensible Daten lokal verarbeiten — Cloud-KI nutzen ohne Datenleck**

Ein Framework für [Claude Code](https://docs.claude.com/en/docs/claude-code), das personenbezogene Daten ausschließlich auf deinem Rechner verarbeitet. Lokales LLM (Gemma 4 via Ollama) bleibt Wächter — Claude bekommt nur anonymisierte Aggregate.

DSGVO-konform. Datenschutz by Design. Open Source.

**Eine technische Veröffentlichung von Thomas Schroffenegger, MSc MAS BEd.**

## Warum?

Cloud-KIs wie Claude sind unschlagbar bei kreativem Schreiben, Analyse und Code. Aber für viele Anwendungsfälle (Schulverwaltung, Personalwesen, Patientendaten) verbietet die DSGVO, personenbezogene Daten an Cloud-Anbieter zu senden.

`private-ai-bridge` löst das: Du bekommst Claudes Sprachstärke, ohne dass auch nur ein Name die Cloud sieht.

## Wie funktioniert es?

```
┌──────┐   ┌──────────────┐   ┌──────────────┐
│ User │ → │ Gemma (lokal) │ → │ Claude (Cloud) │
└──────┘   └──────────────┘   └──────────────┘
              ↑                       ↓
              └─── Re-Mapping ────────┘
```

1. **User** stellt Aufgabe ("Schreibe Zeugnisbemerkungen für alle Schüler")
2. **Claude** erkennt: Datei enthält PII, ruft `gemma_query` Tool auf
3. **Gemma** liest Datei lokal, gibt anonymisierte Daten zurück
4. **Claude** verarbeitet anonymisierte Daten (z.B. schreibt Bemerkungen)
5. **private-ai-bridge** mappt Ergebnis lokal zurück zu echten Namen
6. **User** bekommt finales Ergebnis

Claude sieht nie einen Namen, eine Adresse oder eine E-Mail.

## Quick Start

### Installation

```bash
git clone https://github.com/harubert/private_ai_bridge.git
cd private_ai_bridge
./install.sh
```

Der Installer prüft deine Hardware und installiert das passende Gemma-Modell:
- **8 GB RAM**: gemma:2b (klein, schnell)
- **16 GB RAM**: gemma4:e4b (empfohlen)
- **32 GB RAM**: gemma4:26b (beste Qualität)

### Verwendung

```bash
cd private_ai_bridge
claude
```

Claude Code erkennt die `.mcp.json` automatisch. Sechs neue Tools stehen zur Verfügung:

| Tool | Zweck |
|------|-------|
| `gemma_query` | Lässt Gemma eine Datei lokal verarbeiten |
| `pseudonymize` | Ersetzt echte Werte durch Tokens `[PERS_xxx]` |
| `depseudonymize` | Wandelt Tokens zurück in Klartext |
| `show_mappings` | Zeigt aktuelle Zuordnungstabelle |
| `show_audit_log` | Audit-Log aller Verarbeitungen |
| `system_status` | Status der Ollama-Installation |

## Live-Demo

Eine vollständige Demo mit 7 Schülern und einer realistischen Aufgabe (Wintersportwoche planen) gibt es als interaktive Webseite:

```bash
cd publish && python3 -m http.server 8080
# Browser öffnen: http://localhost:8080
```

Drei Seiten:
- `index.html` — Konzept und Architektur
- `demo.html` — Schritt-für-Schritt-Walkthrough
- `flow.html` — Datenfluss-Visualisierung

## Beispiel-Aufgabe: Wintersportwoche planen

Datei: `examples/schueler/schueler.json` (7 Schüler mit Sportwahl, Allergien, Medikamenten, Sozialermäßigungen)

> **Fiktive Testdaten.** Alle Personen, Adressen, Telefonnummern, Gesundheits- und Familienangaben in `examples/schueler/schueler.json` sind frei erfunden und dienen nur zum Testen. Ähnlichkeiten mit realen Personen sind zufällig. Die E-Mail-Adressen verwenden die dafür reservierte Domain `example.org`.

User-Prompt an Claude:
> "Plane die Wintersportwoche der 3a — Gruppen nach Sportwahl/Niveau, Begleitlehrer, Bus-Sitzplan, Notfall-Datenblätter, individuelle Eltern-Briefe und Förderanträge."

Was passiert:
1. Claude **klassifiziert die Teilaufgaben**: Logistik (Cloud-tauglich) vs. sensible Dokumente (rein lokal)
2. **Logistik** (Gruppen, Bus, Lehrerplan): Claude bekommt von Gemma anonymisierte Profile (nur Sportwahl, Niveau, Größen, Flags wie "allergie_ja_nein")
3. **Notfall-Datenblätter**: Gemma generiert sie komplett lokal mit echten Allergien, Medikamenten, Notfallkontakten — Claude sieht das Dokument nie
4. **Eltern-Briefe**: Claude liefert Template, Gemma füllt lokal mit echten Namen + Sportwahl-spezifischer Packliste
5. **Förderanträge**: Komplett lokal mit Familien-Begründung

**An Cloud gegangen:** 7 anonymisierte Logistik-Profile
**Allergien/Medikamente/Namen in der Cloud:** 0
**Geschätzte Zeitersparnis:** 6-8 Stunden manueller Arbeit

## Sicherheitsstufen

Das Framework klassifiziert Daten in 4 Stufen:

| Stufe | Beispiel | Behandlung |
|-------|----------|------------|
| **L1** | Name, Email, Tel, SVNr, Adresse | Immer pseudonymisieren |
| **L2** | Geburtsdatum, PLZ | Pseudonymisieren in Kombination |
| **L3** | Noten, Bemerkungen | OK ohne Personenzuordnung |
| **L4** | Aggregate (Durchschnitt, Anzahl) | Unbedenklich |

## Architektur

```
private_ai_bridge/
├── server/                  # MCP-Server (Python)
│   ├── mcp_server.py        # Tool-Definitionen
│   ├── gemma_client.py      # Ollama-Wrapper
│   ├── pseudonymizer.py     # Tagged-Token-Mapping
│   └── audit_log.py         # DSGVO Art. 30 Logging
├── examples/                # Beispiel-Daten und Aufgaben
├── publish/                 # Landing Page für eigenen Server (Konzept/Demo/Flow) (Landing/Demo/Flow)
├── .mcp.json                # Claude-Code-Konfiguration
└── install.sh               # Setup mit Hardware-Test
```

## Modell-Austauschbarkeit

Das Framework ist nicht an Gemma gebunden. Setze eine Umgebungsvariable, um andere Ollama-Modelle zu verwenden:

```bash
export PRIVATE_AI_BRIDGE_MODEL="llama3.2:3b"
# oder: mistral:7b, qwen2.5:14b, ...
```

## DSGVO-Konformität

Das Framework unterstützt zentrale DSGVO-Anforderungen:

- **Art. 5 (Datenminimierung):** Cloud bekommt nur die nötigsten Felder
- **Art. 25 (Privacy by Design):** Standardmäßig keine PII in der Cloud
- **Art. 30 (Verzeichnis):** Audit-Log dokumentiert jede Verarbeitung
- **Art. 32 (Sicherheit):** Lokale Lookup-Tabelle, optional verschlüsselt
- **Art. 17 (Löschung):** `clear_mappings` löscht alle Zuordnungen

## Lizenz

Duale Lizenzierung — siehe [LICENSE](LICENSE) für Übersicht.

| Was | Lizenz | Datei |
|-----|--------|-------|
| **Code** (`server/`, `install.sh`, alle `.py`) | MIT | [LICENSE-CODE](LICENSE-CODE) |
| **Dokumentation, Webseite, Konzept** (`README.md`, `publish/`, `examples/`, alle `.md`) | CC BY-SA 4.0 | [LICENSE-DOCS](LICENSE-DOCS) |

**Beide Lizenzen verlangen Namensnennung**:
- MIT: implizit über den Copyright-Hinweis, der in allen Kopien bleiben muss
- CC BY-SA 4.0: explizit, plus Weitergabe unter gleichen Bedingungen (Share-Alike)

## Mitwirken

Issues und Pull Requests willkommen. Insbesondere:
- Adapter für weitere lokale LLMs (llama.cpp, LM Studio, vLLM)
- Verbesserte PII-Erkennung
- Übersetzungen
- Use-Case-Beispiele aus anderen Domänen (Medizin, HR, Recht)

## Inspiration

Entstanden aus dem Bedürfnis, Claude Code in einer österreichischen Mittelschule DSGVO-konform einsetzen zu können. Generalisiert für jeden Anwendungsfall mit sensiblen Daten.

## Autor &amp; Veröffentlichung

**Konzept &amp; Realisierung:** Thomas Schroffenegger, MSc MAS BEd
**Erstveröffentlichung:** April 2026
**Lizenz:** MIT (Code) + CC BY-SA 4.0 (Konzept/Doku) — beide mit Namensnennungspflicht

Bei Verwendung in wissenschaftlichen Arbeiten oder kommerziellen Projekten wird um Namensnennung gebeten:

> Schroffenegger, T. (2026): *private-ai-bridge — DSGVO-konformes Framework für Cloud-KI mit lokaler Datenfilterung.* https://github.com/harubert/private_ai_bridge
