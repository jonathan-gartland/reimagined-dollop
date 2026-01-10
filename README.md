# Liquor Collection Database

PostgreSQL database for managing a liquor collection, imported from a Google Sheets spreadsheet.

## Database Schema

The database contains a single `liquor` table with the following columns:

- `id` - Auto-incrementing primary key
- `name` - Liquor name (required)
- `count` - Quantity/number of bottles
- `country_of_origin` - Country where produced
- `category_style` - Type (Bourbon, Scotch, etc.)
- `region` - Geographic region of production
- `distillery` - Distillery/producer name
- `age` - Age statement (e.g., "10y", "18yr")
- `purchased_approx` - Approximate purchase date
- `abv` - Alcohol by volume percentage
- `volume` - Bottle size (e.g., "750ml")
- `price_cost` - Purchase price
- `opened_closed` - Status (opened/unopened)
- `errata` - Notes, batch info, special details
- `replacement_cost` - Current replacement/market value
- `created_at` - Record creation timestamp
- `updated_at` - Record update timestamp (auto-updated)

## Setup

### Prerequisites

- PostgreSQL 12 or higher
- Python 3.7 or higher
- psycopg2 Python library

### Installation

1. Install PostgreSQL if not already installed:
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Check if PostgreSQL is running
psql --version
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create the database:
```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE liquor_db;

# Exit psql
\q
```

4. Create the schema:
```bash
psql -d liquor_db -f sql/schema.sql
```

5. Import the CSV data:
```bash
# Set database credentials (optional, defaults shown)
export DB_NAME=liquor_db
export DB_USER=jonny
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432

# Run import script
python3 scripts/import_csv.py
```

## Syncing with Google Sheets

The database can be synchronized with your Google Sheets spreadsheet to keep it up-to-date.

### Prerequisites for Sync

The Google Sheets spreadsheet must be publicly accessible:
1. Open your spreadsheet in Google Sheets
2. Click "Share" in the top-right
3. Change to "Anyone with the link can view"

### Sync Commands (Docker - Recommended)

```bash
# Full sync: Google Sheets → PostgreSQL
./docker-run.sh sync

# Download CSV only
./docker-run.sh download

# Import CSV to PostgreSQL only
./docker-run.sh import

# Export PostgreSQL → TypeScript
./docker-run.sh export
```

### Sync Commands (Local Python - Alternative)

```bash
# One-time sync: Download latest data and update database
python3 scripts/sync_from_sheets.py

# Download CSV only (without updating database)
python3 scripts/download_from_sheets.py
```

### Automatic Sync

To automatically sync on a schedule, set up a cron job:

```bash
# Edit crontab
crontab -e

# Add this line to sync daily at 2 AM
0 2 * * * cd /Users/jonny/Projects/liquor_app && /usr/bin/python3 scripts/sync_from_sheets.py >> sync.log 2>&1

# Or sync every hour
0 * * * * cd /Users/jonny/Projects/liquor_app && /usr/bin/python3 scripts/sync_from_sheets.py >> sync.log 2>&1
```

**Note:** The sync script performs a full refresh (clears and re-imports all data) to ensure the database exactly matches the spreadsheet.

## Usage

### Connect to the database

```bash
psql -d liquor_db
```

### Example Queries

```sql
-- Count total bottles
SELECT SUM(count) as total_bottles FROM liquor;

-- Collection overview by country
SELECT country_of_origin, SUM(count) as bottles, SUM(price_cost * count) as total_value
FROM liquor
GROUP BY country_of_origin
ORDER BY bottles DESC;

-- Find all unopened bottles
SELECT name, distillery, age, replacement_cost, opened_closed
FROM liquor
WHERE opened_closed = 'unopened'
ORDER BY replacement_cost DESC;

-- Search for specific distillery
SELECT name, count, age, abv, price_cost, opened_closed
FROM liquor
WHERE distillery ILIKE '%heaven hill%'
ORDER BY name;

-- Find all bourbon
SELECT name, distillery, age, price_cost
FROM liquor
WHERE category_style ILIKE '%bourbon%'
ORDER BY distillery, name;

-- Most valuable bottles
SELECT name, distillery, replacement_cost, price_cost,
       replacement_cost - price_cost as appreciation
FROM liquor
WHERE replacement_cost IS NOT NULL
ORDER BY replacement_cost DESC
LIMIT 10;

-- Total investment analysis
SELECT
    SUM(count) as total_bottles,
    SUM(price_cost * count) as total_spent,
    SUM(replacement_cost * count) as current_value,
    SUM(replacement_cost * count) - SUM(price_cost * count) as appreciation
FROM liquor;

-- Bottles by region (for Scotch)
SELECT region, SUM(count) as bottles
FROM liquor
WHERE category_style ILIKE '%scotch%'
GROUP BY region
ORDER BY bottles DESC;
```

## Database Management

### Backup

```bash
pg_dump -d liquor_db -f liquor_backup_$(date +%Y%m%d).sql
```

### Restore

```bash
psql -d liquor_db -f liquor_backup_YYYYMMDD.sql
```

### Export data to CSV

```bash
psql -d liquor_db -c "\COPY liquor TO 'liquor_export.csv' CSV HEADER"
```

## File Structure

```
liquor_app/
├── scripts/                        # Python scripts
│   ├── download_from_sheets.py        # Download CSV from Google Sheets
│   ├── import_csv.py                  # Import CSV to PostgreSQL
│   ├── sync_from_sheets.py            # Sync database with Google Sheets
│   └── export_to_typescript.py        # Export PostgreSQL to TypeScript
├── sql/                            # SQL files
│   ├── schema.sql                     # Database schema definition
│   └── queries.sql                    # Useful example queries
├── dags/                           # Airflow DAGs (optional)
│   ├── whiskey_sync_dag.py            # Automated workflow DAG
│   └── README.md                      # DAG documentation
├── docs/                           # Documentation
│   └── ENVIRONMENT_SETUP.md           # Environment variables guide
├── requirements.txt                # Python dependencies
├── .env.example                    # Database configuration template
├── .env                            # Local config (gitignored)
├── .gitignore                      # Git ignore rules
├── GITHUB_SECRETS.md               # Production deployment guide
├── CLAUDE.md                       # Project guide for Claude Code
├── README.md                       # This file
└── Liquor - Sheet1.csv             # Downloaded CSV file (generated)
```
