#!/bin/bash
# private-ai-bridge — Installer mit Hardware-Test und Modell-Auswahl

set -e

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

echo ""
echo -e "${BOLD}┌─────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}│  private-ai-bridge Installer                    │${NC}"
echo -e "${BOLD}│  DSGVO-konforme KI mit Claude + Gemma        │${NC}"
echo -e "${BOLD}└─────────────────────────────────────────────┘${NC}"
echo ""

# ── 1. System erkennen ─────────────────────────────────────────
echo -e "${BLUE}[1/5] Hardware analysieren...${NC}"

OS="$(uname -s)"
case "$OS" in
    Darwin)  OS_NAME="macOS" ;;
    Linux)   OS_NAME="Linux" ;;
    *)       OS_NAME="$OS" ;;
esac

if [ "$OS" = "Darwin" ]; then
    RAM_BYTES=$(sysctl -n hw.memsize)
    RAM_GB=$((RAM_BYTES / 1024 / 1024 / 1024))
    CPU=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || sysctl -n machdep.cpu.vendor 2>/dev/null || echo "?")
    ARCH=$(uname -m)
elif [ "$OS" = "Linux" ]; then
    RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    RAM_GB=$((RAM_KB / 1024 / 1024))
    CPU=$(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2 | xargs || echo "?")
    ARCH=$(uname -m)
else
    RAM_GB=8
    CPU="?"
    ARCH="?"
fi

echo "  System: $OS_NAME ($ARCH)"
echo "  CPU:    $CPU"
echo "  RAM:    ${RAM_GB} GB"
echo ""

# ── 2. Ollama prüfen/installieren ──────────────────────────────
echo -e "${BLUE}[2/5] Ollama prüfen...${NC}"

if ! command -v ollama &> /dev/null; then
    echo -e "  ${YELLOW}Ollama nicht installiert.${NC}"
    if [ "$OS" = "Darwin" ]; then
        if command -v brew &> /dev/null; then
            read -p "  Mit Homebrew installieren? [y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                brew install ollama
                brew services start ollama
                sleep 3
            else
                echo -e "  ${RED}Bitte Ollama manuell installieren: https://ollama.com${NC}"
                exit 1
            fi
        else
            echo -e "  ${RED}Bitte Homebrew oder Ollama manuell installieren.${NC}"
            exit 1
        fi
    else
        echo "  Installiere Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
else
    echo -e "  ${GREEN}✓ Ollama installiert${NC}"
fi

# Ollama starten falls nicht aktiv
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Ollama-Server starten..."
    if [ "$OS" = "Darwin" ]; then
        brew services start ollama 2>/dev/null || ollama serve &
    else
        ollama serve &
    fi
    sleep 3
fi

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Ollama läuft${NC}"
else
    echo -e "  ${RED}✗ Ollama nicht erreichbar${NC}"
    exit 1
fi
echo ""

# ── 3. Modell empfehlen ─────────────────────────────────────────
echo -e "${BLUE}[3/5] Passendes Modell wählen...${NC}"

if [ $RAM_GB -lt 6 ]; then
    DEFAULT_MODEL="gemma:2b"
    echo "  Empfehlung: gemma:2b (~2 GB)"
    echo "  ${YELLOW}Hinweis: bei <6 GB RAM ist die Performance limitiert${NC}"
elif [ $RAM_GB -lt 12 ]; then
    DEFAULT_MODEL="gemma:2b"
    echo "  Empfehlung: gemma:2b (~2 GB) — sicher, schnell"
elif [ $RAM_GB -lt 20 ]; then
    DEFAULT_MODEL="gemma4:e4b"
    echo "  Empfehlung: gemma4:e4b (~6 GB) — gute Balance"
elif [ $RAM_GB -lt 36 ]; then
    DEFAULT_MODEL="gemma4:e4b"
    echo "  Empfehlung: gemma4:e4b (~6 GB)"
    echo "  Optional: gemma4:26b-a4b (~16 GB) für mehr Qualität"
else
    DEFAULT_MODEL="gemma4:26b-a4b"
    echo "  Empfehlung: gemma4:26b-a4b (~16 GB) — beste Qualität"
fi
echo ""

# Optionen anzeigen
echo "  Verfügbare Modelle:"
echo "    1) gemma:2b          (~2 GB,   schnell, einfach)"
echo "    2) gemma4:e2b        (~3 GB,   ausgewogen)"
echo "    3) gemma4:e4b        (~6 GB,   empfohlen für 16 GB RAM)"
echo "    4) gemma4:26b-a4b    (~16 GB,  beste Qualität, MoE)"
echo ""
read -p "  Welches Modell installieren? [1-4, Enter für '$DEFAULT_MODEL'] " choice

case $choice in
    1) MODEL="gemma:2b" ;;
    2) MODEL="gemma4:e2b" ;;
    3) MODEL="gemma4:e4b" ;;
    4) MODEL="gemma4:26b-a4b" ;;
    *) MODEL="$DEFAULT_MODEL" ;;
esac

echo ""
echo -e "${BLUE}[4/5] Modell '$MODEL' herunterladen...${NC}"

if ollama list 2>/dev/null | grep -q "${MODEL%:*}"; then
    echo -e "  ${GREEN}✓ Modell bereits installiert${NC}"
else
    ollama pull "$MODEL"
    echo -e "  ${GREEN}✓ Modell heruntergeladen${NC}"
fi
echo ""

# ── 4. Python-Abhängigkeiten ───────────────────────────────────
echo -e "${BLUE}[5/5] Python-Abhängigkeiten installieren...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "  ${RED}Python 3 nicht gefunden. Bitte installieren.${NC}"
    exit 1
fi

# venv erstellen
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "  Virtuelle Umgebung erstellen..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet mcp httpx
echo -e "  ${GREEN}✓ Abhängigkeiten installiert${NC}"
echo ""

# ── 5. Konfiguration anpassen ─────────────────────────────────
echo -e "${BLUE}Konfiguration anpassen...${NC}"

# .mcp.json mit gewähltem Modell und Pfad updaten
cat > .mcp.json <<EOF
{
  "mcpServers": {
    "private-ai-bridge": {
      "command": "$SCRIPT_DIR/venv/bin/python",
      "args": ["-m", "server"],
      "cwd": "$SCRIPT_DIR",
      "env": {
        "PRIVATE_AI_BRIDGE_MODEL": "$MODEL"
      }
    }
  }
}
EOF
echo -e "  ${GREEN}✓ .mcp.json erstellt${NC}"
echo ""

# ── Fertig ────────────────────────────────────────────────────
echo -e "${GREEN}${BOLD}✓ Installation abgeschlossen!${NC}"
echo ""
echo "Nächste Schritte:"
echo "  1. Claude Code in diesem Verzeichnis starten:"
echo -e "     ${BOLD}claude${NC}"
echo ""
echo "  2. Demo ansehen:"
echo -e "     ${BOLD}cd web && python3 -m http.server 8080${NC}"
echo "     Browser: http://localhost:8080"
echo ""
echo "  3. Beispiel testen — Frage Claude:"
echo -e '     ${BOLD}"Schreibe Zeugnisbemerkungen für die Schüler in examples/schueler/schueler.json"${NC}'
echo ""
echo -e "Konfiguration: ${BOLD}$SCRIPT_DIR/.mcp.json${NC}"
echo -e "Modell:        ${BOLD}$MODEL${NC}"
echo ""
