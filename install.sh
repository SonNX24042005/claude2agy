#!/usr/bin/env bash
# Claude2AGY & AGY2Claude One-Line Installer for Linux, macOS, WSL, and Git Bash

set -e

# Detect source repo path or URL
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
INSTALL_DIR="$HOME/.claude2agy"
BIN_DIR="$HOME/.local/bin"

echo "Installing Claude2AGY & AGY2Claude..."

# 1. Check Python installation
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "Error: Python 3 is required but not installed." >&2
    exit 1
fi

# 2. Setup installation directory
mkdir -p "$INSTALL_DIR"

if [ -d "$SCRIPT_DIR/claude2agy" ]; then
    # Running from cloned repo directory
    cp -r "$SCRIPT_DIR/claude2agy" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/setup.py" "$INSTALL_DIR/" 2>/dev/null || true
    cp "$SCRIPT_DIR/run.sh" "$INSTALL_DIR/" 2>/dev/null || true
else
    # Downloading from GitHub repository
    REPO_URL="${CLAUDE2AGY_REPO_URL:-https://github.com/SonNX24042005/claude2agy.git}"
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "Updating existing installation in $INSTALL_DIR..."
        git -C "$INSTALL_DIR" pull --quiet || true
    else
        echo "Downloading source code into $INSTALL_DIR..."
        if command -v git &>/dev/null; then
            git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
        else
            curl -fsSL "https://raw.githubusercontent.com/SonNX24042005/claude2agy/main/run.sh" -o "$INSTALL_DIR/run.sh"
        fi
    fi
fi

# 3. Create bin directory
mkdir -p "$BIN_DIR"

# 4. Create wrapper executable for claude2agy
cat << 'EOF' > "$BIN_DIR/claude2agy"
#!/usr/bin/env bash
SCRIPT_DIR="$HOME/.claude2agy"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi
PYTHONPATH="$SCRIPT_DIR" "$PYTHON_CMD" -m claude2agy.cli "$@"
EOF

# 5. Create wrapper executable for agy2claude
cat << 'EOF' > "$BIN_DIR/agy2claude"
#!/usr/bin/env bash
SCRIPT_DIR="$HOME/.claude2agy"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi
PYTHONPATH="$SCRIPT_DIR" "$PYTHON_CMD" -m claude2agy.cli --reverse "$@"
EOF

chmod +x "$BIN_DIR/claude2agy" "$BIN_DIR/agy2claude"

# 6. Check PATH
PATH_ADDED=false
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
        PATH_ADDED=true
        SHELL_PROFILE=""
        if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
            SHELL_PROFILE="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_PROFILE="$HOME/.bashrc"
        elif [ -f "$HOME/.profile" ]; then
            SHELL_PROFILE="$HOME/.profile"
        fi

        if [ -n "$SHELL_PROFILE" ]; then
            if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_PROFILE"; then
                echo '' >> "$SHELL_PROFILE"
                echo '# Added by Claude2AGY installer' >> "$SHELL_PROFILE"
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_PROFILE"
            fi
        fi
        ;;
esac

echo ""
echo "Installation completed successfully!"
echo "Commands installed:"
echo "  - claude2agy (Claude Code -> Antigravity)"
echo "  - agy2claude (Antigravity -> Claude Code)"
echo ""
if [ "$PATH_ADDED" = true ]; then
    echo "Note: Please restart your terminal or run:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi
