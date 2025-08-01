import psycopg2
from sqlalchemy import create_engine
import pandas as pd

# Database connection parameters
DB_NAME = "dynamic_pricing_db"
DB_USER = "postgres"
DB_PASSWORD = "Ghost143"
DB_HOST = "localhost"
DB_PORT = "5432"

def test_psycopg2_connection():
    """Test direct connection with psycopg2"""
    try:
        print("Testing psycopg2 connection...")
        conn = psycopg2.connect(
            dbname=DB_NAME, 
            user=DB_USER, 
            password=DB_PASSWORD,
            host=DB_HOST, 
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        print(f"Connection successful! Result: {result}")
        
        # Test if tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print(f"Available tables: {tables}")
        
        # Close connection
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test connection with SQLAlchemy"""
    try:
        print("\nTesting SQLAlchemy connection...")
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute("SELECT 1").fetchone()
            print(f"Connection successful! Result: {result}")
        
        # Test if tables exist
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        tables_df = pd.read_sql_query(query, engine)
        print(f"Available tables: {tables_df['table_name'].tolist()}")
        
        # Test seat_prices_raw table
        if 'seat_prices_raw' in tables_df['table_name'].tolist():
            print("\nTesting seat_prices_raw table...")
            query = "SELECT COUNT(*) FROM seat_prices_raw"
            count = pd.read_sql_query(query, engine).iloc[0, 0]
            print(f"seat_prices_raw has {count} rows")
            
            # Get sample data
            if count > 0:
                query = "SELECT * FROM seat_prices_raw LIMIT 5"
                sample_df = pd.read_sql_query(query, engine)
                print("\nSample data from seat_prices_raw:")
                print(sample_df.columns.tolist())
                print(f"Number of columns: {len(sample_df.columns)}")
        
        return True
    except Exception as e:
        print(f"SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    psycopg2_success = test_psycopg2_connection()
    sqlalchemy_success = test_sqlalchemy_connection()
    
    if psycopg2_success and sqlalchemy_success:
        print("\nAll database connection tests passed!")
    else:
        print("\nSome database connection tests failed!")
