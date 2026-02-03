#!/bin/bash
#
# TEMU Development Environment Setup Script
# Creates a separate development environment alongside production
#
# Usage: ./scripts/setup_dev_environment.sh
#
# What it does:
# 1. Clones repository to /home/chx/temu-dev
# 2. Creates virtual environment
# 3. Installs dependencies
# 4. Configures .env (Port 8001)
# 5. Creates bash aliases
# 6. Provides next steps
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROD_DIR="/home/chx/temu"
DEV_DIR="/home/chx/temu-dev"
DEV_PORT=8001

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  TEMU Development Environment Setup                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Production:${NC} $PROD_DIR (Port 8000)"
echo -e "${BLUE}Development:${NC} $DEV_DIR (Port $DEV_PORT)"
echo ""

# ============================================================
# Step 1: Check if dev directory already exists
# ============================================================
echo -e "${YELLOW}Step 1: Checking environment...${NC}"

if [ -d "$DEV_DIR" ]; then
    echo -e "${YELLOW}⚠ Warning: $DEV_DIR already exists!${NC}"
    echo ""
    read -p "Delete and recreate? This will remove ALL changes! (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${RED}✗ Setup aborted by user${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Removing existing $DEV_DIR...${NC}"
    rm -rf "$DEV_DIR"
fi

echo -e "${GREEN}✓ Environment check complete${NC}"
echo ""

# ============================================================
# Step 2: Clone repository
# ============================================================
echo -e "${YELLOW}Step 2: Cloning repository...${NC}"

if [ ! -d "$PROD_DIR" ]; then
    echo -e "${RED}✗ Error: Production directory not found: $PROD_DIR${NC}"
    echo -e "${RED}  Please ensure production is set up first.${NC}"
    exit 1
fi

# Clone from local production directory
echo "Cloning from: $PROD_DIR"
git clone "$PROD_DIR" "$DEV_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error: Failed to clone repository${NC}"
    echo -e "${YELLOW}  Trying alternative method...${NC}"

    # Alternative: Copy directory
    cp -r "$PROD_DIR" "$DEV_DIR"
    cd "$DEV_DIR"

    # Reinitialize git (clean any local changes)
    rm -rf .git
    git init
    git remote add origin $(cd "$PROD_DIR" && git config --get remote.origin.url)
    git fetch origin
    git checkout -b main --track origin/main
fi

echo -e "${GREEN}✓ Repository cloned to $DEV_DIR${NC}"
echo ""

# ============================================================
# Step 3: Create virtual environment
# ============================================================
echo -e "${YELLOW}Step 3: Creating virtual environment...${NC}"

cd "$DEV_DIR"

# Remove existing venv if any
if [ -d ".venv" ]; then
    rm -rf .venv
fi

# Create new venv
python3 -m venv .venv

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error: Failed to create virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment created${NC}"
echo ""

# ============================================================
# Step 4: Install dependencies
# ============================================================
echo -e "${YELLOW}Step 4: Installing dependencies...${NC}"

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "Installing packages from requirements.txt..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error: Failed to install dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# ============================================================
# Step 5: Configure .env file
# ============================================================
echo -e "${YELLOW}Step 5: Configuring environment...${NC}"

ENV_FILE="modules/shared/config/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ Error: .env file not found: $ENV_FILE${NC}"
    echo -e "${YELLOW}  You'll need to create it manually.${NC}"
else
    # Backup original
    cp "$ENV_FILE" "${ENV_FILE}.backup"

    # Update PORT in .env
    if grep -q "^PORT=" "$ENV_FILE"; then
        sed -i "s/^PORT=.*/PORT=$DEV_PORT/" "$ENV_FILE"
        echo -e "${GREEN}✓ PORT updated to $DEV_PORT in $ENV_FILE${NC}"
    else
        echo "" >> "$ENV_FILE"
        echo "PORT=$DEV_PORT" >> "$ENV_FILE"
        echo -e "${GREEN}✓ PORT=$DEV_PORT added to $ENV_FILE${NC}"
    fi

    # Add ENVIRONMENT flag if not exists
    if ! grep -q "^ENVIRONMENT=" "$ENV_FILE"; then
        echo "ENVIRONMENT=development" >> "$ENV_FILE"
        echo -e "${GREEN}✓ ENVIRONMENT=development added to $ENV_FILE${NC}"
    fi

    # Add LOG_LEVEL if not exists
    if ! grep -q "^LOG_LEVEL=" "$ENV_FILE"; then
        echo "LOG_LEVEL=DEBUG" >> "$ENV_FILE"
        echo -e "${GREEN}✓ LOG_LEVEL=DEBUG added to $ENV_FILE${NC}"
    fi
fi

echo ""

# ============================================================
# Step 6: Create bash aliases
# ============================================================
echo -e "${YELLOW}Step 6: Creating bash aliases...${NC}"

BASHRC="$HOME/.bashrc"
ALIAS_MARKER="# TEMU Development Aliases"

