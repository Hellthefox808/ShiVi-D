#!/usr/bin/env bash
# ==============================================================================
# ShiVi Zero-Docker Tactical Edge Deployment (Bare-Metal / Rugged Field Laptop)
# ==============================================================================
set -eo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo -e "${GREEN}================================================================================"
echo -e "  🛡️ SHIVI - ZERO-DOCKER BARE-METAL TACTICAL EDGE DEPLOYMENT                    "
echo -e "================================================================================${NC}"

# Check Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] python3 not found. Required for Core API.${NC}"
    exit 1
fi

# Check Node.js 18+
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js not found. Required for Web COP.${NC}"
    exit 1
fi

echo -e "${CYAN}[1/4] Configuring Python Core API Environment...${NC}"
cd "$BACKEND_DIR"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "${GREEN}[OK] Python backend virtualenv ready.${NC}"

echo -e "${CYAN}[2/4] Compiling Next.js Standalone Frontend...${NC}"
cd "$FRONTEND_DIR"
npm ci --silent
npm run build

echo -e "${CYAN}[3/4] Initializing Database & Seed Telemetry...${NC}"
cd "$BACKEND_DIR"
python scripts/reset_db_safe.py || true
python scripts/seed_data.py || true

echo -e "${CYAN}[4/4] Starting Microservice Daemons in Background...${NC}"
mkdir -p "$ROOT_DIR/logs"

# Start Backend
PORT=8000 HOST=0.0.0.0 nohup python server.py > "$ROOT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$ROOT_DIR/logs/backend.pid"

# Start Frontend
cd "$FRONTEND_DIR"
PORT=3000 nohup node scripts/run-next.js start > "$ROOT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$ROOT_DIR/logs/frontend.pid"

# Sleep for startup
sleep 3

# Verify Health
if curl -s -f http://localhost:8000/health &> /dev/null; then
    echo -e "\n${GREEN}================================================================================"
    echo -e "  ✅ SHIVI TACTICAL BARE-METAL DEPLOYMENT ACTIVE"
    echo -e "================================================================================${NC}"
    echo -e "  • Web Command Portal:         ${CYAN}http://localhost:3000${NC} (PID: $FRONTEND_PID)"
    echo -e "  • Disaster SMS & Sat Lab:     ${CYAN}http://localhost:3000/sms${NC}"
    echo -e "  • REST API Documentation:     ${CYAN}http://localhost:8000/docs${NC} (PID: $BACKEND_PID)"
    echo -e "  • Health Probe Endpoint:      ${CYAN}http://localhost:8000/health${NC}"
    echo -e "  • Log Files:                  ${CYAN}$ROOT_DIR/logs/${NC}"
    echo -e "${GREEN}================================================================================${NC}"
else
    echo -e "${RED}[ERROR] Backend failed to start. Review logs at $ROOT_DIR/logs/backend.log${NC}"
    exit 1
fi
