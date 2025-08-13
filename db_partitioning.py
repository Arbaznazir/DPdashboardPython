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
        
        # Run the automated partitioning and data migration
        with engine.begin() as conn:
            conn.execute(text(f"SELECT create_partitions_and_migrate_data({batch_size});"))
            
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
            batch_df = df.iloc[i:i+batch_size]
            batch_df.to_sql(f"{table_name}_partitioned", engine, if_exists='append', index=False)
            
            rows_processed += len(batch_df)
            progress = (rows_processed / total_rows) * 100
            print(f"  ⏳ Progress: {progress:.1f}% ({rows_processed}/{total_rows} rows)")
        
        # Create indexes for the affected partitions
        with engine.begin() as conn:
            # Get unique dates in the data
            unique_dates = pd.date_range(start=min_date, end=max_date, freq='7D')
            
            for date in unique_dates:
                next_date = date + timedelta(days=7)
                partition_name = f"p{date.strftime('%Y_%m_%d')}_{next_date.strftime('%Y_%m_%d')}"
                
                # Create indexes for this partition
                conn.execute(text(f"SELECT create_partition_indexes('{partition_name}');"))
                print(f"  ✅ Created indexes for partition {partition_name}")
        
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
                WHERE parent.relname IN ('seat_prices_partitioned', 'seat_wise_prices_partitioned')
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
