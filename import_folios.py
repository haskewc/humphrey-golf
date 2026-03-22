#!/usr/bin/env python3
"""
Golf Ball Folio Import Script
Imports Folios II, III, and IV into the golf_balls_v2.db database
"""

import pandas as pd
import sqlite3
import re
import os
from pathlib import Path

# Configuration
DB_PATH = '/home/humphrey/.openclaw/workspace/projects/humphrey-golf/golf_balls_v2.db'
FOLIOS_DIR = '/home/humphrey/.openclaw/workspace/kevin_files/folios'

# Column mapping for each folio (normalized names)
COLUMN_MAPPINGS = {
    2: {  # Folio II - Rubber-Core 1903-1920
        '#': 'record_no',
        'BALL NAME': 'ball_name',
        'BALL NAME FORMAT': 'ball_name_format',
        'ERA': 'era',
        'COVER\nPATTERN': 'cover_pattern',
        'WEIGHTS, DIMENSIONS,\nSPECIFICATIONS & CHARACTERISTICS': 'specs',
        ' PATENTS, DESIGNS, CONSTRUCTION & LEGAL ': 'patents_legal',
        'MANUFACTURER,\nMAKER & ADDRESS': 'manufacturer',
        'AUCTION RESULTS &\nVALUATION REMARKS': 'auction_remarks',
        'VALUE £': 'value_raw',
        'NOTES NICK': 'notes',
    },
    3: {  # Folio III - Wound 1920-1945
        'No.': 'record_no',
        'BALL NAME': 'ball_name',
        'BALL NAME FORMAT': 'ball_name_format',
        'ERA': 'era',
        'COVER PATTERN': 'cover_pattern',
        'WEIGHTS, DIMENSIONS, SPECIFICATIONS & CHARACTERISTICS': 'specs',
        ' PATENTS, DESIGNS, \nCONSTRUCTION & PHOTO REFERENCES ': 'patents_legal',
        'MANUFACTURER,\nMAKER & ADDRESS': 'manufacturer',
        'AUCTION RESULTS &\nVALUATION REMARKS': 'auction_remarks',
        'VALUE': 'value_raw',
        'BALL PHOTO ?': 'notes',
    },
    4: {  # Folio IV - Post-War 1945-1970
        'No.': 'record_no',
        'BALL NAME': 'ball_name',
        'BALL NAME FORMAT': 'ball_name_format',
        'ERA': 'era',
        'COVER PATTERN': 'cover_pattern',
        'WEIGHTS, DIMENSIONS,\nSPECIFICATIONS & CHARACTERISTICS': 'specs',
        'PATENTS, DESIGNS,\nCONSTRUCTION & LEGAL ': 'patents_legal',
        'MANUFACTURER/\nRETAILER & ADDRESS': 'manufacturer',
        'AUCTION RESULTS &\nVALUATION REMARKS': 'auction_remarks',
        'VALUE £': 'value_raw',
        'nick NOTES': 'notes',
    }
}


def normalize_column_names(df, folio_num):
    """Normalize column names by removing newlines and standardizing"""
    # Create a mapping for this specific folio
    mapping = COLUMN_MAPPINGS[folio_num]
    
    # Rename columns
    df = df.rename(columns=mapping)
    
    return df


