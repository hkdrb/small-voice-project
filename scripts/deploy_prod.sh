#!/bin/bash
set -e

# Deployment Script for Small Voice Project Production

echo "🚀 Starting deployment process..."

# 1. Update Codebase
echo "📥 Pulling latest changes from git..."
git pull origin main

# 1.5 Clean up docker system
echo "🧹 Cleaning up unused Docker images..."
docker system prune -af

# 2. Pull Latest Images
echo "⬇️ Pulling latest Docker images..."
docker compose -f docker-compose.prod.yml pull

# 3. Set Deployment Metadata in .env file directly
GIT_COMMIT_HASH=$(git rev-parse --short HEAD)
DEPLOY_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "ℹ️  Deploying version: $GIT_COMMIT_HASH at $DEPLOY_TIMESTAMP"

# Function to update or append env var in .env file
update_env() {
    local key=$1
    local value=$2
    if grep -q "^$key=" .env; then
        # Use a temporary file to avoid issues with sed in-place editing on some systems
        sed "s|^$key=.*|$key=\"$value\"|" .env > .env.tmp && mv .env.tmp .env
    else
        echo "$key=\"$value\"" >> .env
    fi
}

echo "📝 Updating .env file with deployment metadata..."
update_env "GIT_COMMIT_HASH" "$GIT_COMMIT_HASH"
update_env "DEPLOY_TIMESTAMP" "$DEPLOY_TIMESTAMP"

# 4. Restart Services
echo "🔄 Restarting services..."
# Now we don't need sudo -E or sudo env, because the values are in the .env file
docker compose -f docker-compose.prod.yml up -d

echo "✅ Deployment completed successfully!"
echo "   - Version: $GIT_COMMIT_HASH"
echo "   - Timestamp: $DEPLOY_TIMESTAMP"
