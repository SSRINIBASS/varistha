#!/usr/bin/env bash
# ==============================================================================
# Varistha One-Line Installer (Linux / macOS)
# Open-source control plane to build, run, monitor and govern AI agents
# License: Apache-2.0
# ==============================================================================

set -euo pipefail

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

print_banner() {
    echo -e "${BOLD}${BLUE}"
    cat << "EOF"
  __     __         _     _   _           
  \ \   / /_ _ _ __(_)___| |_| |__   __ _ 
   \ \ / / _` | '__| / __| __| '_ \ / _` |
    \ V / (_| | |  | \__ \ |_| | | | (_| |
     \_/ \__,_|_|  |_|___/\__|_| |_|\__,_|
EOF
    echo -e "${NC}${BOLD}AI Employee Control Plane for Startups${NC}\n"
}

check_prerequisites() {
    info "Verifying system prerequisites..."

    # Check git
    if ! command -v git &> /dev/null; then
        error "git is not installed. Please install git and re-run this script."
        exit 1
    fi

    # Check docker
    if ! command -v docker &> /dev/null; then
        warn "docker is not detected in PATH. Docker is required to run the local control plane."
    fi

    # Check python or uv
    if command -v uv &> /dev/null; then
        info "Found uv package manager: $(uv --version)"
    elif command -v python3 &> /dev/null; then
        PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        info "Found Python: $PY_VER"
    else
        warn "Neither uv nor Python 3.12+ was detected. You can install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
}

install_varistha() {
    TARGET_DIR="${VARISTHA_HOME:-$HOME/.varistha}"
    REPO_URL="https://github.com/SSRINIBASS/varistha.git"

    if [ -d "$TARGET_DIR/.git" ]; then
        info "Existing Varistha installation found at $TARGET_DIR. Updating..."
        git -C "$TARGET_DIR" pull --quiet origin main || git -C "$TARGET_DIR" pull --quiet origin master || true
    else
        info "Cloning Varistha into $TARGET_DIR..."
        git clone --quiet "$REPO_URL" "$TARGET_DIR"
    fi

    # Configure .env if not present
    if [ ! -f "$TARGET_DIR/deploy/.env" ] && [ -f "$TARGET_DIR/deploy/.env.example" ]; then
        info "Generating initial deploy/.env configuration..."
        cp "$TARGET_DIR/deploy/.env.example" "$TARGET_DIR/deploy/.env"
        # Generate random 32-byte secret key if openssl is available
        if command -v openssl &> /dev/null; then
            NEW_SECRET=$(openssl rand -hex 32)
            sed -i.bak "s/dev-secret-key-change-in-production/${NEW_SECRET}/g" "$TARGET_DIR/deploy/.env" 2>/dev/null || true
            rm -f "$TARGET_DIR/deploy/.env.bak"
        fi
    fi

    # Install CLI
    info "Installing varistha CLI tool..."
    if command -v uv &> /dev/null; then
        uv tool install --editable "$TARGET_DIR/packages/cli" --force 2>/dev/null || \
            uv pip install --editable "$TARGET_DIR/packages/cli" 2>/dev/null || true
    elif command -v pip3 &> /dev/null; then
        pip3 install --user --editable "$TARGET_DIR/packages/cli" 2>/dev/null || true
    fi

    success "Varistha successfully installed at $TARGET_DIR!"
}

print_next_steps() {
    TARGET_DIR="${VARISTHA_HOME:-$HOME/.varistha}"
    echo ""
    echo -e "${BOLD}Next Steps:${NC}"
    echo -e "  1. Start the local control plane:"
    echo -e "     ${GREEN}cd $TARGET_DIR && docker compose -f deploy/docker-compose.yml up -d${NC}"
    echo -e "  2. Access the dashboard:"
    echo -e "     ${BLUE}http://localhost:3000${NC}"
    echo -e "  3. Create your first agent spec:"
    echo -e "     ${GREEN}varistha init --name my-agent${NC}"
    echo -e "  4. Apply and trigger execution:"
    echo -e "     ${GREEN}varistha apply -f agent.yaml && varistha run my-agent${NC}"
    echo ""
}

main() {
    print_banner
    check_prerequisites
    install_varistha
    print_next_steps
}

main "$@"
