#!/usr/bin/env bash
# ==============================================================================
# ShiVi Production Deployment Orchestrator (Docker & Nginx Stack)
# ==============================================================================
set -eo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}================================================================================"
echo -e "  🚀 SHIVI - SMART HYBRID INTELLIGENT VIRTUAL INTEGRATION (PRODUCTION DEPLOY)  "
echo -e "================================================================================${NC}"

# Check Docker CLI
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker is not installed or not in PATH. Aborting.${NC}"
    exit 1
fi

# Detect docker compose or docker-compose
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}[ERROR] Docker Compose is not installed. Aborting.${NC}"
    exit 1
fi

echo -e "${CYAN}[INFO] Using: $($COMPOSE_CMD version)${NC}"

# Ensure environment file exists
if [ ! -f .env.production ]; then
    echo -e "${YELLOW}[WARN] .env.production not found. Generating default production secrets...${NC}"
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || echo "shivi_disaster_ops_production_key_2026_secured")
    cat <<EOF > .env.production
NODE_ENV=production
ENVIRONMENT=production
JWT_SECRET=${JWT_SECRET}
PORT=8000
FRONTEND_PORT=3000
DATABASE_URL=sqlite+aiosqlite:////data/shivi_production.db
CORS_ORIGINS=*
EOF
    echo -e "${GREEN}[OK] .env.production generated successfully.${NC}"
fi

# Pull & Build Images
echo -e "${CYAN}[1/3] Building production microservices (FastAPI + Next.js Standalone)...${NC}"
$COMPOSE_CMD -f docker-compose.prod.yml build --parallel

# Launch Containers
echo -e "${CYAN}[2/3] Launching containerized topology with Nginx Reverse Proxy...${NC}"
$COMPOSE_CMD -f docker-compose.prod.yml up -d

# Wait for Healthy Endpoints
echo -e "${CYAN}[3/3] Awaiting cluster health convergence (timeout: 60s)...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f http://localhost/nginx-health &> /dev/null && curl -s -f http://localhost/health &> /dev/null; then
        echo -e "\n${GREEN}================================================================================"
        echo -e "  ✅ SHIVI PRODUCTION CLUSTER ONLINE & HEALTHY"
        echo -e "================================================================================${NC}"
        echo -e "  • Unified Web Entrance: ${CYAN}http://localhost${NC} (Port 80 via Nginx)"
        echo -e "  • Common Operational Picture: ${CYAN}http://localhost/${NC}"
        echo -e "  • Disaster SMS & Satellite Lab: ${CYAN}http://localhost/sms${NC}"
        echo -e "  • REST API Documentation:     ${CYAN}http://localhost/docs${NC}"
        echo -e "  • Core Edge Health Probe:     ${CYAN}http://localhost/health${NC}"
        echo -e "  • Container Status:           ${CYAN}$($COMPOSE_CMD -f docker-compose.prod.yml ps)${NC}"
        echo -e "${GREEN}================================================================================${NC}"
        exit 0
    fi
    printf "."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

echo -e "\n${RED}[ERROR] Cluster healthcheck timed out after 60 seconds.${NC}"
$COMPOSE_CMD -f docker-compose.prod.yml logs --tail=30
exit 1
