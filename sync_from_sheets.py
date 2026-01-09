#!/usr/bin/env python3
"""
Sync liquor database with Google Sheets
Downloads latest CSV from Google Sheets and updates the database
"""

import csv
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
import urllib.request
import urllib.error
from datetime import datetime

# Google Sheets configuration
SPREADSHEET_ID = '1plsSjVwRABsIbpjZGsxBXWpLV4hAGPRTFFlJOV4guFk'
SHEET_ID = '0'
CSV_FILE = 'Liquor - Sheet1.csv'

# Database configuration
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'liquor_db'),
    'user': os.environ.get('DB_USER', 'jonny'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432')
}

def parse_value(value):
    """Parse a value from CSV, returning None for empty strings"""
    if value == '' or value is None or value == '-':
        return None
    return value

def parse_numeric(value):
    """Parse numeric value, handling empty strings, dollar signs, and commas"""
    if value == '' or value is None or value == '-':
        return None
    # Remove dollar signs and commas
    cleaned = value.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def parse_integer(value):
    """Parse integer value, handling empty strings"""
    if value == '' or value is None or value == '-':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def parse_date(value):
    """Parse date value, handling various formats"""
    if value == '' or value is None or value == '-':
        return None

    # Try various date formats
    formats = ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y', '%d/%m/%Y']

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue

    return None

def download_from_google_sheets():
    """Download Google Sheet as CSV"""
    url = f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_ID}'

    print("Step 1: Downloading latest data from Google Sheets...")

    try:
        with urllib.request.urlopen(url) as response:
            csv_data = response.read()

        with open(CSV_FILE, 'wb') as f:
            f.write(csv_data)

        print(f"✓ Downloaded {CSV_FILE}")
        return True

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("Error: Spreadsheet not found or not publicly accessible")
            print("Make sure the spreadsheet is shared with 'Anyone with the link can view'")
        else:
            print(f"HTTP Error {e.code}: {e.reason}")
        return False

    except Exception as e:
        print(f"Error downloading spreadsheet: {e}")
        return False

def sync_to_database():
    """Sync CSV data to PostgreSQL database"""

    print(f"\nStep 2: Connecting to database...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Get current count before sync
        cur.execute("SELECT COUNT(*) FROM liquor")
        old_count = cur.fetchone()[0]

        print(f"Current database records: {old_count:,}")
        print(f"\nStep 3: Reading CSV file...")

        # Read CSV file
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            data = []
            for row in reader:
                # Skip rows with no name (empty rows)
                name = parse_value(row['name'])
                if not name:
                    continue

                data.append((
                    name,
                    parse_integer(row['count']),
                    parse_value(row['Country of Origin']),
                    parse_value(row['category/style']),
                    parse_value(row['region']),
                    parse_value(row['distillery']),
                    parse_value(row['age']),
                    parse_date(row['purchased approx']),
                    parse_numeric(row['ABV']),
                    parse_value(row['volume']),
                    parse_numeric(row['price (cost)']),
                    parse_value(row['Opened/Closed']),
                    parse_value(row['errata']),
                    parse_numeric(row.get('Replacement Cost'))
                ))

        print(f"CSV records to import: {len(data):,}")

        print(f"\nStep 4: Syncing database...")
        print("  - Clearing old data...")

        # Clear existing data
        cur.execute("TRUNCATE TABLE liquor RESTART IDENTITY")

        print("  - Inserting new data...")

        # Batch insert new data
        insert_query = """
            INSERT INTO liquor (
                name, count, country_of_origin, category_style, region, distillery,
                age, purchased_approx, abv, volume, price_cost, opened_closed,
                errata, replacement_cost
            ) VALUES %s
        """

        execute_values(cur, insert_query, data)

        # Commit transaction
        conn.commit()

        # Get new count
        cur.execute("SELECT COUNT(*) FROM liquor")
        new_count = cur.fetchone()[0]

        print(f"\n✓ Sync complete!")
        print(f"  Old records: {old_count:,}")
        print(f"  New records: {new_count:,}")
        print(f"  Difference: {new_count - old_count:+,}")

        cur.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False

    except FileNotFoundError:
        print(f"Error: CSV file '{CSV_FILE}' not found")
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main sync workflow"""
    print("=" * 60)
    print("Liquor Database Sync")
    print("=" * 60)

    # Download latest data
    if not download_from_google_sheets():
        print("\n✗ Sync failed: Could not download from Google Sheets")
        sys.exit(1)

    # Sync to database
    if not sync_to_database():
        print("\n✗ Sync failed: Could not update database")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Sync completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()
