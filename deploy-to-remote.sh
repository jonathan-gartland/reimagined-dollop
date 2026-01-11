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

echo "Step 2: Create symlinks to Airflow directories..."
cd ~/airflow

# Remove old symlinks/files if they exist
rm -f dags/whiskey_sync_dag.py
rm -f dags/README.md

# Symlink DAG files to Airflow dags directory
ln -sf ~/liquor_app/dags/whiskey_sync_dag.py dags/whiskey_sync_dag.py
ln -sf ~/liquor_app/dags/README.md dags/README.md

# Symlink scripts directory (if not already mounted in docker-compose)
if [ ! -L scripts ]; then
    rm -rf scripts
    ln -sf ~/liquor_app/scripts scripts
fi

echo "Step 3: Verify symlinks..."
ls -la dags/
ls -la scripts/

echo "Step 4: Restart Airflow to pick up changes..."
cd ~/airflow
docker compose restart airflow-scheduler airflow-dag-processor

echo ""
echo "=== Deployment Complete ==="
echo "DAG should appear in UI within 30 seconds"
echo "Access: http://$(curl -s ifconfig.me):8080"

ENDSSH

echo ""
echo "✓ Deployed successfully!"
echo "Check the Airflow UI for your DAG"
