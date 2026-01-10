#!/bin/bash
# Run liquor_app scripts in Docker container
#
# Usage:
#   ./docker-run.sh sync              # Run full sync (Google Sheets → PostgreSQL)
#   ./docker-run.sh export            # Export PostgreSQL → TypeScript
#   ./docker-run.sh download          # Download CSV from Google Sheets only
#   ./docker-run.sh import            # Import CSV to PostgreSQL only

set -e

cd "$(dirname "$0")/airflow"

# Ensure liquor-app container is running
if ! docker compose ps liquor-app | grep -q "Up"; then
    echo "Starting liquor-app container..."
    docker compose up -d liquor-app
    sleep 2
fi

SCRIPT=""
case "$1" in
    sync)
        SCRIPT="scripts/sync_from_sheets.py"
        echo "Running full sync: Google Sheets → PostgreSQL"
        ;;
    export)
        SCRIPT="scripts/export_to_typescript.py"
        echo "Exporting: PostgreSQL → TypeScript"
        ;;
    download)
        SCRIPT="scripts/download_from_sheets.py"
        echo "Downloading CSV from Google Sheets"
        ;;
    import)
        SCRIPT="scripts/import_csv.py"
        echo "Importing CSV to PostgreSQL"
        ;;
    *)
        echo "Usage: $0 {sync|export|download|import}"
        echo ""
        echo "Commands:"
        echo "  sync     - Full sync: Google Sheets → PostgreSQL"
        echo "  export   - Export PostgreSQL → TypeScript"
        echo "  download - Download CSV from Google Sheets only"
        echo "  import   - Import CSV to PostgreSQL only"
        exit 1
        ;;
esac

echo ""
docker compose exec liquor-app python3 "$SCRIPT"
