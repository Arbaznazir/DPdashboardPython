import os
import psycopg2
import pandas as pd
from psycopg2 import sql
from datetime import datetime

# ----------------- CONFIG -----------------
SEAT_PRICES_DIR = r"D:\Programming\DP-Dashboard\seat_prices"
SEAT_WISE_PRICES_DIR = r"D:\Programming\DP-Dashboard\seat_wise_prices"
LOG_FILE = r"D:\Programming\DP-Dashboard\loaded_files_log\loaded_files.txt"
DB_NAME = "dynamic_pricing_db"
DB_USER = "postgres"
DB_PASSWORD = "Ghost143"
DB_HOST = "localhost"
DB_PORT = "5432"

# ------------- UTILITY FUNCTIONS -------------
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=DB_PORT
    )

def ensure_table_exists(conn, table_name, sample_df):
    cur = conn.cursor()
    # Deduplicate columns case-insensitively, keeping only the first occurrence
    seen = set()
    orig_cols = []
    for c in sample_df.columns:
        cl = c.lower()
        # Exclude legacy timestamp columns
        if cl in ["datestamp", "timestamp", "timeanddatestamp"]:
            continue
        if cl not in seen:
            seen.add(cl)
            orig_cols.append(c)
    # Always append SnapshotDate, SnapshotTime, TimeAndDateStamp at the end
    final_cols = orig_cols.copy()
    for col in ["SnapshotDate", "SnapshotTime", "TimeAndDateStamp"]:
        if not any(c.lower() == col.lower() for c in final_cols):
            final_cols.append(col)
    columns = ", ".join([f'{col} TEXT' for col in final_cols])
    cur.execute(
        sql.SQL(f"""CREATE TABLE IF NOT EXISTS {table_name} ({columns});""")
    )
    conn.commit()
    cur.close()
    print(f"🛠️ Ensured table exists: {table_name}")

import os

def extract_timestamp_from_filename(filename, table_type):
    """Extract timestamp from filename and format as:
    - SnapshotDate: DD-MM-YYYY
    - SnapshotTime: HH:MM:00
    - TimeAndDateStamp: DD-MM-YYYY HH:MM:00
    """
    try:
        basename = os.path.basename(filename)

        # Remove prefix and .csv
        if table_type == "seat_prices":
            timestamp_str = basename.replace("seat_prices_", "").replace(".csv", "")
        elif table_type == "seat_wise_prices":
            timestamp_str = basename.replace("seat_wise_prices_", "").replace(".csv", "")
        else:
            raise ValueError("Unknown table_type")

        # Split date and time
        date_part, time_part = timestamp_str.split("_")  # '2025-07-31', '08-00'

        # Convert to required formats
        year, month, day = date_part.split("-")
        hour, minute = time_part.split("-")

        snapshot_date = f"{day}-{month}-{year}"
        snapshot_time = f"{hour}:{minute}:00"
        time_and_date_stamp = f"{snapshot_date} {snapshot_time}"

        return snapshot_date, snapshot_time, time_and_date_stamp

    except Exception as e:
        print(f"⚠️ Error parsing timestamp from {filename}: {e}")
        return None, None, None

def drop_table_if_exists(conn, table_name):
    """Drop a table if it exists"""
    cur = conn.cursor()
    try:
        cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        conn.commit()
        print(f"✅ Dropped table {table_name} (if it existed)")
    except Exception as e:
        conn.rollback()
        print(f"Error dropping table {table_name}: {e}")
    finally:
        cur.close()

