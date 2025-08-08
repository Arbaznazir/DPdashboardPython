import psycopg2
import pandas as pd

# Database connection parameters
DB_NAME = "dynamic_pricing_db"
DB_USER = "postgres"
DB_PASSWORD = "Ghost143"
DB_HOST = "localhost"
DB_PORT = "5432"

def check_tables():
    """Check tables in the database"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, 
            user=DB_USER, 
            password=DB_PASSWORD,
            host=DB_HOST, 
            port=DB_PORT
        )
        
        # Get list of tables
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cur.fetchall()
        
        print("Tables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check if seat_prices_with_dt exists and has data
        if ('seat_prices_with_dt',) in tables:
            cur.execute("SELECT COUNT(*) FROM seat_prices_with_dt;")
            count = cur.fetchone()[0]
            print(f"\nRecords in seat_prices_with_dt: {count}")
            
            if count > 0:
                cur.execute("SELECT DISTINCT operator_id FROM seat_prices_with_dt;")
                operators = cur.fetchall()
                print(f"Distinct operator_ids in seat_prices_with_dt: {[op[0] for op in operators]}")
                
                cur.execute("SELECT DISTINCT date_of_journey FROM seat_prices_with_dt LIMIT 5;")
                dates = cur.fetchall()
                print(f"Sample dates in seat_prices_with_dt: {[date[0] for date in dates]}")
                
                cur.execute("SELECT DISTINCT departure_time FROM seat_prices_with_dt LIMIT 5;")
                times = cur.fetchall()
                print(f"Sample departure_times in seat_prices_with_dt: {[time[0] for time in times]}")
        
        # Check if seat_wise_prices_with_dt exists and has data
        if ('seat_wise_prices_with_dt',) in tables:
            cur.execute("SELECT COUNT(*) FROM seat_wise_prices_with_dt;")
            count = cur.fetchone()[0]
            print(f"\nRecords in seat_wise_prices_with_dt: {count}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_tables()
