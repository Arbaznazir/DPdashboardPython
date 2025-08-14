"""
Script to load data from raw tables into partitioned tables.
"""
import psycopg2
from sqlalchemy import create_engine, text
from db_utils import get_connection

def load_data_to_partitioned_tables():
    """Load data from raw tables to partitioned tables"""
    print("Loading data into partitioned tables...")
    
    conn = get_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Load data into seat_prices_partitioned
        print("Loading data into seat_prices_partitioned...")
        cursor.execute("""
            INSERT INTO seat_prices_partitioned
            SELECT * FROM seat_prices_raw
            ON CONFLICT DO NOTHING;
        """)
        
        # Load data into seat_wise_prices_partitioned
        print("Loading data into seat_wise_prices_partitioned...")
        cursor.execute("""
            INSERT INTO seat_wise_prices_partitioned
            SELECT * FROM seat_wise_prices_raw
            ON CONFLICT DO NOTHING;
        """)
        
        # Load data into seat_prices_with_dt_partitioned
        print("Loading data into seat_prices_with_dt_partitioned...")
        cursor.execute("""
            INSERT INTO seat_prices_with_dt_partitioned
            SELECT * FROM seat_prices_with_dt
            ON CONFLICT DO NOTHING;
        """)
        
        # Load data into seat_wise_prices_with_dt_partitioned
        print("Loading data into seat_wise_prices_with_dt_partitioned...")
        cursor.execute("""
            INSERT INTO seat_wise_prices_with_dt_partitioned
            SELECT * FROM seat_wise_prices_with_dt
            ON CONFLICT DO NOTHING;
        """)
        
        conn.commit()
        print("✅ Data loaded into partitioned tables successfully")
        
    except Exception as e:
        print(f"⚠️ Error loading data into partitioned tables: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    
    return True

if __name__ == "__main__":
    load_data_to_partitioned_tables()
