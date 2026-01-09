# Airflow DAGs

This directory contains Apache Airflow DAG definitions for automating the whiskey data sync workflow.

## DAG: whiskey_sync_dag.py

Automates the complete data pipeline:
1. Sync Google Sheets → PostgreSQL
2. Export PostgreSQL → TypeScript (catalog-beta)
3. Git commit with conventional commit message
4. Git push to GitHub

## Setup

The DAG file is symlinked to the Airflow dags folder:
```
~/airflow/dags/whiskey_sync_dag.py -> /Users/jonny/Projects/liquor_app/dags/whiskey_sync_dag.py
```

This follows Airflow best practices by keeping the DAG version-controlled with the project code it orchestrates.

## Running the DAG

```bash
# Quick run (recommended)
cd ~/airflow && ./run-dag.sh

# Or via Airflow web UI
# Start services: ~/airflow/start-airflow.sh {scheduler|webserver}
# Access: http://localhost:8080
```

## Configuration

- **Schedule**: Manual trigger only (no automatic schedule)
- **Target Branch**: Configured in the DAG file (currently: main)
- **Retry Logic**: 2 retries per task, 30-second delay
- **Idempotency**: Skips commit/push if no data changes

## Documentation

See `~/airflow/README.md` for complete Airflow documentation.
