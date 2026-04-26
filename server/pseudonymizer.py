"""
Deterministische Pseudonymisierung mit lokaler Lookup-Tabelle.
Tagged Tokens: [PERS_a3f2], [EMAIL_b7c1], [TEL_d9e4], etc.
"""
import json
import hashlib
import re
import os
from pathlib import Path

# Speicherort für die Lookup-Tabelle
LOOKUP_DIR = Path(os.environ.get("PRIVATE_AI_BRIDGE_DATA", str(Path.home() / ".private-ai-bridge")))
LOOKUP_DIR.mkdir(parents=True, exist_ok=True)
LOOKUP_FILE = LOOKUP_DIR / "lookup.json"

# Sicherheitsstufen
PII_CATEGORIES = {
    "PERS": "Vor- und Nachname",
    "EMAIL": "E-Mail-Adresse",
    "TEL": "Telefonnummer",
    "ADDR": "Postadresse",
    "SVNR": "Sozialversicherungsnummer",
    "GEB": "Geburtsdatum",
    "ORT": "Wohnort",
}


class Pseudonymizer:
    def __init__(self):
        self.forward: dict[str, dict[str, str]] = {}  # {"PERS": {"Anna Bauer": "PERS_a3f2"}}
        self.reverse: dict[str, str] = {}  # {"PERS_a3f2": "Anna Bauer"}
        self._load()

    def _load(self):
        if LOOKUP_FILE.exists():
            data = json.loads(LOOKUP_FILE.read_text(encoding="utf-8"))
            self.forward = data.get("forward", {})
            self.reverse = data.get("reverse", {})

    def _save(self):
        LOOKUP_FILE.write_text(
            json.dumps({"forward": self.forward, "reverse": self.reverse}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _generate_id(self, category: str, value: str) -> str:
        """Erzeugt eine stabile, kurze ID für einen Wert."""
        h = hashlib.sha256(f"{category}:{value}".encode("utf-8")).hexdigest()
        return f"{category}_{h[:6]}"

    def pseudonymize(self, category: str, value: str) -> str:
        """Gibt das Pseudonym-Token für einen Wert zurück (erzeugt es bei Bedarf)."""
        category = category.upper()
        if category not in self.forward:
            self.forward[category] = {}

        if value in self.forward[category]:
            return f"[{self.forward[category][value]}]"

        token = self._generate_id(category, value)
        self.forward[category][value] = token
        self.reverse[token] = value
        self._save()
        return f"[{token}]"

    def depseudonymize(self, text: str) -> str:
        """Ersetzt alle [TOKEN]s im Text durch ihre Klartextwerte."""
        def replace(match):
            token = match.group(1)
            return self.reverse.get(token, match.group(0))

        return re.sub(r"\[([A-Z]+_[a-f0-9]{6})\]", replace, text)

    def pseudonymize_text(self, text: str, replacements: dict[str, list[str]]) -> str:
        """Ersetzt alle bekannten Klartextwerte in einem Text durch Tokens."""
        result = text
        # Längste zuerst (vermeidet Teilstring-Probleme)
        for category, values in replacements.items():
            for value in sorted(values, key=len, reverse=True):
                if value and value in result:
                    token = self.pseudonymize(category, value)
                    result = result.replace(value, token)
        return result

    def detect_pii_in(self, text: str) -> list[str]:
        """Findet Tokens im Text und gibt ihre Kategorien zurück."""
        return re.findall(r"\[([A-Z]+_[a-f0-9]{6})\]", text)

    def find_leaked_pii(self, text: str) -> list[tuple[str, str]]:
        """Sicherheitscheck: prüft ob Klartextwerte aus der Lookup-Tabelle im Text vorkommen.
        Gibt Liste von (Wert, Kategorie) zurück.
        """
        leaks = []
        for category, mappings in self.forward.items():
            for real_value in mappings:
                if real_value in text:
                    leaks.append((real_value, category))
        return leaks

    def get_mappings(self) -> dict:
        return self.forward

    def clear(self):
        self.forward = {}
        self.reverse = {}
        if LOOKUP_FILE.exists():
            LOOKUP_FILE.unlink()