def parse_era(era_str):
    """Parse era string into era_start, era_end, era_sort"""
    if pd.isna(era_str) or era_str == '':
        return None, None, None
    
    era_str = str(era_str).strip().upper()
    
    # Handle specific patterns
    patterns = [
        # "Late 1910s", "Early 1920s", "Mid 1930s"
        (r'^(EARLY|MID|LATE)\s+(\d{2})0S$', lambda m: (int(m.group(2)) * 100, int(m.group(2)) * 100 + 49 if m.group(1) == 'EARLY' else (int(m.group(2)) * 100 + 50 if m.group(1) == 'MID' else int(m.group(2)) * 100 + 99))),
        # "1910s", "1920s"
        (r'^(\d{4})S$', lambda m: (int(m.group(1)), int(m.group(1)) + 9)),
        # "1906", "1910" - exact year
        (r'^(\d{4})$', lambda m: (int(m.group(1)), int(m.group(1)))),
        # "1906-1910", "1906/1910"
        (r'^(\d{4})[-/](\d{4})$', lambda m: (int(m.group(1)), int(m.group(2)))),
        # "1900s" - decade
        (r'^(\d{3})0S$', lambda m: (int(m.group(1)) * 10, int(m.group(1)) * 10 + 9)),
    ]
    
    for pattern, extractor in patterns:
        match = re.match(pattern, era_str)
        if match:
            start, end = extractor(match)
            # For era_sort, use the start year
            return start, end, start
    
    # Default: try to extract any 4-digit year
    years = re.findall(r'\d{4}', era_str)
    if years:
        year = int(years[0])
        return year, year, year
    
    return None, None, None


def parse_value(value_str):
    """Parse value string into value_low, value_high, value_mid, currency"""
    if pd.isna(value_str) or value_str == '':
        return None, None, None, 'GBP'  # Default to GBP for folios II-IV
    
    value_str = str(value_str).strip()
    
    # Detect currency
    currency = 'GBP'
    if '$' in value_str or 'USD' in value_str or value_str.startswith('$'):
        currency = 'USD'
    elif '£' in value_str:
        currency = 'GBP'
    
    # Remove currency symbols and whitespace
    value_str = value_str.replace('£', '').replace('$', '').replace('USD', '').strip()
    
    # Handle ranges like "50/35.00", "300/400", "£300/350"
    if '/' in value_str:
        parts = value_str.split('/')
        if len(parts) == 2:
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                # Handle case where high is written as "35.00" when low is "50" (i.e., 50/35 should be 35/50)
                if high < low:
                    low, high = high, low
                mid = (low + high) / 2
                return low, high, mid, currency
            except ValueError:
                pass
    
    # Handle ranges with dash
    if '-' in value_str:
        parts = value_str.split('-')
        if len(parts) == 2:
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                mid = (low + high) / 2
                return low, high, mid, currency
            except ValueError:
                pass
    
    # Single value
    try:
        val = float(value_str.replace(',', ''))
        return val, val, val, currency
    except ValueError:
        pass
    
    return None, None, None, currency


def clean_cover_pattern(pattern):
    """Clean cover pattern by stripping ASSUMPTION: prefixes"""
    if pd.isna(pattern) or pattern == '':
        return None
    
    pattern = str(pattern).strip()
    
    # Remove ASSUMPTION: prefix
    if pattern.upper().startswith('ASSUMPTION:'):
        pattern = pattern[11:].strip()
    
    # Normalize newlines
    pattern = pattern.replace('\n', ' ').replace('  ', ' ')
    
    return pattern


def extract_country(manufacturer_str):
    """Extract country from manufacturer string"""
    if pd.isna(manufacturer_str):
        return 'Unknown'
    
    manufacturer_str = str(manufacturer_str).upper()
    
    # Check for country indicators
    if 'SCOTLAND' in manufacturer_str or 'EDINBURGH' in manufacturer_str or 'GLASGOW' in manufacturer_str or 'ST ANDREWS' in manufacturer_str or 'FIFE' in manufacturer_str:
        return 'Scotland'
    elif 'ENGLAND' in manufacturer_str or 'LONDON' in manufacturer_str or 'LIVERPOOL' in manufacturer_str or 'MANCHESTER' in manufacturer_str:
        return 'England'
    elif 'USA' in manufacturer_str or 'AMERICA' in manufacturer_str or 'OHIO' in manufacturer_str or 'MASSACHUSETTS' in manufacturer_str or 'NEW YORK' in manufacturer_str:
        return 'USA'
    elif 'IRELAND' in manufacturer_str or 'BELFAST' in manufacturer_str or 'DUBLIN' in manufacturer_str:
        return 'Ireland'
    elif 'FRANCE' in manufacturer_str or 'PARIS' in manufacturer_str:
        return 'France'
    elif 'GERMANY' in manufacturer_str:
        return 'Germany'
    elif 'JAPAN' in manufacturer_str:
        return 'Japan'
    elif 'AUSTRALIA' in manufacturer_str:
        return 'Australia'
    
    return 'Unknown'