# Check if aliases already exist
if grep -q "$ALIAS_MARKER" "$BASHRC"; then
    echo -e "${YELLOW}⚠ Aliases already exist in $BASHRC${NC}"
    echo -e "${YELLOW}  Skipping alias creation.${NC}"
else
    # Add aliases
    cat >> "$BASHRC" << 'EOF'

# ==================== TEMU Development Aliases ====================

# Quick navigation
alias temu-dev='cd /home/chx/temu-dev && source .venv/bin/activate'
alias temu-live='cd /home/chx/temu'

# Start development server
alias temu-start='cd /home/chx/temu-dev && source .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8001'

# Quick status checks
alias temu-dev-status='curl -s http://localhost:8001/api/health | jq'
alias temu-live-status='curl -s http://localhost:8000/api/health | jq'

# Git shortcuts
alias temu-dev-branch='cd /home/chx/temu-dev && git branch'
alias temu-dev-git='cd /home/chx/temu-dev && git status'

# Logs
alias temu-dev-logs='tail -f /home/chx/temu-dev/logs/pdf_reader/pdf_reader.log'
alias temu-live-logs='pm2 logs temu-api --lines 50'

# Screen shortcuts
alias temu-screen='screen -S temu-dev'
alias temu-attach='screen -r temu-dev'
alias temu-screens='screen -ls'

# ==================================================================

EOF
    echo -e "${GREEN}✓ Aliases added to $BASHRC${NC}"
    echo -e "${BLUE}  Run 'source ~/.bashrc' to activate them${NC}"
fi

echo ""

# ============================================================
# Step 7: Create initial feature branch
# ============================================================
echo -e "${YELLOW}Step 7: Setting up git...${NC}"

cd "$DEV_DIR"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}Current branch: $CURRENT_BRANCH${NC}"

# Suggest creating feature branch
echo ""
echo -e "${BLUE}Recommendation: Create a feature branch for development${NC}"
read -p "Create feature branch? (yes/no): " create_branch

if [ "$create_branch" = "yes" ]; then
    read -p "Enter feature branch name (e.g., feature/my-feature): " branch_name
    if [ ! -z "$branch_name" ]; then
        git checkout -b "$branch_name"
        echo -e "${GREEN}✓ Created and switched to branch: $branch_name${NC}"
    fi
fi

echo ""

# ============================================================
# Summary and Next Steps
# ============================================================
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Setup Complete!                                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Development Environment:${NC}"
echo -e "  Location:  $DEV_DIR"
echo -e "  Port:      $DEV_PORT"
echo -e "  Branch:    $(cd "$DEV_DIR" && git branch --show-current)"
echo ""
echo -e "${BLUE}Production Environment:${NC}"
echo -e "  Location:  $PROD_DIR"
echo -e "  Port:      8000"
echo -e "  Status:    $(pm2 list | grep temu-api | awk '{print $10}')"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}1. Reload bash configuration:${NC}"
echo -e "   ${GREEN}source ~/.bashrc${NC}"
echo ""
echo -e "${BLUE}2. Start development server:${NC}"
echo -e "   ${GREEN}temu-start${NC}"
echo -e "   ${BLUE}Or with screen:${NC}"
echo -e "   ${GREEN}screen -S temu-dev${NC}"
echo -e "   ${GREEN}temu-start${NC}"
echo -e "   ${BLUE}(Detach with: Ctrl+A, then D)${NC}"
echo ""
echo -e "${BLUE}3. Access development environment:${NC}"
echo -e "   ${GREEN}http://192.168.178.4:8001${NC}  (Frontend)"
echo -e "   ${GREEN}http://localhost:8001/api/health${NC}  (API)"
echo ""
echo -e "${BLUE}4. Test API:${NC}"
echo -e "   ${GREEN}curl http://localhost:8001/api/health${NC}"
echo ""
echo -e "${BLUE}5. Development workflow:${NC}"
echo -e "   - Edit code in: $DEV_DIR"
echo -e "   - Auto-reload is enabled (--reload flag)"
echo -e "   - Commit often: ${GREEN}git commit -m \"feat: description\"${NC}"
echo -e "   - Push to GitHub: ${GREEN}git push origin <branch>${NC}"
echo ""
echo -e "${BLUE}6. Deploy to production when ready:${NC}"
echo -e "   ${GREEN}cd /home/chx/temu${NC}"
echo -e "   ${GREEN}git pull origin <branch>${NC}"
echo -e "   ${GREEN}pm2 restart temu-api${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Useful Aliases:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${GREEN}temu-dev${NC}           - Navigate to dev + activate venv"
echo -e "  ${GREEN}temu-start${NC}         - Start development server"
echo -e "  ${GREEN}temu-dev-status${NC}    - Check dev server health"
echo -e "  ${GREEN}temu-live-status${NC}   - Check production server health"
echo -e "  ${GREEN}temu-screen${NC}        - Start screen session"
echo -e "  ${GREEN}temu-attach${NC}        - Attach to screen session"
echo -e "  ${GREEN}temu-dev-logs${NC}      - View development logs"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Documentation:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BLUE}Full guide:${NC} $PROD_DIR/docs/DEVELOPMENT/dev_environment_setup.md"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
