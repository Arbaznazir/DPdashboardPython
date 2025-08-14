"""
Script to drop existing partitioned tables before recreating them with correct schema.
"""
import psycopg2
from db_utils import get_connection

def drop_partitioned_tables():
    """Drop all existing partitioned tables"""
    print("Dropping existing partitioned tables...")
    
    conn = get_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    # List of partitioned tables to drop
    tables_to_drop = [
        "seat_prices_partitioned",
        "seat_prices_with_dt_partitioned",
        "seat_wise_prices_partitioned",
        "seat_wise_prices_with_dt_partitioned"
    ]
    
    for table in tables_to_drop:
        try:
            print(f"Dropping table {table}...")
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            conn.commit()
            print(f"✅ Successfully dropped {table}")
        except Exception as e:
            print(f"⚠️ Error dropping {table}: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("✅ All partitioned tables dropped successfully")
    return True

if __name__ == "__main__":
    drop_partitioned_tables()