def ensure_tables_exist_once(conn):
    """Ensure both required tables exist with only expected columns plus our three timestamp columns"""
    # Drop tables first to ensure clean schema during development
    drop_table_if_exists(conn, "seat_prices_raw")
    drop_table_if_exists(conn, "seat_wise_prices_raw")
    
    # Expected columns for each table type (these are the ONLY columns we want to keep from CSVs)
    seat_prices_expected_cols = [
        "expected_occupancy", "actual_occupancy", "demand_index", "time_step_to_check", 
        "operator_id", "date_of_journey", "time_slot", "seat_type", "hours_before_departure", 
        "price", "origin", "destination", "actual_fare", "schedule_id", "coach_layout_id"
    ]
    
    seat_wise_prices_expected_cols = [
        "schedule_id", "seat_number", "seat_type", "final_price", "actual_fare", 
        "coach_layout_id", "sales_count", "sales_percentage", "operator_reservation_id", 
        "travel_id", "origin_id", "destination_id", "travel_date", "op_origin", "op_destination"
    ]
    
    # Create tables with expected columns
    create_table_with_expected_columns(conn, "seat_prices_raw", SEAT_PRICES_DIR, seat_prices_expected_cols)
    create_table_with_expected_columns(conn, "seat_wise_prices_raw", SEAT_WISE_PRICES_DIR, seat_wise_prices_expected_cols)

def create_table_with_expected_columns(conn, table_name, folder_path, expected_columns):
    """Create a table with only expected columns plus timestamp columns"""
    cur = conn.cursor()
    
    # Find a sample CSV file to get column structure
    if os.path.exists(folder_path) and os.listdir(folder_path):
        sample_file = None
        for filename in os.listdir(folder_path):
            if filename.endswith('.csv'):
                sample_file = os.path.join(folder_path, filename)
                break
                
        if sample_file:
            # Create table with expected columns
            columns_sql = ", ".join([f'"{col}" TEXT' for col in expected_columns])
            columns_sql += ', "SnapshotDate" TEXT, "SnapshotTime" TEXT, "TimeAndDateStamp" TEXT'
            
            try:
                cur.execute(f"CREATE TABLE {table_name} ({columns_sql});")
                conn.commit()
                print(f"🛠️ Created table {table_name} with expected columns")
            except Exception as e:
                conn.rollback()
                print(f"Error creating {table_name}: {e}")
        else:
            print(f"⚠️ No CSV files found in {folder_path}")
    else:
        print(f"⚠️ Directory {folder_path} does not exist or is empty")
    
    cur.close()

