"""
Import Folio 2, 3, and 4 Excel data into the golf_balls_v2.db database.
"""
import sqlite3
import re
import openpyxl


def parse_era(era_text):
    """Parse era text into era_start, era_end, era_sort values."""
    if era_text is None:
        return None, None, None

    era_text = str(era_text).strip().replace('\n', ' ')

    # Direct year like "1910", "1935", 1940
    m = re.match(r'^(\d{4})$', era_text)
    if m:
        year = int(m.group(1))
        return year, year, year

    # "Early 1910s", "Late 1910s", "Mid 1920s"
    m = re.match(r'(Early|Mid|Late)\s+(\d{4})s', era_text, re.IGNORECASE)
    if m:
        prefix = m.group(1).lower()
        decade = int(m.group(2))
        if prefix == 'early':
            start, end, sort = decade, decade + 3, decade
        elif prefix == 'mid':
            start, end, sort = decade + 4, decade + 6, decade + 5
        else:  # late
            start, end, sort = decade + 7, decade + 9, decade + 8
        return start, end, sort

    # "1920s", "1930s", "1940s"
    m = re.match(r'^(\d{4})s$', era_text)
    if m:
        decade = int(m.group(1))
        return decade, decade + 9, decade + 5

    # "Late 1930s / Early 1940s" or "Late 1930s /\nEarly 1940s"
    m = re.match(r'(Early|Mid|Late)\s+(\d{4})s\s*/\s*(Early|Mid|Late)\s+(\d{4})s', era_text, re.IGNORECASE)
    if m:
        decade1 = int(m.group(2))
        decade2 = int(m.group(4))
        return decade1 + 7, decade2 + 3, decade1 + 8

    # "1920s / 1930s"
    m = re.match(r'(\d{4})s\s*/\s*(\d{4})s', era_text)
    if m:
        d1, d2 = int(m.group(1)), int(m.group(2))
        return d1, d2 + 9, d1 + 5

    # Just return the year if it's a number
    try:
        year = int(float(era_text))
        return year, year, year
    except (ValueError, TypeError):
        pass

    return None, None, None


def parse_value(val_text):
    """Parse value field. Returns (value_raw, value_low, value_high, value_mid, currency)."""
    if val_text is None:
        return None, None, None, None, None

    val_str = str(val_text).strip().replace('\n', ' ').replace(',', '')
    # Clean up common typos in values
    val_str = re.sub(r'\.{2,}', '.', val_str)  # ".." -> "."
    val_str = re.sub(r'\.(\D|$)', r'\1', val_str.rstrip('.'))  # trailing dots

    # Plain number (USD)
    try:
        v = float(val_str)
        return val_str, v, v, v, 'USD'
    except ValueError:
        pass

    # "£50/35.00" or "£60/40.00" format - GBP/USD, use USD
    m = re.match(r'£\s*([\d.]+)\s*/\s*£?\s*([\d.]+)', val_str)
    if m:
        gbp = float(m.group(1))
        usd = float(m.group(2))
        return val_str, usd, usd, usd, 'USD'

    # "£50" just GBP
    m = re.match(r'£\s*([\d.]+)', val_str)
    if m:
        gbp = float(m.group(1))
        return val_str, gbp, gbp, gbp, 'GBP'

    # "$300" USD
    m = re.match(r'\$\s*([\d.]+)', val_str)
    if m:
        usd = float(m.group(1))
        return val_str, usd, usd, usd, 'USD'

    # Range like "200-500"
    m = re.match(r'([\d.]+)\s*-\s*([\d.]+)', val_str)
    if m:
        low, high = float(m.group(1)), float(m.group(2))
        return val_str, low, high, (low + high) / 2, 'USD'

    return val_str, None, None, None, None


def clean_text(text):
    """Clean text: convert from ALL CAPS to proper case for names, strip whitespace."""
    if text is None:
        return None
    text = str(text).strip()
    if not text:
        return None
    # Remove excessive whitespace but preserve intentional newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*', '\n', text)
    return text


