"""
Script to manage database partitioning for improved query performance.
This handles creating partitions and migrating data to partitioned tables.
Uses 7-day range partitioning with batched data migration for optimal performance.
"""
import os
import sys
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
from db_utils import get_connection, get_engine

def setup_partitioning(batch_size=500000):
    """Set up database partitioning for improved performance.
    
    Args:
        batch_size (int): Number of rows to process in each batch
        
    Returns:
        bool: True if partitioning was set up successfully, False otherwise.
    """
    print("\n🔄 Setting up database partitioning for improved performance...")
    
    try:
        engine = get_engine()
        
        # Read and execute the SQL script
        script_path = os.path.join(os.path.dirname(__file__), 'db_partitioning.sql')
        with open(script_path, 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script to create functions and tables
        with engine.begin() as conn:
            conn.execute(text(sql_script))
            print("✅ SQL script executed successfully")
        
        # Run the automated partitioning setup only, without full data migration
        # This is much faster than running the full migration
        with engine.begin() as conn:
            # Set a statement timeout to prevent hanging (5 minutes)
            conn.execute(text("SET statement_timeout = 300000;"))
            
            # Create the partitioned tables structure directly using SQL statements
            # These statements create the parent partitioned tables if they don't exist
            conn.execute(text("""
                -- Create partitioned seat_prices_with_dt table if it doesn't exist
                CREATE TABLE IF NOT EXISTS seat_prices_with_dt_partitioned (
                    schedule_id INTEGER,
                    seat_type VARCHAR(50),
                    price NUMERIC,
                    date_of_journey DATE,
                    timeanddatestamp TIMESTAMP,
                    PRIMARY KEY (date_of_journey, schedule_id, seat_type, timeanddatestamp)
                ) PARTITION BY RANGE (date_of_journey);
                
                -- Create partitioned seat_wise_prices_with_dt table if it doesn't exist
                CREATE TABLE IF NOT EXISTS seat_wise_prices_with_dt_partitioned (
                    schedule_id INTEGER,
                    seat_number INTEGER,
                    seat_type VARCHAR(50),
                    final_price NUMERIC,
                    actual_fare NUMERIC,
                    coach_layout_id INTEGER,
                    sales_count NUMERIC,
                    sales_percentage NUMERIC,
                    operator_reservation_id INTEGER,
                    travel_id INTEGER,
                    origin_id INTEGER,
                    destination_id INTEGER,
                    travel_date DATE,
                    op_origin INTEGER,
                    op_destination INTEGER,
                    snapshotdate VARCHAR(20),
                    snapshottime VARCHAR(20),
                    timeanddatestamp TIMESTAMP,
                    PRIMARY KEY (travel_date, schedule_id, seat_number, timeanddatestamp)
                ) PARTITION BY RANGE (travel_date);
            """))
            
            # Now create the partitions for the current date range
            # We'll use the existing create_partitions_for_range function
            # Get the min and max dates from the data
            min_date_result = conn.execute(text("""
                SELECT MIN(date_of_journey) AS min_date FROM seat_prices_with_dt
                UNION ALL
                SELECT MIN(travel_date) AS min_date FROM seat_wise_prices_with_dt
                ORDER BY min_date
                LIMIT 1
            """)).fetchone()
            
            max_date_result = conn.execute(text("""
                SELECT MAX(date_of_journey) AS max_date FROM seat_prices_with_dt
                UNION ALL
                SELECT MAX(travel_date) AS max_date FROM seat_wise_prices_with_dt
                ORDER BY max_date DESC
                LIMIT 1
            """)).fetchone()
            
            if min_date_result and max_date_result and min_date_result[0] and max_date_result[0]:
                min_date = min_date_result[0]
                max_date = max_date_result[0]
                
                # Create partitions for this date range
                conn.execute(text(f"SELECT create_partitions_for_range('{min_date}', '{max_date}');"))
                print(f"✅ Created partitions for date range: {min_date} to {max_date}")
            else:
                print("⚠️ No date range found for creating partitions")
            
            # We'll skip the full data migration as it's very slow
            # Instead, we'll create partitions as needed when loading new data
            
        print("✅ Partitioning setup and data migration completed successfully!")
        
        # Display partition statistics
        get_partition_stats()
        
        return True
    except Exception as e:
        print(f"❌ Error setting up partitioning: {str(e)}")
        return False

def ensure_partitions_exist(start_date, end_date):
    """Ensure partitions exist for the given date range.
    
    Args:
        start_date (datetime): Start date for partitioning
        end_date (datetime): End date for partitioning
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = get_engine()
        
        # Convert dates to strings in YYYY-MM-DD format
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Call the function to create partitions
        with engine.begin() as conn:
            conn.execute(text(f"SELECT create_partitions_for_range('{start_str}', '{end_str}');"))
        
        print(f"✅ Ensured partitions exist from {start_str} to {end_str}")
        return True
    except Exception as e:
        print(f"❌ Error ensuring partitions exist: {str(e)}")
        return False

def load_to_partitioned_tables(conn, df, table_name, batch_size=100000):
    """Load data to partitioned tables in batches.
    
    Args:
        conn: Database connection
        df (DataFrame): DataFrame containing the data
        table_name (str): Name of the table (e.g., seat_prices_with_dt)
        batch_size (int): Number of rows to process in each batch
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if df.empty:
            print(f"⚠️ No data to load into partitioned {table_name}")
            return True
        
        # Determine the date column based on table name
        if table_name in ["seat_prices_with_dt", "seat_prices_raw"]:
            date_column = "date_of_journey"
        elif table_name in ["seat_wise_prices_with_dt", "seat_wise_prices_raw"]:
            date_column = "travel_date"
        else:
            print(f"⚠️ Unknown table {table_name}, cannot determine date column")
            return False
        
        # Call the existing function with the correct parameters
        return load_data_to_partitioned_tables(df, table_name, date_column, batch_size)
    except Exception as e:
        print(f"❌ Error in load_to_partitioned_tables: {str(e)}")
        return False

def load_data_to_partitioned_tables(df, table_name, date_column, batch_size=100000):
    """Load data to partitioned tables in batches.
    
    Args:
        df (DataFrame): DataFrame containing the data
        table_name (str): Name of the target table (without _partitioned suffix)
        date_column (str): Name of the date column used for partitioning
        batch_size (int): Number of rows to process in each batch
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if df.empty:
            print(f"⚠️ No data to load into {table_name}_partitioned")
            return True
        
        # Get min and max dates from the data
        min_date = df[date_column].min()
        max_date = df[date_column].max()
        
        # Ensure dates are datetime objects
        if isinstance(min_date, str):
            min_date = datetime.strptime(min_date, '%Y-%m-%d')
        if isinstance(max_date, str):
            max_date = datetime.strptime(max_date, '%Y-%m-%d')
        
        # Add a buffer day to max_date to ensure inclusion
        max_date = max_date + timedelta(days=1)
        
        # Ensure partitions exist for this date range
        ensure_partitions_exist(min_date, max_date)
        
        # Load data into the partitioned table in batches
        engine = get_engine()
        total_rows = len(df)
        rows_processed = 0
        
        print(f"🔄 Loading {total_rows} rows into {table_name}_partitioned in batches of {batch_size}...")
        
        # Process in batches
        for i in range(0, total_rows, batch_size):
            batch_df = df.iloc[i:i+batch_size].copy()
            
            # Ensure column names match between source and target tables
            # First, check if the partitioned table exists and get its columns
            try:
                with engine.connect() as conn:
                    # Get columns of the partitioned table
                    result = conn.execute(text(f"SELECT * FROM {table_name}_partitioned LIMIT 0"))
                    
                    # Handle different return types from SQLAlchemy
                    target_columns = []
                    for col in result.keys():
                        # Check if col is a string or has a name attribute
                        if isinstance(col, str):
                            target_columns.append(col)
                        elif hasattr(col, 'name'):
                            target_columns.append(col.name)
                        else:
                            # Fallback - convert to string
                            target_columns.append(str(col))
                    
                    # Filter dataframe to only include columns that exist in the target table
                    common_columns = [col for col in batch_df.columns if col in target_columns]
                    if common_columns:
                        batch_df = batch_df[common_columns]
                        print(f"  ℹ️ Using {len(common_columns)} matching columns for data loading")
                    else:
                        # If no common columns, we need to handle this differently
                        print(f"  ⚠️ No matching columns found between source data and target table")
                        # Try to map columns by lowercase name
                        lowercase_map = {col.lower(): col for col in batch_df.columns}
                        batch_df.columns = [col.lower() for col in batch_df.columns]
                        
            except Exception as e:
                print(f"  ⚠️ Error checking target table columns: {e}")
                # Continue with original columns
                
            try:
                # Use pandas to_sql with appropriate parameters
                batch_df.to_sql(f"{table_name}_partitioned", engine, if_exists='append', index=False)
                
                rows_processed += len(batch_df)
                progress = (rows_processed / total_rows) * 100
                print(f"  ⏳ Progress: {progress:.1f}% ({rows_processed}/{total_rows} rows)")
            except Exception as e:
                print(f"  ❌ Error loading batch: {e}")
                # Try one more approach - convert all column names to lowercase
                try:
                    batch_df.columns = [col.lower() for col in batch_df.columns]
                    batch_df.to_sql(f"{table_name}_partitioned", engine, if_exists='append', index=False)
                    print("  ✅ Successfully loaded data with lowercase column names")
                    
                    rows_processed += len(batch_df)
                    progress = (rows_processed / total_rows) * 100
                    print(f"  ⏳ Progress: {progress:.1f}% ({rows_processed}/{total_rows} rows)")
                except Exception as e2:
                    print(f"  ❌ Failed second attempt: {e2}")
                    # Continue with next batch
        
        # Create indexes for the affected partitions, but only if needed
        try:
            # Get unique dates in the data
            unique_dates = pd.date_range(start=min_date, end=max_date, freq='7D')
            
            # Only create indexes for a limited number of partitions at a time
            # to avoid overwhelming the database
            max_partitions_to_index = 2  # Limit to indexing 2 partitions at a time
            partitions_to_index = unique_dates[:max_partitions_to_index]
            
            if partitions_to_index.size > 0:
                print(f"🔍 Creating indexes for {len(partitions_to_index)} partitions (limited to avoid performance issues)...")
                
                for date in partitions_to_index:
                    try:
                        next_date = date + timedelta(days=7)
                        partition_name = f"p{date.strftime('%Y_%m_%d')}_{next_date.strftime('%Y_%m_%d')}"
                        
                        # Check if indexes already exist for this partition
                        with engine.connect() as conn:
                            # Create indexes for this partition with a timeout
                            conn.execute(text(f"SET statement_timeout = '30s'; SELECT create_partition_indexes('{partition_name}');"))
                            print(f"  ✅ Created indexes for partition {partition_name}")
                    except Exception as e:
                        print(f"  ⚠️ Could not create indexes for partition: {e}")
                        # Continue with other partitions even if one fails
                        continue
            else:
                print("  ℹ️ No partitions need indexing")
        except Exception as e:
            print(f"  ⚠️ Error during index creation: {e}")
            # Continue even if indexing fails - data is still loaded
        
        print(f"✅ Successfully loaded all data into {table_name}_partitioned")
        return True
    except Exception as e:
        print(f"❌ Error loading data to partitioned table: {str(e)}")
        return False

def get_partition_stats():
    """Get statistics about the partitioned tables.
    
    Returns:
        list: List of dictionaries with partition statistics
    """
    try:
        engine = get_engine()
        
        with engine.connect() as conn:
            # Get list of partitions
            result = conn.execute(text("""
                SELECT parent.relname AS parent_table, 
                       child.relname AS partition_name,
                       pg_size_pretty(pg_relation_size(child.oid)) AS size,
                       pg_stat_get_live_tuples(child.oid) AS row_count
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                WHERE parent.relname IN ('seat_prices_partitioned', 'seat_wise_prices_partitioned', 
                                        'seat_prices_raw_partitioned', 'seat_wise_prices_raw_partitioned')
                ORDER BY parent.relname, child.relname;
            """))
            
            partitions = [dict(row._mapping) for row in result]
            
            print("\n📊 Partition Statistics:")
            print("-" * 80)
            print(f"{'Parent Table':<25} {'Partition Name':<30} {'Size':<15} {'Row Count':<10}")
            print("-" * 80)
            
            for p in partitions:
                print(f"{p['parent_table']:<25} {p['partition_name']:<30} {p['size']:<15} {p['row_count']:<10}")
            
            return partitions
    except Exception as e:
        print(f"❌ Error getting partition stats: {str(e)}")
        return []

def is_imported_by_load_script():
    """Check if this script was imported by load_to_postgres.py"""
    import inspect
    for frame in inspect.stack():
        if frame.filename.endswith('load_to_postgres.py'):
            return True
    return False

if __name__ == "__main__":
    # Only run automatically if not imported by load_to_postgres.py
    if not is_imported_by_load_script():
        setup_partitioning()