def add_missing_columns(conn, table_name, df):
    cur = conn.cursor()
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s
    """, (table_name,))
    existing_cols = [row[0].lower() for row in cur.fetchall()]

    # Only add columns if not present (case-insensitive)
    for col in df.columns:
        if col.lower() not in existing_cols:
            cur.execute(sql.SQL("ALTER TABLE {} ADD COLUMN {} TEXT").format(
                sql.Identifier(table_name),
                sql.Identifier(col)
            ))
            print(f"➕ Added missing column '{col}' to {table_name}")

    conn.commit()
    cur.close()

def load_csv_files(folder, table_name, conn, already_loaded):
    """Load CSV files from folder into database table"""
    new_files = []
    # Only create one cursor for the whole function
    table_type = "seat_prices" if "seat_prices" in table_name else "seat_wise_prices"
    
    # Define expected columns for each table type
    if table_type == "seat_prices":
        expected_columns = [
            "expected_occupancy", "actual_occupancy", "demand_index", "time_step_to_check", 
            "operator_id", "date_of_journey", "time_slot", "seat_type", "hours_before_departure", 
            "price", "origin", "destination", "actual_fare", "schedule_id", "coach_layout_id"
        ]
    else:  # seat_wise_prices
        expected_columns = [
            "schedule_id", "seat_number", "seat_type", "final_price", "actual_fare", 
            "coach_layout_id", "sales_count", "sales_percentage", "operator_reservation_id", 
            "travel_id", "origin_id", "destination_id", "travel_date", "op_origin", "op_destination"
        ]
    
    # Make sure the tables have the required columns
    with conn.cursor() as prep_cur:
        for column_name in ["SnapshotDate", "SnapshotTime", "TimeAndDateStamp"]:
            try:
                prep_cur.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS \"{column_name}\" TEXT;")
            except Exception as e:
                print(f"Error ensuring column {column_name}: {e}")
        conn.commit()
    
    # Get column info once before processing files
    all_columns = set()
    with conn.cursor() as info_cur:
        info_cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
        for col in info_cur.fetchall():
            all_columns.add(col[0].lower())
    
    # Process each file
    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".csv") and filename not in already_loaded:
            file_path = os.path.join(folder, filename)
            print(f"📥 Loading {filename} into {table_name}...")
            
            # Read CSV file
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()
            
            # Filter to keep only expected columns (case insensitive)
            col_mapping = {col.lower(): col for col in df.columns}
            columns_to_keep = []
            for expected_col in expected_columns:
                if expected_col.lower() in col_mapping:
                    columns_to_keep.append(col_mapping[expected_col.lower()])
            
            # Keep only expected columns
            df = df[columns_to_keep]
            
            # Extract timestamp from filename using updated format
            snapshot_date, snapshot_time, time_and_date_stamp = extract_timestamp_from_filename(filename, table_type)
            
            # Add timestamp columns to dataframe
            if snapshot_date and snapshot_time and time_and_date_stamp:
                df['SnapshotDate'] = snapshot_date
                df['SnapshotTime'] = snapshot_time
                df['TimeAndDateStamp'] = time_and_date_stamp
                
            # Filter columns that exist in the table
            columns_to_use = []
            for col in df.columns:
                if col.lower() in all_columns:
                    columns_to_use.append(col)
                    
            # Prepare for insert using only columns that exist in the table
            if not columns_to_use:
                print(f"⚠️ No matching columns found for {table_name}!")
                continue
                
            # Insert data into table - use a new cursor for each file
            with conn.cursor() as insert_cur:
                placeholder = ', '.join(['%s'] * len(columns_to_use))
                columns = ', '.join(f'"{col}"' for col in columns_to_use)
                insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholder})"
                
                for _, row in df.iterrows():
                    values = tuple(None if pd.isna(value) else value for value in row[columns_to_use])
                    try:
                        insert_cur.execute(insert_query, values)
                    except Exception as e:
                        print(f"⚠️ Error inserting row: {e}")
                        print(f"Query was: {insert_query}")
                        conn.rollback()
                        break
            
            # Commit after each file
            conn.commit()
            new_files.append(filename)
            
    return new_files

def read_log():
    if not os.path.exists(LOG_FILE):
        return set()
    with open(LOG_FILE, "r") as f:
        return set(f.read().splitlines())

def update_log(new_files):
    with open(LOG_FILE, "a") as f:
        for file in new_files:
            f.write(file + "\n")

def refresh_views(conn):
    cur = conn.cursor()
    # 1. Latest views
    cur.execute("DROP VIEW IF EXISTS seat_prices_latest;")
    cur.execute("""
        CREATE VIEW seat_prices_latest AS
        SELECT * FROM seat_prices_raw
        ORDER BY "TimeAndDateStamp" DESC;
    """)

    cur.execute("DROP VIEW IF EXISTS seat_wise_prices_latest;")
    cur.execute("""
        CREATE VIEW seat_wise_prices_latest AS
        SELECT * FROM seat_wise_prices_raw
        ORDER BY "TimeAndDateStamp" DESC;
    """)

    # 2. Reference views

    # 1) fnGetHoursBeforeDeparture
    cur.execute("DROP VIEW IF EXISTS fnGetHoursBeforeDeparture;")
    cur.execute("""
        CREATE VIEW fnGetHoursBeforeDeparture AS
        SELECT DISTINCT "hours_before_departure", "schedule_id", "TimeAndDateStamp"
        FROM seat_prices_raw;
    """)

    # 2) occupancies
    cur.execute("DROP VIEW IF EXISTS occupancies;")
    cur.execute("""
        CREATE VIEW occupancies AS
        SELECT DISTINCT "actual_occupancy", "seat_type", "schedule_id", "TimeAndDateStamp"
        FROM seat_prices_raw
        ORDER BY "TimeAndDateStamp" DESC;
    """)

    # 3) expected_occupancies
    cur.execute("DROP VIEW IF EXISTS expected_occupancies;")
    cur.execute("""
        CREATE VIEW expected_occupancies AS
        SELECT DISTINCT "expected_occupancy", "seat_type", "schedule_id", "TimeAndDateStamp"
        FROM seat_prices_raw
        ORDER BY "TimeAndDateStamp" DESC;
    """)

    # 4) DateOfJourney
    cur.execute("DROP VIEW IF EXISTS DateOfJourney;")
    cur.execute("""
        CREATE VIEW DateOfJourney AS
        SELECT DISTINCT "date_of_journey", "schedule_id", "TimeAndDateStamp"
        FROM seat_prices_raw;
    """)

    # 5) schedule_id_text
    cur.execute("DROP VIEW IF EXISTS schedule_id_text;")
    cur.execute("""
        CREATE VIEW schedule_id_text AS
        SELECT DISTINCT "schedule_id", CAST("schedule_id" AS TEXT) AS "schedule_id_text"
        FROM seat_prices_raw;
    """)

    # 6) Actual_Price_SP
    cur.execute("DROP VIEW IF EXISTS Actual_Price_SP;")
    cur.execute("""
        CREATE VIEW Actual_Price_SP AS
        SELECT DISTINCT "seat_type", "actual_fare", "schedule_id", "TimeAndDateStamp"
        FROM seat_prices_raw;
    """)

    # 7) Model_Price_SP
    cur.execute("DROP VIEW IF EXISTS Model_Price_SP;")
    cur.execute("""
        CREATE VIEW Model_Price_SP AS
        SELECT DISTINCT "seat_type", "price", "schedule_id", "TimeAndDateStamp"
        FROM seat_prices_raw;
    """)

    conn.commit()
    cur.close()
    print("🔁 Views refreshed.")

# ----------------- MAIN SCRIPT -----------------
def drop_existing_tables(conn):
    cur = conn.cursor()
    for tbl in ["seat_prices_raw", "seat_wise_prices_raw"]:
        cur.execute(f'DROP TABLE IF EXISTS {tbl} CASCADE;')
    conn.commit()
    cur.close()


def main():
    conn = get_connection()
    print("🔌 Connected to database successfully")
    
    # Drop existing tables for a clean deduped schema
    drop_existing_tables(conn)

    # Read log of already loaded files
    already_loaded = read_log()
    print(f"📋 Found {len(already_loaded)} already loaded files in log")
    
    # Ensure both tables exist once at the beginning
    print("🛠️ Creating tables with proper schema...")
    ensure_tables_exist_once(conn)

    # Load new files from each directory
    print(f"📂 Checking for new files in {SEAT_PRICES_DIR}...")
    new_seat_files = load_csv_files(SEAT_PRICES_DIR, "seat_prices_raw", conn, already_loaded)
    print(f"📂 Checking for new files in {SEAT_WISE_PRICES_DIR}...")
    new_wise_files = load_csv_files(SEAT_WISE_PRICES_DIR, "seat_wise_prices_raw", conn, already_loaded)

    # Update log and refresh views if new files were loaded
    all_new_files = new_seat_files + new_wise_files
    print(f"📊 Found {len(new_seat_files)} new seat_prices files and {len(new_wise_files)} new seat_wise_prices files")
    
    if all_new_files:
        update_log(all_new_files)
        print("🔄 Refreshing views...")
        refresh_views(conn)
        print(f"✅ Successfully loaded {len(all_new_files)} new files")
    else:
        print("ℹ️ No new files to load")

    conn.close()
    print("✅ All done.")

if __name__ == "__main__":
    main()
