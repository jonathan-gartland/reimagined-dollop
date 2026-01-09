"""
Whiskey Data Sync DAG
Automates the complete workflow: Google Sheets → PostgreSQL → TypeScript → Git commit/push
"""

from datetime import datetime, timedelta
import subprocess
import os
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import ShortCircuitOperator
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the parent directory of the dags folder
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Project paths (from environment variables)
LIQUOR_APP_PATH = os.getenv('LIQUOR_APP_PATH', '/Users/jonny/Projects/liquor_app')
CATALOG_BETA_PATH = os.getenv('CATALOG_BETA_PATH', '/Users/jonny/Projects/catalog-beta')
DATA_FILE_PATH = 'src/data/whiskey-data.ts'

# Git environment variables for commit attribution (from .env)
GIT_ENV = {
    'GIT_AUTHOR_NAME': os.getenv('GIT_AUTHOR_NAME', 'Airflow'),
    'GIT_AUTHOR_EMAIL': os.getenv('GIT_AUTHOR_EMAIL', 'airflow@localhost'),
    'GIT_COMMITTER_NAME': os.getenv('GIT_COMMITTER_NAME', 'Airflow'),
    'GIT_COMMITTER_EMAIL': os.getenv('GIT_COMMITTER_EMAIL', 'airflow@localhost'),
    # Ensure Node.js is in PATH for git hooks (husky/commitlint)
    'PATH': '/opt/homebrew/bin:/usr/local/bin:' + os.environ.get('PATH', ''),
}

# DAG default arguments
default_args = {
    'owner': os.getenv('AIRFLOW_DAG_OWNER', 'airflow'),
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=30),
}

# Define the DAG
with DAG(
    dag_id='whiskey_data_sync',
    default_args=default_args,
    description='Sync whiskey collection from Google Sheets to PostgreSQL and catalog-beta',
    schedule=None,  # Manual trigger only
    start_date=datetime(2026, 1, 1),  # Fixed start date
    catchup=False,
    tags=['whiskey', 'data-sync', 'manual'],
) as dag:

    # Task 1: Download from Google Sheets and sync to PostgreSQL
    sync_to_database = BashOperator(
        task_id='sync_google_sheets_to_postgres',
        bash_command=f'cd {LIQUOR_APP_PATH} && python3 sync_from_sheets.py',
        cwd=LIQUOR_APP_PATH,
    )

    # Task 2: Export PostgreSQL to TypeScript
    export_to_typescript = BashOperator(
        task_id='export_postgres_to_typescript',
        bash_command=f'cd {LIQUOR_APP_PATH} && python3 export_to_typescript.py',
        cwd=LIQUOR_APP_PATH,
    )

    # Task 3: Check if git changes exist (idempotency check)
    def check_git_changes():
        """
        Returns True if changes exist, False if no changes.
        This prevents empty commits when data hasn't changed.
        """
        result = subprocess.run(
            ['git', 'diff', '--quiet', DATA_FILE_PATH],
            cwd=CATALOG_BETA_PATH,
            capture_output=True
        )
        # git diff --quiet returns 0 if no changes, 1 if changes exist
        has_changes = result.returncode != 0

        if has_changes:
            print(f"✓ Git changes detected in {DATA_FILE_PATH}")
        else:
            print(f"✗ No changes in {DATA_FILE_PATH}, skipping commit/push")

        return has_changes

    check_changes = ShortCircuitOperator(
        task_id='check_for_git_changes',
        python_callable=check_git_changes,
        ignore_downstream_trigger_rules=False,
    )

    # Task 4: Git add and commit
    git_commit = BashOperator(
        task_id='git_commit_changes',
        bash_command=f'''
            cd {CATALOG_BETA_PATH} && \\
            git add {DATA_FILE_PATH} && \\
            git commit -m "chore: sync whiskey data from Google Sheets [$(date +%Y-%m-%d)]"
        ''',
        env={**os.environ.copy(), **GIT_ENV},
        cwd=CATALOG_BETA_PATH,
    )

    # Task 5: Git push to remote
    git_push = BashOperator(
        task_id='git_push_to_remote',
        bash_command=f'cd {CATALOG_BETA_PATH} && git push origin test-airflow-sync-2',
        cwd=CATALOG_BETA_PATH,
    )

    # Define task dependencies
    sync_to_database >> export_to_typescript >> check_changes >> git_commit >> git_push
