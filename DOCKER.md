# Docker Setup

This project can run entirely in Docker containers, eliminating the need for local Python installation or environment setup.

## Architecture

The project uses Docker Compose to manage two main setups:

1. **liquor_app** - The Python application for syncing data
2. **Airflow** - Workflow automation (optional)

## Quick Start

### Running Scripts in Docker

```bash
# Full sync: Google Sheets → PostgreSQL
./docker-run.sh sync

# Export PostgreSQL → TypeScript
./docker-run.sh export

# Download CSV from Google Sheets only
./docker-run.sh download

# Import CSV to PostgreSQL only
./docker-run.sh import
```

These commands use the `liquor-app` container to run the Python scripts without needing Python installed on your host machine.

## Container Details

### liquor-app Container

**Image**: Built from `Dockerfile` in project root

**Includes**:
- Python 3.12
- PostgreSQL client tools
- psycopg2-binary for database access
- All Python scripts from `scripts/` directory

**Environment Variables** (from `airflow/.env`):
- `DB_NAME` - PostgreSQL database name (default: liquor_db)
- `DB_USER` - PostgreSQL username (default: jonny)
- `DB_PASSWORD` - PostgreSQL password (default: empty)
- `DB_HOST` - PostgreSQL host (default: host.docker.internal)
- `DB_PORT` - PostgreSQL port (default: 5432)

**Volume Mounts**:
- `./scripts` → `/app/scripts` - Python scripts
- `./sql` → `/app/sql` - SQL files
- `../catalog-beta` → `/catalog-beta` - TypeScript export destination

### Manual Docker Commands

If you prefer to use Docker commands directly:

```bash
cd airflow

# Start the container
docker compose up -d liquor-app

# Run sync
docker compose exec liquor-app python3 scripts/sync_from_sheets.py

# Run export
docker compose exec liquor-app python3 scripts/export_to_typescript.py

# View logs
docker compose logs liquor-app

# Stop the container
docker compose stop liquor-app
```

## Building the Image

The image is automatically built when you run `./docker-run.sh` for the first time. To rebuild manually:

```bash
cd airflow
docker compose build liquor-app
```

## Connecting to Host PostgreSQL

The container needs to connect to PostgreSQL running on your host machine. It uses `host.docker.internal` as the hostname, which Docker automatically resolves to your host's IP address.

**Verify PostgreSQL is accessible:**
```bash
# From inside the container
docker compose exec liquor-app psql -h host.docker.internal -U jonny -d liquor_db -c "SELECT COUNT(*) FROM liquor"
```

If this fails, check:
1. PostgreSQL is running: `brew services list | grep postgres`
2. PostgreSQL is accepting connections on localhost
3. PostgreSQL user credentials are correct in `airflow/.env`

## Standalone Usage (Without Airflow)

You can use just the liquor_app container without the full Airflow setup:

```bash
cd airflow

# Edit docker-compose.yaml to only include liquor-app service, or:
docker compose up -d liquor-app
docker compose exec liquor-app python3 scripts/sync_from_sheets.py
```

## Advantages of Docker Approach

✅ **No Local Dependencies** - No need to install Python, pip, or Python packages on your machine

✅ **Consistent Environment** - Same Python version and dependencies everywhere

✅ **Easy Cleanup** - Remove containers when done, no lingering packages

✅ **Portable** - Works the same on macOS, Linux, Windows (with Docker)

✅ **Isolated** - Doesn't interfere with system Python or other projects

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs liquor-app

# Rebuild image
docker compose build --no-cache liquor-app
```

### Can't connect to PostgreSQL

```bash
# Test connection from container
docker compose exec liquor-app python3 -c "
import psycopg2
import os
conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME', 'liquor_db'),
    user=os.getenv('DB_USER', 'jonny'),
    password=os.getenv('DB_PASSWORD', ''),
    host=os.getenv('DB_HOST', 'host.docker.internal'),
    port=os.getenv('DB_PORT', '5432')
)
print('✓ Connected successfully')
"
```

### Scripts not updating

The scripts directory is mounted as a volume, so changes to scripts on your host are immediately reflected in the container. No rebuild needed.

### Export file not created

Check that catalog-beta is mounted correctly:
```bash
docker compose exec liquor-app ls -la /catalog-beta/src/data/
```

If the directory doesn't exist, check the `CATALOG_BETA_HOST_PATH` in `airflow/.env`.

## Cleanup

```bash
# Stop and remove container
cd airflow
docker compose down liquor-app

# Remove image
docker rmi airflow-liquor-app

# Remove all Airflow services (optional)
docker compose down -v
```
