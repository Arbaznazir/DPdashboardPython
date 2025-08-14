import psycopg2

# Database connection parameters
DB_NAME = "dynamic_pricing_db"
DB_USER = "postgres"
DB_PASSWORD = "Ghost143"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=DB_PORT
    )

def check_table_columns():
    conn = get_connection()
    cur = conn.cursor()
    
    # List of tables to check
    tables = [
        'seat_prices_raw', 
        'seat_wise_prices_raw', 
        'seat_prices_with_dt', 
        'seat_wise_prices_with_dt',
        'seat_prices_raw_partitioned', 
        'seat_wise_prices_raw_partitioned', 
        'seat_prices_with_dt_partitioned', 
        'seat_wise_prices_with_dt_partitioned'
    ]
    
    for table in tables:
        try:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table,))
            
            if not cur.fetchone()[0]:
                print(f"\n❌ TABLE {table} DOES NOT EXIST")
                continue
                
            # Get columns for this table
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table,))
            
            columns = cur.fetchall()
            
            print(f"\n✅ {table.upper()} COLUMNS ({len(columns)}):")
            for col in columns:
                print(f"  - {col[0]} ({col[1]})")
                
        except Exception as e:
            print(f"\n❌ Error checking {table}: {e}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_table_columns()
