#!/bin/bash
set -e

# ==========================================
# Small Voice Project - Production Deploy Script
# Optimized for: GCE e2-small (Limited Disk)
# Requires: User must be in 'docker' group
# ==========================================

echo "🚀 Starting deployment process..."

# 0. Check Docker Permission
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running or you don't have permission."
    echo "   Try running: 'newgrp docker' or check if docker daemon is up."
    exit 1
fi

# 1. Update Codebase
echo "📥 Pulling latest changes from git..."
git pull origin main

# 2. Stop & Clean (Critical for 30GB Disk)
echo "🛑 Stopping services to free up space..."
docker compose -f docker-compose.prod.yml down

echo "🧹 Pruning ALL unused images and build cache..."
# This removes all stopped containers, unused networks, and ALL images not currently used by a running container
# Since we stopped the services above, this will delete the old application images.
docker system prune -af

# 3. Pull Latest Images
echo "⬇️ Pulling latest Docker images..."
docker compose -f docker-compose.prod.yml pull

# 4. Update Metadata in .env
echo "📝 Updating deployment metadata..."
GIT_COMMIT_HASH=$(git rev-parse --short HEAD)
DEPLOY_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

update_env() {
    local key=$1
    local value=$2
    if grep -q "^$key=" .env; then
        sed -i "s|^$key=.*|$key=\"$value\"|" .env
    else
        echo "$key=\"$value\"" >> .env
    fi
}

# backup .env just in case
cp .env .env.bak

# Update .env (using sed -i is safe on Linux)
update_env "GIT_COMMIT_HASH" "$GIT_COMMIT_HASH"
update_env "DEPLOY_TIMESTAMP" "$DEPLOY_TIMESTAMP"

echo "   - Version: $GIT_COMMIT_HASH"
echo "   - Timestamp: $DEPLOY_TIMESTAMP"

# 5. Start Services
echo "� Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo "✅ Deployment completed successfully!"
