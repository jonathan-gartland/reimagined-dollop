#!/bin/bash
# Deploy liquor_app to remote Airflow server
#
# Usage:
#   ./deploy-to-remote.sh LINODE_IP
#
# Example:
#   ./deploy-to-remote.sh 97.107.138.118

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 LINODE_IP"
    echo "Example: $0 97.107.138.118"
    exit 1
fi

SERVER="root@$1"
REPO_URL="git@github.com:jonathan-gartland/reimagined-dollop.git"

echo "=== Deploying liquor_app to $SERVER ==="

# SSH and run deployment commands
ssh "$SERVER" << 'ENDSSH'
set -e

echo "Step 1: Clone/update repository..."
if [ -d ~/liquor_app ]; then
    echo "  Repository exists, pulling latest changes..."
    cd ~/liquor_app
    git pull
else
    echo "  Cloning repository..."
    cd ~
    git clone git@github.com:jonathan-gartland/reimagined-dollop.git liquor_app
fi

echo "Step 2: Copy DAG files to Airflow dags directory..."
cd ~/airflow

# Remove old files
rm -f dags/whiskey_sync_dag.py
rm -f dags/README.md

# Copy DAG files (Docker can't follow symlinks across mounts)
cp ~/liquor_app/dags/whiskey_sync_dag.py dags/
cp ~/liquor_app/dags/README.md dags/

echo "Step 3: Configure environment variables..."
# Set LIQUOR_APP_DIR in .env if not already set
if ! grep -q "LIQUOR_APP_DIR" .env 2>/dev/null; then
    echo "LIQUOR_APP_DIR=/root/liquor_app" >> .env
    echo "  Added LIQUOR_APP_DIR to .env"
else
    echo "  LIQUOR_APP_DIR already configured"
fi

echo "Step 4: Verify files..."
ls -la dags/ | grep whiskey

echo "Step 5: Restart Airflow to pick up changes..."
cd ~/airflow
docker compose down
docker compose up -d

echo ""
echo "=== Deployment Complete ==="
echo "DAG should appear in UI within 30 seconds"
echo "Access: http://$(curl -s ifconfig.me):8080"

ENDSSH

echo ""
echo "✓ Deployed successfully!"
echo "Check the Airflow UI for your DAG"
