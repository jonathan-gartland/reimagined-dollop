#!/bin/bash
# Stop all Airflow services

set -e

cd "$(dirname "$0")"

echo "Stopping Airflow Docker services..."
docker compose down

echo "Airflow services stopped."
