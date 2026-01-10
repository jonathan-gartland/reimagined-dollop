# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based data pipeline that syncs whiskey collection data from Google Sheets to PostgreSQL and exports to TypeScript for a Next.js web app. The project is fully containerized with Docker and includes optional Airflow automation for scheduled syncing with automatic git commits.

## Technology Stack

- **Language**: Python 3.12 (containerized)
- **Database**: PostgreSQL (host machine)
- **Containerization**: Docker Compose
- **Automation**: Apache Airflow 3.1.5 (Docker)
- **Data Source**: Google Sheets (public CSV export)
- **Target**: Next.js app in sibling `catalog-beta` directory

## Development Commands

### Docker (Recommended - No Python Required)

```bash
# Data Operations
./docker-run.sh sync      # Full sync: Google Sheets → PostgreSQL
./docker-run.sh export    # Export PostgreSQL → TypeScript
./docker-run.sh download  # Download CSV only
./docker-run.sh import    # Import CSV only

# Database Operations
psql -d liquor_db                          # Connect to database
psql -d liquor_db -f sql/queries.sql       # Run example queries
pg_dump -d liquor_db -f backup.sql         # Backup database

# Airflow Automation
cd airflow && ./start.sh                   # Start all Airflow services
cd airflow && ./stop.sh                    # Stop all services
docker compose logs -f                     # View logs
# UI: http://localhost:8080 (admin/admin)

# Container Management
cd airflow && docker compose ps            # View running containers
cd airflow && docker compose build         # Rebuild images
```

### Local Python (Alternative)

```bash
# Setup
pip install -r requirements.txt
psql -d liquor_db -f sql/schema.sql

# Run Scripts
python3 scripts/sync_from_sheets.py
python3 scripts/export_to_typescript.py
```

## Architecture

### Data Flow

```
Google Sheets (Public Spreadsheet)
    ↓
[download_from_sheets.py] → CSV File
    ↓
[import_csv.py] → PostgreSQL (liquor_db)
    ↓
[export_to_typescript.py] → catalog-beta/src/data/whiskey-data.ts
    ↓
Next.js Web App (catalog-beta)
```

### Docker Architecture

```
liquor-app container (Python 3.12)
├── Runs sync/export scripts
├── Connects to host PostgreSQL via host.docker.internal
└── Mounts catalog-beta for TypeScript export

Airflow containers (optional automation)
├── airflow-apiserver (Web UI :8080)
├── airflow-scheduler (DAG orchestration)
├── airflow-worker (task execution)
├── airflow-dag-processor (DAG parsing)
├── airflow-triggerer (deferred tasks)
├── postgres (Airflow metadata)
└── redis (message broker)
```

### Sync Process

**Full refresh workflow** (not incremental):

1. **Download**: Fetches CSV from Google Sheets public export URL
2. **Parse**: Transforms data types (dates → DATE, prices → NUMERIC, etc.)
3. **Truncate**: Clears existing PostgreSQL table
4. **Batch Insert**: Uses `execute_values` for fast bulk import
5. **Export**: Generates TypeScript file with camelCase column mapping
6. **Commit** (Airflow only): Auto-commits and pushes to GitHub if changes detected

**Key Behavior**: Every sync completely replaces the database to ensure consistency with Google Sheets.

### Google Sheets Configuration

- **Spreadsheet ID**: `1plsSjVwRABsIbpjZGsxBXWpLV4hAGPRTFFlJOV4guFk`
- **Sheet ID (gid)**: `0` (first sheet)
- **Access**: Must be publicly accessible ("Anyone with the link can view")
- **Export URL**: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_ID}`

### Database Configuration

**Database**: `liquor_db`
**Table**: `liquor`

Environment variables are loaded from `.env` file:
```bash
# Copy .env.example to .env and configure
DB_NAME=liquor_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

**Security Note:** The `.env` file is gitignored. For production deployment, set these as GitHub secrets or environment variables. See `GITHUB_SECRETS.md` for details.

## Column Mapping

Google Sheets → PostgreSQL:

