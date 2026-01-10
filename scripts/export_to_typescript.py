#!/usr/bin/env python3
"""
Export PostgreSQL liquor database to TypeScript format
Generates the whiskey-data.ts file for the Next.js catalog app
"""

import psycopg2
import os
import json
from datetime import date

# Database configuration
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'liquor_db'),
    'user': os.environ.get('DB_USER', 'jonny'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432')
}

# Output file path (relative to scripts/ directory)
OUTPUT_FILE = '../../catalog-beta/src/data/whiskey-data.ts'

def format_value(value, field_type='string'):
    """Format a value for TypeScript output"""
    if value is None:
        if field_type == 'string':
            return '""'
        elif field_type == 'number':
            return '0'
        else:
            return 'null'

    if field_type == 'string':
        # Escape quotes and backslashes
        escaped = str(value).replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    elif field_type == 'number':
        return str(value)
    elif field_type == 'date':
        if isinstance(value, date):
            return f'"{value.strftime("%-m/%-d/%Y")}"'
        return f'"{value}"'

    return str(value)

def export_to_typescript():
    """Export database to TypeScript file"""

    print("=" * 60)
    print("Export PostgreSQL to TypeScript")
    print("=" * 60)

    try:
        print("\nStep 1: Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Step 2: Querying data...")
        cur.execute("""
            SELECT
                name,
                count,
                country_of_origin,
                category_style,
                region,
                distillery,
                age,
                purchased_approx,
                abv,
                volume,
                price_cost,
                opened_closed,
                errata,
                replacement_cost
            FROM liquor
            ORDER BY name
        """)

        rows = cur.fetchall()
        print(f"Found {len(rows):,} records")

        print("\nStep 3: Generating TypeScript file...")

        # Build TypeScript content
        ts_content = """import { WhiskeyBottle } from '@/types/whiskey';

export const whiskeyCollection: WhiskeyBottle[] = [
"""

        for i, row in enumerate(rows):
            (name, count, country, type_, region, distillery, age,
             purchase_date, abv, volume, price_cost, status, errata,
             replacement_cost) = row

            # Set defaults for missing values
            quantity = count if count is not None else 1
            purchase_price = price_cost if price_cost is not None else 0
            current_value = replacement_cost if replacement_cost is not None else purchase_price

            # Build the object
            ts_content += "  {\n"
            ts_content += f"    name: {format_value(name, 'string')},\n"
            ts_content += f"    quantity: {quantity},\n"
            ts_content += f"    country: {format_value(country, 'string')},\n"
            ts_content += f"    type: {format_value(type_, 'string')},\n"
            ts_content += f"    region: {format_value(region, 'string')},\n"
            ts_content += f"    distillery: {format_value(distillery, 'string')},\n"
            ts_content += f"    age: {format_value(age, 'string')},\n"
            ts_content += f"    purchaseDate: {format_value(purchase_date, 'date')},\n"
            ts_content += f"    abv: {format_value(abv, 'number')},\n"
            ts_content += f"    size: {format_value(volume, 'string')},\n"
            ts_content += f"    purchasePrice: {format_value(purchase_price, 'number')},\n"
            ts_content += f"    status: {format_value(status, 'string')},\n"
            ts_content += f"    batch: {format_value(errata, 'string')},\n"
            ts_content += f"    notes: \"\",\n"
            ts_content += f"    currentValue: {format_value(current_value, 'number')}"

            # Add replacementCost if it exists
            if replacement_cost is not None:
                ts_content += f",\n    replacementCost: {format_value(replacement_cost, 'number')}"

            ts_content += "\n  }"

            # Add comma if not last item
            if i < len(rows) - 1:
                ts_content += ","

            ts_content += "\n"

        ts_content += "];\n"

        # Write to file
        output_path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ts_content)

        print(f"\n✓ Successfully exported to {OUTPUT_FILE}")
        print(f"  Total records: {len(rows):,}")

        cur.close()
        conn.close()

        print("\n" + "=" * 60)
        print("Export completed successfully!")
        print("=" * 60)

        return True

    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
        return False

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    export_to_typescript()
