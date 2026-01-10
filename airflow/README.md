# Airflow Docker Setup

This directory contains the Docker Compose configuration for running Apache Airflow to automate the whiskey data sync workflow.

## Quick Start

### 1. Build and Start Airflow

```bash
cd /Users/jonny/Projects/liquor_app/airflow

# Build the custom Docker image (includes git)
docker-compose build

# Initialize the database and create admin user
docker-compose up airflow-init

# Start all Airflow services
docker-compose up -d
```

### 2. Access the Web UI

Open http://localhost:8080 in your browser.

**Credentials:**
- Username: `admin`
- Password: `admin`

### 3. Trigger the DAG

1. In the Airflow UI, find the `whiskey_data_sync` DAG
2. Click the play button (▶) to trigger it manually
3. Monitor the execution in the Graph or Gantt view

## What the DAG Does

The `whiskey_data_sync` DAG automates the complete workflow:

1. **sync_google_sheets_to_postgres** - Downloads data from Google Sheets and imports to PostgreSQL
2. **export_postgres_to_typescript** - Exports PostgreSQL data to TypeScript file in catalog-beta
3. **check_for_git_changes** - Checks if the TypeScript file changed (idempotency check)
4. **git_commit_changes** - Commits changes with conventional commit message (skipped if no changes)
5. **git_push_to_remote** - Pushes to GitHub (skipped if no changes)

## Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f airflow-scheduler

# Restart services
docker-compose restart

# Rebuild image after changes
docker-compose build
docker-compose up -d --force-recreate

# Clean up everything (WARNING: deletes database and logs)
docker-compose down -v
```

## Architecture

The Docker setup includes:

- **postgres** - PostgreSQL database for Airflow metadata
- **redis** - Message broker for CeleryExecutor
- **airflow-apiserver** - Airflow Web UI (port 8080)
- **airflow-scheduler** - Schedules and monitors DAG runs
- **airflow-dag-processor** - Processes DAG files
- **airflow-worker** - Executes tasks
- **airflow-triggerer** - Handles deferred tasks
- **airflow-init** - One-time initialization service

## Volume Mounts

The Docker containers mount these directories from your host:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `../dags/` | `/opt/airflow/dags` | DAG definitions |
| `../scripts/` | `/opt/airflow/scripts` | Python scripts |
| `../sql/` | `/opt/airflow/sql` | SQL files |
| `../logs/` | `/opt/airflow/logs` | Execution logs |
| `../config/` | `/opt/airflow/config` | Configuration files |
| `../plugins/` | `/opt/airflow/plugins` | Custom plugins |
| `../../catalog-beta/` | `/catalog-beta` | Next.js app repository |
| `~/.ssh/` | `/home/airflow/.ssh` | SSH keys for git push |

## Environment Variables

Configuration is stored in `.env` file. Key variables:

- `AIRFLOW_UID` - User ID for file permissions (default: 501)
- `DB_HOST` - PostgreSQL host for liquor_db (use `host.docker.internal` to connect to host machine)
- `CATALOG_BETA_PATH` - Path to catalog-beta repository
- `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` - Git commit attribution
- `_PIP_ADDITIONAL_REQUIREMENTS` - Python packages to install (psycopg2-binary, python-dotenv)

## Custom Docker Image

The setup uses a custom Dockerfile to extend the official Airflow image with:

- **git** - For committing and pushing changes
- **openssh-client** - For SSH authentication with GitHub
- **psycopg2-binary** - PostgreSQL adapter for Python
- **python-dotenv** - Environment variable loading

## Connecting to Host PostgreSQL

The DAG needs to connect to your local PostgreSQL database (`liquor_db`). Docker uses `host.docker.internal` to access services on the host machine:

```bash
# Verify PostgreSQL is accessible
psql -d liquor_db -c "SELECT COUNT(*) FROM liquor"

# Check PostgreSQL is listening on all interfaces (needed for Docker)
psql -d postgres -c "SHOW listen_addresses"
# Should show: 'localhost' or '*'

# If needed, edit postgresql.conf:
# listen_addresses = 'localhost'
```

## SSH Keys for Git Push

The Docker containers mount your SSH keys (`~/.ssh/`) to enable git push. Ensure:

1. SSH key is loaded in ssh-agent:
   ```bash
   ssh-add -l  # Should show your key
   ```

2. Key has access to the GitHub repository

3. GitHub host key is trusted (first-time setup):
   ```bash
   docker-compose exec airflow-worker ssh -T git@github.com
   # Accept the host key fingerprint
   ```

## Troubleshooting

### Web UI shows "502 Bad Gateway"

Wait 1-2 minutes for all services to start. Check status:
```bash
docker-compose ps
docker-compose logs airflow-apiserver
```

### Permission errors on mounted volumes

Set the correct `AIRFLOW_UID` in `.env`:
```bash
echo "AIRFLOW_UID=$(id -u)" >> .env
docker-compose down
docker-compose up -d
```

### DAG can't connect to PostgreSQL

1. Verify PostgreSQL is running on host:
   ```bash
   psql -d liquor_db -c "SELECT 1"
   ```

2. Check PostgreSQL accepts connections from Docker:
   ```bash
   docker-compose exec airflow-worker psql -h host.docker.internal -U jonny -d liquor_db -c "SELECT 1"
   ```

3. If connection fails, check `pg_hba.conf` allows connections from Docker network

### Git push fails with "permission denied"

1. Check SSH keys are mounted:
   ```bash
   docker-compose exec airflow-worker ls -la /home/airflow/.ssh
   ```

2. Test SSH connection:
   ```bash
   docker-compose exec airflow-worker ssh -T git@github.com
   ```

3. Verify key permissions:
   ```bash
   chmod 600 ~/.ssh/id_*
   chmod 644 ~/.ssh/id_*.pub
   ```

### DAG shows "Import Errors"

Check the logs:
```bash
docker-compose logs airflow-scheduler | grep ERROR
```

Common issues:
- Missing Python dependencies → Add to `_PIP_ADDITIONAL_REQUIREMENTS` in `.env`
- Path issues → Verify volume mounts in `docker-compose.yaml`
- Environment variables → Check `.env` file configuration

## Resource Requirements

Minimum system requirements:
- **Memory**: 4 GB (8 GB recommended)
- **CPU**: 2 cores
- **Disk**: 10 GB free space

Check Docker resources:
```bash
docker stats
```

Adjust in Docker Desktop: Settings → Resources

## Upgrading Airflow

To upgrade to a newer Airflow version:

1. Update `AIRFLOW_IMAGE_NAME` in `.env`:
   ```bash
   AIRFLOW_IMAGE_NAME=apache/airflow:3.2.0
   ```

2. Rebuild and restart:
   ```bash
   docker-compose build
   docker-compose down
   docker-compose up -d
   ```

## Cleaning Up

To completely remove Airflow (keeps your DAGs and scripts):
```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove custom image
docker rmi liquor_app-airflow-common
```

## Production Deployment

This Docker setup is for **local development only**. For production:

1. Use a managed service (AWS MWAA, Google Cloud Composer, Astronomer)
2. Or deploy with Kubernetes using Airflow Helm Chart
3. Configure secrets management (not environment variables)
4. Enable authentication and SSL
5. Set up monitoring and alerting
6. Configure auto-scaling for workers

See: https://airflow.apache.org/docs/apache-airflow/stable/production-deployment.html

## References

- [Running Airflow in Docker](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Airflow Configuration Reference](https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html)