def process_folio(folio_num, file_name):
    """Process a single folio Excel file"""
    print(f"\n{'='*60}")
    print(f"Processing Folio {folio_num}: {file_name}")
    print('='*60)
    
    # Read Excel file
    file_path = os.path.join(FOLIOS_DIR, file_name)
    df = pd.read_excel(file_path)
    
    print(f"Raw rows: {len(df)}")
    print(f"Raw columns: {list(df.columns)}")
    
    # Normalize column names
    df = normalize_column_names(df, folio_num)
    
    # Add folio column
    df['folio'] = folio_num
    
    # Parse era
    print("Parsing eras...")
    era_data = df['era'].apply(parse_era)
    df['era_start'] = era_data.apply(lambda x: x[0] if x else None)
    df['era_end'] = era_data.apply(lambda x: x[1] if x else None)
    df['era_sort'] = era_data.apply(lambda x: x[2] if x else None)
    
    # Parse values
    print("Parsing values...")
    value_data = df['value_raw'].apply(parse_value)
    df['value_low'] = value_data.apply(lambda x: x[0] if x else None)
    df['value_high'] = value_data.apply(lambda x: x[1] if x else None)
    df['value_mid'] = value_data.apply(lambda x: x[2] if x else None)
    df['currency'] = value_data.apply(lambda x: x[3] if x else 'GBP')
    
    # Clean cover pattern
    print("Cleaning cover patterns...")
    df['cover_pattern'] = df['cover_pattern'].apply(clean_cover_pattern)
    
    # Extract country
    print("Extracting countries...")
    df['country'] = df['manufacturer'].apply(extract_country)
    
    # Set default condition_grade and rarity_score
    df['condition_grade'] = None
    df['rarity_score'] = 0
    
    # Clean up text fields - replace NaN with None
    text_columns = ['ball_name', 'ball_name_format', 'era', 'cover_pattern', 
                   'manufacturer', 'specs', 'patents_legal', 'auction_remarks']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: None if pd.isna(x) else str(x).strip())
    
    # Ensure record_no is integer
    df['record_no'] = pd.to_numeric(df['record_no'], errors='coerce')
    
    # Remove rows with null record_no
    df = df[df['record_no'].notna()]
    
    print(f"Processed rows: {len(df)}")
    
    return df


