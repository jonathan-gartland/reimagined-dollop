#!/bin/bash
# Start all Airflow services in Docker

set -e

cd "$(dirname "$0")"

echo "Starting Airflow Docker services..."
docker compose up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 5

echo ""
echo "Service status:"
docker compose ps

echo ""
echo "Airflow Web UI: http://localhost:8080"
echo "Username: admin"
echo "Password: admin"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
