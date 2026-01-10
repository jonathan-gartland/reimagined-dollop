#!/usr/bin/env python3
"""
Download liquor data from Google Sheets as CSV
"""

import urllib.request
import urllib.error
import os
import sys

# Google Sheets configuration
SPREADSHEET_ID = '1plsSjVwRABsIbpjZGsxBXWpLV4hAGPRTFFlJOV4guFk'
SHEET_ID = '0'  # gid from the URL
OUTPUT_FILE = 'Liquor - Sheet1.csv'

def download_google_sheet_as_csv():
    """Download Google Sheet as CSV using export URL"""

    # Construct the CSV export URL
    # Format: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_ID}
    url = f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_ID}'

    print(f"Downloading from Google Sheets...")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"Sheet ID: {SHEET_ID}")

    try:
        # Download the CSV
        with urllib.request.urlopen(url) as response:
            csv_data = response.read()

        # Save to file
        with open(OUTPUT_FILE, 'wb') as f:
            f.write(csv_data)

        # Get file size
        file_size = os.path.getsize(OUTPUT_FILE)

        # Count lines
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f) - 1  # Subtract header row

        print(f"✓ Successfully downloaded {OUTPUT_FILE}")
        print(f"  File size: {file_size:,} bytes")
        print(f"  Records: {line_count:,}")

        return True

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: Spreadsheet not found or not publicly accessible")
            print(f"Make sure the spreadsheet is shared with 'Anyone with the link can view'")
        else:
            print(f"HTTP Error {e.code}: {e.reason}")
        return False

    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        print("Check your internet connection")
        return False

    except Exception as e:
        print(f"Error downloading spreadsheet: {e}")
        return False

if __name__ == '__main__':
    success = download_google_sheet_as_csv()
    sys.exit(0 if success else 1)