| Google Sheets Column | PostgreSQL Column   | Type         | Parser Function  |
|---------------------|---------------------|--------------|------------------|
| name                | name                | TEXT         | parse_value()    |
| count               | count               | INTEGER      | parse_integer()  |
| Country of Origin   | country_of_origin   | TEXT         | parse_value()    |
| category/style      | category_style      | TEXT         | parse_value()    |
| region              | region              | TEXT         | parse_value()    |
| distillery          | distillery          | TEXT         | parse_value()    |
| age                 | age                 | TEXT         | parse_value()    |
| purchased approx    | purchased_approx    | DATE         | parse_date()     |
| ABV                 | abv                 | NUMERIC(5,2) | parse_numeric()  |
| volume              | volume              | TEXT         | parse_value()    |
| price (cost)        | price_cost          | NUMERIC(10,2)| parse_numeric()  |
| Opened/Closed       | opened_closed       | TEXT         | parse_value()    |
| errata              | errata              | TEXT         | parse_value()    |
| Replacement Cost    | replacement_cost    | NUMERIC(10,2)| parse_numeric()  |

Additional database columns (auto-generated):
- `id` - Serial primary key
- `created_at` - Timestamp (default: now)
- `updated_at` - Timestamp (auto-updates on row changes)

## Data Parsing

### Parser Functions

All parser functions handle empty values (`''`, `None`, `'-'`) by returning `None`:

- **parse_value()**: Returns string as-is or None
- **parse_integer()**: Converts to integer or None
- **parse_numeric()**: Removes `$` and `,`, converts to float or None
- **parse_date()**: Tries multiple date formats (`%m/%d/%Y`, `%Y-%m-%d`, etc.)

### Error Handling

- Empty rows (no name) are skipped
- Invalid values return None instead of failing
- Database operations are transactional (commit or rollback)
- HTTP 404 errors indicate spreadsheet access issues

## Project Structure

```
liquor_app/
├── scripts/                   # Python scripts
│   ├── download_from_sheets.py    # Download CSV from Google Sheets
│   ├── import_csv.py              # Import CSV to PostgreSQL
│   ├── sync_from_sheets.py        # Complete sync workflow (download + import)
│   └── export_to_typescript.py    # Export PostgreSQL to TypeScript data file
├── dags/                      # Airflow DAGs
│   ├── whiskey_sync_dag.py        # Airflow DAG definition
│   └── README.md                  # DAG documentation
├── sql/                       # SQL files
│   ├── schema.sql                 # Database schema with indexes
│   └── queries.sql                # Example SQL queries
├── airflow/                   # Airflow Docker setup
│   ├── docker-compose.yaml        # Docker Compose configuration
│   ├── Dockerfile                 # Custom Airflow image (with git)
│   ├── .env                       # Airflow environment variables (gitignored)
│   ├── .gitignore                 # Airflow-specific ignores
│   ├── start.sh                   # Start Airflow services
│   ├── stop.sh                    # Stop Airflow services
│   └── README.md                  # Airflow documentation
├── logs/                      # Airflow logs (generated, gitignored)
├── config/                    # Airflow config (generated, gitignored)
├── plugins/                   # Airflow plugins (empty, gitignored)
├── docs/                      # Documentation
│   └── ENVIRONMENT_SETUP.md       # Environment variables guide
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Local config (gitignored, create from .env.example)
├── Dockerfile                 # Docker image for liquor_app scripts
├── docker-run.sh              # Helper script to run containerized commands
├── .gitignore                 # Git ignore rules
├── GITHUB_SECRETS.md          # Guide for production secrets
├── DOCKER.md                  # Docker setup guide
├── CLAUDE.md                  # Project guide for Claude Code
├── README.md                  # Detailed setup instructions
└── Liquor - Sheet1.csv        # Downloaded CSV file (generated, gitignored)
```

## Integration with catalog-beta

**Purpose**: Exports PostgreSQL data as TypeScript for the Next.js web app

**Export Process**:
- Target: `../catalog-beta/src/data/whiskey-data.ts`
- Column mapping: snake_case → camelCase (e.g., `country_of_origin` → `country`)
- Date format: PostgreSQL DATE → `M/D/YYYY` string
- Null handling: Empty strings for text, 0 for numbers
- Output: `whiskeyCollection` array of `WhiskeyBottle` objects

