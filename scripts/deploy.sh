#!/bin/bash
# Revolution X - Production Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENV=${1:-production}
COMPOSE_FILE="docker/docker-compose.prod.yml"
BACKUP_DIR="/backups/revolutionx/$(date +%Y%m%d_%H%M%S)"

echo -e "${YELLOW}🚀 Starting Revolution X deployment to ${ENV}...${NC}"

# Pre-deployment checks
echo -e "${YELLOW}📋 Running pre-deployment checks...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found${NC}"
    exit 1
fi

# Check environment file
if [ ! -f ".env.${ENV}" ]; then
    echo -e "${RED}❌ Environment file .env.${ENV} not found${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env.${ENV} | xargs)

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup database
echo -e "${YELLOW}💾 Creating database backup...${NC}"
docker-compose -f ${COMPOSE_FILE} exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > ${BACKUP_DIR}/db_backup.sql
echo -e "${GREEN}✅ Backup created at ${BACKUP_DIR}${NC}"

# Pull latest images
echo -e "${YELLOW}📥 Pulling latest images...${NC}"
docker-compose -f ${COMPOSE_FILE} pull

# Run database migrations
echo -e "${YELLOW}🗄️ Running database migrations...${NC}"
docker-compose -f ${COMPOSE_FILE} run --rm backend alembic upgrade head

# Deploy with zero downtime
echo -e "${YELLOW}🚀 Deploying new version...${NC}"
docker-compose -f ${COMPOSE_FILE} up -d --no-deps --scale backend=4 backend

# Wait for health checks
echo -e "${YELLOW}⏳ Waiting for health checks...${NC}"
sleep 10

# Check if new containers are healthy
if docker-compose -f ${COMPOSE_FILE} ps | grep -q "unhealthy"; then
    echo -e "${RED}❌ Health checks failed! Rolling back...${NC}"
    docker-compose -f ${COMPOSE_FILE} up -d --no-deps backend
    exit 1
fi

# Scale down old containers
echo -e "${YELLOW}🔄 Scaling down old containers...${NC}"
docker-compose -f ${COMPOSE_FILE} up -d --no-deps --scale backend=3 backend

# Update frontend
echo -e "${YELLOW}🎨 Updating frontend...${NC}"
docker-compose -f ${COMPOSE_FILE} up -d --no-deps frontend

# Clean up old images
echo -e "${YELLOW}🧹 Cleaning up old images...${NC}"
docker image prune -af --filter "until=168h"

# Verify deployment
echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
if curl -sf http://localhost/health > /dev/null; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
else
    echo -e "${RED}❌ Deployment verification failed${NC}"
    exit 1
fi

# Send notification
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    curl -s -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚀 Revolution X deployed successfully to '${ENV}'"}' \
        ${SLACK_WEBHOOK_URL}
fi

echo -e "${GREEN}🎉 Deployment complete!${NC}"