def title_case_ball_name(name):
    """Convert ball name to title case, handling special cases."""
    if name is None:
        return None
    name = str(name).strip()
    if not name:
        return None
    # Convert from ALL CAPS to title case
    # But preserve abbreviations and short words
    words = name.replace('\n', ' ').split()
    result = []
    for w in words:
        # Keep abbreviations (all caps, short) or numbers as-is
        if len(w) <= 3 and w.isupper():
            result.append(w)
        elif w.isupper():
            result.append(w.title())
        else:
            result.append(w)
    return ' '.join(result)


def import_folio(db, filepath, sheet_name, folio_num, start_record_no):
    """Import a single folio Excel file into the database."""
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb[sheet_name]

    records = []
    for row in ws.iter_rows(min_row=2, max_col=11, values_only=True):
        # Skip empty rows or non-data rows
        if row[0] is None or not isinstance(row[0], (int, float)):
            continue

        orig_num = int(row[0])
        ball_name = title_case_ball_name(row[1])
        ball_name_format = clean_text(row[2])
        era_raw = clean_text(row[3])
        cover_pattern = clean_text(row[4])
        specs = clean_text(row[5])
        patents_legal = clean_text(row[6])
        manufacturer = clean_text(row[7])
        auction_remarks = clean_text(row[8])
        value_raw_input = row[9]

        era_start, era_end, era_sort = parse_era(era_raw)
        value_raw, value_low, value_high, value_mid, currency = parse_value(value_raw_input)

        # Try to determine country from manufacturer
        country = None
        if manufacturer:
            mfr_upper = manufacturer.upper()
            if any(x in mfr_upper for x in ['SCOTLAND', 'GLASGOW', 'EDINBURGH']):
                country = 'Scotland'
            elif any(x in mfr_upper for x in ['ENGLAND', 'LONDON', 'MANCHESTER', 'BIRMINGHAM', 'SURREY', 'KENT', 'LEEDS', 'LANCASHIRE', 'MIDDLESEX']):
                country = 'England'
            elif any(x in mfr_upper for x in ['USA', 'OHIO', 'ILLINOIS', 'NEW YORK', 'CHICAGO', 'MASSACHUSETTS', 'NEW JERSEY', 'CALIFORNIA', 'CONNECTICUT', 'MICHIGAN', 'WISCONSIN', 'PENNSYLVANIA', 'INDIANA', 'MISSOURI', 'VIRGINIA', 'TEXAS', 'MARYLAND', 'GEORGIA', 'FLORIDA', 'MINNESOTA', 'IOWA', 'KENTUCKY', 'TENNESSEE', 'NORTH CAROLINA', 'CINCINNATI', 'AKRON', 'ELYRIA']):
                country = 'USA'
            elif any(x in mfr_upper for x in ['CANADA', 'TORONTO', 'MONTREAL']):
                country = 'Canada'
            elif any(x in mfr_upper for x in ['FRANCE', 'PARIS']):
                country = 'France'
            elif any(x in mfr_upper for x in ['GERMANY', 'BERLIN']):
                country = 'Germany'
            elif any(x in mfr_upper for x in ['JAPAN', 'TOKYO']):
                country = 'Japan'
            elif any(x in mfr_upper for x in ['IRELAND', 'DUBLIN']):
                country = 'Ireland'
            elif 'UN-ATTRIBUTED' in mfr_upper:
                # Check if there's a country hint after UN-ATTRIBUTED
                m = re.search(r'UN-ATTRIBUTED\s+(England|Scotland|USA|Canada|France|Germany)', manufacturer, re.IGNORECASE)
                if m:
                    country = m.group(1).title()
                    if country == 'Usa':
                        country = 'USA'

        # Determine rarity score based on value
        rarity = 0
        if value_mid is not None:
            if value_mid >= 5000:
                rarity = 6
            elif value_mid >= 2000:
                rarity = 5
            elif value_mid >= 1000:
                rarity = 4
            elif value_mid >= 500:
                rarity = 3
            elif value_mid >= 200:
                rarity = 2
            else:
                rarity = 1

        # Parse condition from auction remarks
        condition = None
        if auction_remarks:
            cond_match = re.search(r'\[([AW][1-5])\]', auction_remarks)
            if cond_match:
                condition = cond_match.group(1)

        records.append({
            'ball_name': ball_name,
            'ball_name_format': ball_name_format,
            'era': era_raw,
            'era_start': era_start,
            'era_end': era_end,
            'era_sort': era_sort,
            'cover_pattern': cover_pattern,
            'manufacturer': manufacturer,
            'specs': specs,
            'patents_legal': patents_legal,
            'auction_remarks': auction_remarks,
            'condition_grade': condition,
            'value_raw': value_raw,
            'value_low': value_low,
            'value_high': value_high,
            'value_mid': value_mid,
            'currency': currency,
            'country': country,
            'rarity_score': rarity,
            'folio': folio_num,
        })

    wb.close()

    # Insert records with new record_no starting from start_record_no
    for i, rec in enumerate(records):
        record_no = start_record_no + i
        db.execute('''
            INSERT INTO golf_balls (
                record_no, ball_name, ball_name_format, era, era_start, era_end, era_sort,
                cover_pattern, manufacturer, specs, patents_legal, auction_remarks,
                condition_grade, value_raw, value_low, value_high, value_mid,
                currency, country, rarity_score, folio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_no, rec['ball_name'], rec['ball_name_format'], rec['era'],
            rec['era_start'], rec['era_end'], rec['era_sort'],
            rec['cover_pattern'], rec['manufacturer'], rec['specs'],
            rec['patents_legal'], rec['auction_remarks'], rec['condition_grade'],
            rec['value_raw'], rec['value_low'], rec['value_high'], rec['value_mid'],
            rec['currency'], rec['country'], rec['rarity_score'], rec['folio']
        ))

    print(f"  Imported {len(records)} records (record_no {start_record_no} - {start_record_no + len(records) - 1})")
    return start_record_no + len(records)


def main():
    db = sqlite3.connect('golf_balls_v2.db')

    # Step 1: Add folio column if it doesn't exist
    cursor = db.execute("PRAGMA table_info(golf_balls)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'folio' not in columns:
        print("Adding 'folio' column to golf_balls table...")
        db.execute("ALTER TABLE golf_balls ADD COLUMN folio INTEGER DEFAULT 1")
        db.execute("UPDATE golf_balls SET folio = 1")
        db.commit()
        print("  Done. Set all existing records to folio 1.")
    else:
        print("'folio' column already exists.")

    # Step 2: Check current max record_no
    max_rec = db.execute("SELECT MAX(record_no) FROM golf_balls").fetchone()[0]
    print(f"\nCurrent max record_no: {max_rec}")
    next_rec = max_rec + 1

    # Step 3: Remove any previously imported folio 2/3/4 data (idempotent)
    for folio_num in [2, 3, 4]:
        deleted = db.execute("DELETE FROM golf_balls WHERE folio = ?", (folio_num,)).rowcount
        if deleted:
            print(f"  Removed {deleted} existing folio {folio_num} records (re-import)")
    db.commit()

    # Recalculate next record_no after cleanup
    max_rec = db.execute("SELECT MAX(record_no) FROM golf_balls").fetchone()[0]
    next_rec = max_rec + 1

    # Step 4: Import each folio
    print(f"\nImporting Folio 2...")
    next_rec = import_folio(db, 'FINAL FOLIO 2 EXCELL TO NICK  (1).xlsx', 'Sheet1', 2, next_rec)

    print(f"Importing Folio 3...")
    next_rec = import_folio(db, 'FINAL FOLIO 3 EXCELL FOR NICK (1).xlsx', 'FOLIO 3', 3, next_rec)

    print(f"Importing Folio 4...")
    next_rec = import_folio(db, 'FINAL FOLIO 4 EXCELL TO NICK.xlsx', 'FOLIO 4', 4, next_rec)

    db.commit()

    # Step 5: Print summary
    print("\n=== IMPORT SUMMARY ===")
    for folio_num in [1, 2, 3, 4]:
        count = db.execute("SELECT COUNT(*) FROM golf_balls WHERE folio = ?", (folio_num,)).fetchone()[0]
        print(f"  Folio {folio_num}: {count} balls")
    total = db.execute("SELECT COUNT(*) FROM golf_balls").fetchone()[0]
    print(f"  TOTAL: {total} balls")

    db.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
