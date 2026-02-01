#!/bin/bash
set -e

# Deployment Script for Small Voice Project Production

echo "🚀 Starting deployment process..."

# 1. Update Codebase
echo "📥 Pulling latest changes from git..."
git pull origin main

# 2. Infrastructure Maintenance
echo "🧹 Pruning unused Docker resources to free up space..."
sudo docker system prune -af

# 3. Pull Latest Images
echo "⬇️ Pulling latest Docker images..."
sudo docker compose -f docker-compose.prod.yml pull

# 4. Set Deployment Metadata
export GIT_COMMIT_HASH=$(git rev-parse --short HEAD)
export DEPLOY_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "ℹ️  Deploying version: $GIT_COMMIT_HASH at $DEPLOY_TIMESTAMP"

# 5. Restart Services
echo "🔄 Restarting services..."
sudo -E docker compose -f docker-compose.prod.yml up -d

echo "✅ Deployment completed successfully!"
echo "   - Version: $GIT_COMMIT_HASH"
echo "   - Timestamp: $DEPLOY_TIMESTAMP"