**Path Detection**:
- Docker: Uses `/catalog-beta` (mounted volume)
- Local: Uses `../../catalog-beta` (relative path)
- Auto-detects environment via `os.path.exists('/catalog-beta')`

**Workflow**:
1. Edit Google Sheets
2. Run `./docker-run.sh sync` → Updates PostgreSQL
3. Run `./docker-run.sh export` → Generates TypeScript
4. (Optional) Airflow DAG does all steps + git commit/push

## Common Workflows

### Initial Setup

```bash
# 1. Create database and schema
createdb liquor_db
psql -d liquor_db -f sql/schema.sql

# 2. First sync (Docker)
./docker-run.sh sync

# 3. Export to catalog-beta
./docker-run.sh export

# 4. (Optional) Start Airflow
cd airflow && ./start.sh
```

### Manual Sync

```bash
# Sync only
./docker-run.sh sync

# Sync + Export
./docker-run.sh sync && ./docker-run.sh export
```

### Scheduled Automation

Use Airflow (recommended) or cron:

```bash
# Airflow: Web UI → Trigger whiskey_data_sync DAG
# Or edit schedule in dags/whiskey_sync_dag.py

# Cron alternative:
crontab -e
# Add: 0 2 * * * cd /path/to/liquor_app && ./docker-run.sh sync && ./docker-run.sh export
```

### Airflow Automation (Optional)

**Purpose**: Automates the complete workflow with git commit/push

**DAG Flow** (`whiskey_data_sync`):
1. `sync_google_sheets_to_postgres` - Downloads and imports data
2. `export_postgres_to_typescript` - Generates TypeScript file
3. `check_for_git_changes` - Detects if file changed (idempotency)
4. `git_commit_changes` - Creates conventional commit (skipped if no changes)
5. `git_push_to_remote` - Pushes to GitHub (skipped if no changes)

**Quick Start:**
```bash
cd airflow
./start.sh                    # Start all services
# Open http://localhost:8080 (admin/admin)
# Click play button on whiskey_data_sync DAG
./stop.sh                     # Stop when done
```

**Configuration:**
- Manual trigger only (set `schedule=None` in DAG)
- To enable scheduled runs: Change schedule parameter (e.g., `schedule='0 2 * * *'` for daily 2 AM)
- Environment: `airflow/.env` (gitignored)
- DAG definition: `dags/whiskey_sync_dag.py`

**Requirements:**
- Docker Desktop running
- PostgreSQL on host (accessible via `host.docker.internal`)
- SSH key for GitHub push (~/.ssh/ mounted in containers)
- catalog-beta at `/Users/jonny/Projects/catalog-beta`

### Changing Spreadsheet ID

Edit the constants in all three Python files:
```python
SPREADSHEET_ID = 'your_new_spreadsheet_id'
SHEET_ID = '0'  # or your sheet's gid
```

### Database Queries

The `sql/queries.sql` file contains useful examples:
- Total bottles and investment value
- Collection breakdown by country, type, distillery
- Most valuable bottles
- Unopened bottles list
- Regional analysis

## Troubleshooting

**"Spreadsheet not found or not publicly accessible"**
- Check that the spreadsheet is shared with "Anyone with the link can view"
- Verify SPREADSHEET_ID and SHEET_ID are correct

**"Database error: connection refused"**
- Ensure PostgreSQL is running: `brew services start postgresql@15`
- Check DB_HOST and DB_PORT environment variables

**"CSV file not found"**
- Run `download_from_sheets.py` first, or use `sync_from_sheets.py` instead

**Date parsing issues**
- Check that dates in the spreadsheet use supported formats
- Add new format to `parse_date()` function if needed

## Database Schema

Key indexes for performance:
- `idx_liquor_name` - Name lookups
- `idx_liquor_distillery` - Distillery filtering
- `idx_liquor_category` - Category/type filtering
- `idx_liquor_country` - Country grouping
- `idx_liquor_opened_closed` - Status filtering

Auto-trigger:
- `updated_at` column automatically updates on row changes