def update_database_schema():
    """Add folio column to database if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if folio column exists
    cursor.execute("PRAGMA table_info(golf_balls)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'folio' not in columns:
        print("Adding folio column to database...")
        cursor.execute("ALTER TABLE golf_balls ADD COLUMN folio INTEGER DEFAULT 1")
        cursor.execute("UPDATE golf_balls SET folio = 1 WHERE folio IS NULL")
        conn.commit()
        print("Schema updated successfully")
    else:
        print("Folio column already exists")
    
    conn.close()


def import_to_database(df, folio_num):
    """Import processed dataframe to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get max record_no to avoid conflicts (folio balls get new record numbers)
    cursor.execute("SELECT MAX(record_no) FROM golf_balls")
    max_record = cursor.fetchone()[0] or 0
    
    # For folios 2-4, we'll add to the existing records with new record numbers
    # This preserves the original folio I data
    
    records_imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            max_record += 1
            
            cursor.execute("""
                INSERT INTO golf_balls (
                    record_no, ball_name, ball_name_format, era, era_start, era_end, era_sort,
                    cover_pattern, manufacturer, specs, patents_legal, auction_remarks,
                    condition_grade, value_raw, value_low, value_high, value_mid, currency,
                    country, rarity_score, folio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                max_record,
                row.get('ball_name'),
                row.get('ball_name_format'),
                row.get('era'),
                row.get('era_start'),
                row.get('era_end'),
                row.get('era_sort'),
                row.get('cover_pattern'),
                row.get('manufacturer'),
                row.get('specs'),
                row.get('patents_legal'),
                row.get('auction_remarks'),
                row.get('condition_grade'),
                row.get('value_raw'),
                row.get('value_low'),
                row.get('value_high'),
                row.get('value_mid'),
                row.get('currency'),
                row.get('country'),
                row.get('rarity_score', 0),
                folio_num  # Set the folio number
            ))
            records_imported += 1
            
        except Exception as e:
            errors.append(f"Row {idx}: {e}")
    
    conn.commit()
    conn.close()
    
    return records_imported, errors


def validate_import():
    """Validate the import results"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM golf_balls")
    total = cursor.fetchone()[0]
    print(f"\nTotal balls in database: {total}")
    print(f"Expected: 551 (Folio I) + 1,193 (Folio II) + 1,177 (Folio III) + 1,515 (Folio IV) = 4,436")
    
    # Count by folio
    cursor.execute("SELECT folio, COUNT(*) FROM golf_balls GROUP BY folio ORDER BY folio")
    folio_counts = cursor.fetchall()
    print(f"\nBalls per folio:")
    for folio, count in folio_counts:
        print(f"  Folio {folio}: {count}")
    
    # Check era_sort values
    cursor.execute("SELECT MIN(era_sort), MAX(era_sort) FROM golf_balls WHERE era_sort IS NOT NULL")
    era_range = cursor.fetchone()
    print(f"\nEra sort range: {era_range[0]} to {era_range[1]}")
    
    # Sample records from each folio
    print("\nSample records:")
    for folio in [1, 2, 3, 4]:
        cursor.execute("""
            SELECT record_no, ball_name, era, value_mid, currency, country 
            FROM golf_balls 
            WHERE folio = ? 
            LIMIT 2
        """, (folio,))
        samples = cursor.fetchall()
        print(f"\n  Folio {folio} samples:")
        for s in samples:
            print(f"    {s}")
    
    conn.close()
    
    return total


def main():
    print("GOLF BALL FOLIO IMPORT")
    print("="*60)
    
    # Update schema
    update_database_schema()
    
    # Process each folio
    folios = [
        (2, 'folio_II.xlsx'),
        (3, 'folio_III.xlsx'),
        (4, 'folio_IV.xlsx'),
    ]
    
    import_stats = {}
    
    for folio_num, file_name in folios:
        try:
            # Process the folio
            df = process_folio(folio_num, file_name)
            
            # Import to database
            print(f"Importing to database...")
            imported, errors = import_to_database(df, folio_num)
            
            import_stats[folio_num] = {
                'processed': len(df),
                'imported': imported,
                'errors': len(errors)
            }
            
            print(f"Successfully imported {imported} records")
            if errors:
                print(f"Errors: {len(errors)}")
                for err in errors[:5]:  # Show first 5 errors
                    print(f"  {err}")
                
        except Exception as e:
            print(f"ERROR processing Folio {folio_num}: {e}")
            import_stats[folio_num] = {
                'processed': 0,
                'imported': 0,
                'errors': 1,
                'error_msg': str(e)
            }
    
    # Validate
    total = validate_import()
    
    # Summary report
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"\nFolio I (existing): 551 balls")
    for folio_num in [2, 3, 4]:
        stats = import_stats.get(folio_num, {})
        print(f"Folio {folio_num}: {stats.get('imported', 0)} balls imported")
    print(f"\nTotal in database: {total}")
    print(f"Expected total: 4,436")
    print(f"Difference: {total - 4436}")
    
    return import_stats


if __name__ == '__main__':
    main()
