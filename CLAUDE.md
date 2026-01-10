# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based data pipeline that downloads whiskey collection data from Google Sheets and syncs it to a PostgreSQL database. This project serves as the data source for the Next.js web application in the sibling `catalog-beta` directory.

## Technology Stack

- **Language**: Python 3.7+
- **Database**: PostgreSQL 12+
- **Dependencies**: psycopg2-binary (PostgreSQL adapter), python-dotenv (environment variables)
- **Data Source**: Google Sheets (publicly accessible spreadsheet)
- **Automation**: Apache Airflow 3.0.6 (optional, for automated syncing)

## Development Commands

### Docker (Recommended)

```bash
# Data Operations (containerized - no Python install needed)
./docker-run.sh sync      # Full sync: Google Sheets → PostgreSQL
./docker-run.sh export    # Export PostgreSQL → TypeScript
./docker-run.sh download  # Download CSV from Google Sheets only
./docker-run.sh import    # Import CSV to PostgreSQL only
```

### Local Python (Alternative)

```bash
# Setup
pip install -r requirements.txt             # Install Python dependencies
psql -d liquor_db -f sql/schema.sql        # Create database schema

# Data Operations
python3 scripts/download_from_sheets.py    # Download CSV from Google Sheets only
python3 scripts/import_csv.py              # Import existing CSV to database
python3 scripts/sync_from_sheets.py        # Full sync: download + import
python3 scripts/export_to_typescript.py    # Export PostgreSQL to catalog-beta TypeScript file
```

# Database Operations
psql -d liquor_db                          # Connect to database
psql -d liquor_db -f sql/queries.sql       # Run example queries
pg_dump -d liquor_db -f backup.sql         # Backup database

# Airflow Operations (Docker - Recommended)
cd /Users/jonny/Projects/liquor_app/airflow && ./start.sh  # Start all services
cd /Users/jonny/Projects/liquor_app/airflow && ./stop.sh   # Stop all services
docker compose logs -f                                      # View logs
# Access UI: http://localhost:8080 (admin/admin)
# Trigger: whiskey_data_sync DAG (manual trigger button)
```

## Architecture

### Data Flow

```
Google Sheets (Public)
    ↓ (download_from_sheets.py)
CSV File (Liquor - Sheet1.csv)
    ↓ (import_csv.py)
PostgreSQL (liquor_db)
    ↓ (export_to_typescript.py)
catalog-beta/src/data/whiskey-data.ts (Next.js app)
```

### Sync Process

The `sync_from_sheets.py` script performs a complete end-to-end sync:

1. **Download**: Fetches CSV export from Google Sheets using public export URL
2. **Parse**: Reads CSV and transforms data types (dates, numbers, etc.)
3. **Refresh**: Truncates existing database table
4. **Import**: Batch inserts all rows using `execute_values` for performance
5. **Report**: Shows before/after record counts

**Important**: This is a full refresh, not an incremental sync. The database is cleared and rebuilt on each run.

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

## Relationship to catalog-beta

The **catalog-beta** project (Next.js web app) uses this data via a TypeScript data file (`src/data/whiskey-data.ts`). The workflow to update the web app is:

1. Update Google Sheets with new bottles
2. Run `python3 sync_from_sheets.py` to update PostgreSQL
3. Run `python3 export_to_typescript.py` to generate the TypeScript data file

**Export Details**:
- The export script queries PostgreSQL and generates a TypeScript file at `../catalog-beta/src/data/whiskey-data.ts`
- Column mapping: PostgreSQL snake_case → TypeScript camelCase (e.g., `country_of_origin` → `country`, `price_cost` → `purchasePrice`)
- The TypeScript file exports a `whiskeyCollection` array conforming to the `WhiskeyBottle` interface
- Empty/null values are handled appropriately (empty strings for text, 0 for numbers)
- Date formatting: Converts PostgreSQL dates to `M/D/YYYY` format for consistency with the web app

## Common Tasks

### Initial Setup

```bash
# 1. Create database
createdb liquor_db

# 2. Create schema
psql -d liquor_db -f sql/schema.sql

# 3. First sync
python3 scripts/sync_from_sheets.py
```

### Regular Syncing

```bash
# One-time sync to PostgreSQL
python3 scripts/sync_from_sheets.py

# Full sync to PostgreSQL and export to Next.js app
python3 scripts/sync_from_sheets.py && python3 scripts/export_to_typescript.py

# Or set up cron for automatic syncing (example: daily at 2 AM)
crontab -e
# Add: 0 2 * * * cd /Users/jonny/Projects/liquor_app && python3 scripts/sync_from_sheets.py && python3 scripts/export_to_typescript.py >> sync.log 2>&1
```

### Automated Syncing with Airflow (Recommended)

Apache Airflow automates the complete workflow including git commit/push:

**What It Does:**
1. Syncs Google Sheets → PostgreSQL
2. Exports PostgreSQL → TypeScript (catalog-beta)
3. Commits changes with conventional commit message
4. Pushes to GitHub automatically
5. Skips commit/push if no data changes (idempotency)

**Start Airflow (Docker):**
```bash
cd /Users/jonny/Projects/liquor_app/airflow
./start.sh                    # Starts all services in Docker
```

**Access Web UI:**
- URL: http://localhost:8080
- Username: `admin`
- Password: `admin`

**Trigger Sync:**
- Open http://localhost:8080
- Find `whiskey_data_sync` DAG
- Click the "Play" button (▶) to trigger manually
- Monitor execution in Graph view

**Stop Airflow:**
```bash
cd /Users/jonny/Projects/liquor_app/airflow
./stop.sh                     # Stops all services
```

**Configuration:**
- Docker setup: `airflow/docker-compose.yaml`
- Environment variables: `airflow/.env` (gitignored)
- DAG file: `dags/whiskey_sync_dag.py`
- Airflow documentation: `airflow/README.md`
- Currently set to manual trigger only (no automatic schedule)
- To enable scheduled runs: Edit `schedule=None` in the DAG file

**Requirements:**
- Docker Desktop installed and running
- PostgreSQL running on host machine
- SSH key loaded for GitHub push
- catalog-beta repository at `/Users/jonny/Projects/catalog-beta`

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
