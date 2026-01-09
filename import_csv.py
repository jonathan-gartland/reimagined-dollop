#!/usr/bin/env python3
"""
Import liquor data from CSV to PostgreSQL database
"""

import csv
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'liquor_db'),
    'user': os.environ.get('DB_USER', 'jonny'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432')
}

CSV_FILE = 'Liquor - Sheet1.csv'

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

def import_csv_to_postgres():
    """Import CSV data into PostgreSQL"""

    print(f"Connecting to database: {DB_CONFIG['dbname']} at {DB_CONFIG['host']}:{DB_CONFIG['port']}")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print(f"Reading CSV file: {CSV_FILE}")

        # Read CSV file
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Prepare data for batch insert
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

        print(f"Inserting {len(data)} records into database...")

        # Batch insert using execute_values for better performance
        insert_query = """
            INSERT INTO liquor (
                name, count, country_of_origin, category_style, region, distillery,
                age, purchased_approx, abv, volume, price_cost, opened_closed,
                errata, replacement_cost
            ) VALUES %s
        """

        execute_values(cur, insert_query, data)

        # Commit the transaction
        conn.commit()

        # Get count
        cur.execute("SELECT COUNT(*) FROM liquor")
        count = cur.fetchone()[0]

        print(f"✓ Successfully imported {count} liquor items to the database")

        # Close connection
        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: CSV file '{CSV_FILE}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import_csv_to_postgres()
