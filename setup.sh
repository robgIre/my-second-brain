#!/bin/bash
# ============================================================================
# My Second Brain — One-time setup script
# Run this once on your OD to get started.
# ============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}  ║     My Second Brain — Setup      ║${RESET}"
echo -e "${CYAN}${BOLD}  ╚══════════════════════════════════╝${RESET}"
echo ""

# ── Step 1: Find the project ─────────────────────────────────────────────────

# Detect the project directory (works from git clone or Google Drive)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/app.py" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
else
    echo -e "${RED}Could not find app.py in the same directory as this script.${RESET}"
    echo "Make sure you're running setup.sh from the my-second-brain folder."
    echo ""
    echo "Try:"
    echo "  cd ~/my-second-brain && bash setup.sh"
    exit 1
fi

echo -e "${GREEN}[1/5]${RESET} Found project at:"
echo "      $PROJECT_DIR"
echo ""

# ── Step 2: Check Python ─────────────────────────────────────────────────────

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Please install Python 3 first.${RESET}"
    exit 1
fi

PY_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}[2/5]${RESET} $PY_VERSION"

# ── Step 3: Install dependencies ─────────────────────────────────────────────

VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${GREEN}[3/4]${RESET} Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo -e "${GREEN}[3/5]${RESET} Installing dependencies..."
pip install -q --proxy http://fwdproxy:8080 -r "$PROJECT_DIR/requirements.txt" 2>/dev/null \
    || pip install -q -r "$PROJECT_DIR/requirements.txt"
echo "      Done."
echo ""

# ── Step 4: Check Claude Code ────────────────────────────────────────────────

if command -v claude &> /dev/null; then
    echo -e "${GREEN}[4/5]${RESET} Claude Code CLI found."
else
    echo -e "${YELLOW}[4/5]${RESET} Claude Code CLI not found in PATH."
    echo "      The app will still run, but you won't be able to connect until Claude Code is installed."
    echo "      See: https://www.internalfb.com/wiki/Thomas_Wu/Building_Your_AI_Toolkit_at_Meta/"
fi

# ── Step 5: Install plugins (if not already installed) ───────────────────────

if command -v claude &> /dev/null; then
    PLUGINS_NEEDED=(
        "calendar@claude-templates"
        "para-workspace@claude-templates"
        "data@claude-templates"
        "debrief@claude-templates"
        "gdrive-mount@claude-templates"
    )

    SETTINGS_FILE="$HOME/.claude/settings.json"
    INSTALLED_ANY=false

    for plugin in "${PLUGINS_NEEDED[@]}"; do
        # Check if plugin is already enabled in settings.json
        plugin_key=$(echo "$plugin" | sed 's/@/-at-/g')
        if [ -f "$SETTINGS_FILE" ] && grep -q "\"$plugin\"" "$SETTINGS_FILE" 2>/dev/null; then
            continue
        fi
        if [ "$INSTALLED_ANY" = false ]; then
            echo ""
            echo -e "${GREEN}[5/5]${RESET} Installing plugins..."
            INSTALLED_ANY=true
        fi
        claude plugin install "$plugin" 2>/dev/null || true
    done

    if [ "$INSTALLED_ANY" = true ]; then
        echo "      Done."
    else
        echo -e "${GREEN}[5/5]${RESET} Plugins already installed."
    fi
else
    echo -e "${YELLOW}[5/5]${RESET} Skipping plugin install (Claude Code not found)."
fi

echo ""

# ── Start the server ─────────────────────────────────────────────────────────

PORT="${MSB_PORT:-${BIAJ_PORT:-5151}}"

echo -e "${CYAN}${BOLD}  Starting My Second Brain...${RESET}"
echo ""
echo -e "  Open this URL in your browser:"
echo ""
echo -e "  ${BOLD}${GREEN}  http://localhost:${PORT}  ${RESET}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${RESET} to stop."
echo ""
echo "──────────────────────────────────────"

cd "$PROJECT_DIR"
python3 app.py
