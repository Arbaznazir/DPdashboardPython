import psycopg2
import pandas as pd

# Connect to database
conn = psycopg2.connect(
    dbname="dynamic_pricing_db", 
    user="postgres", 
    password="Ghost143",
    host="localhost", 
    port="5432"
)

# Get all operators
query = "SELECT DISTINCT operator_id FROM seat_prices_with_dt ORDER BY operator_id"
df_operators = pd.read_sql_query(query, conn)
print(f"Operators found: {df_operators['operator_id'].tolist()}")

# Get all dates
query = "SELECT DISTINCT date_of_journey FROM seat_prices_with_dt ORDER BY date_of_journey DESC"
df_dates = pd.read_sql_query(query, conn)
print(f"Dates found (first 5): {df_dates['date_of_journey'].head(5).tolist()}")

# Check for matching departure times between operators
if len(df_operators) >= 2:
    operator1 = df_operators.iloc[0]['operator_id']
    operator2 = df_operators.iloc[1]['operator_id']
    
    print(f"\nChecking matching departure times between operators {operator1} and {operator2}:")
    
    # Get departure times for each operator
    query1 = """
    SELECT DISTINCT departure_time, date_of_journey
    FROM seat_prices_with_dt
    WHERE operator_id = %s
    """
    df_times1 = pd.read_sql_query(query1, conn, params=(operator1,))
    
    query2 = """
    SELECT DISTINCT departure_time, date_of_journey
    FROM seat_prices_with_dt
    WHERE operator_id = %s
    """
    df_times2 = pd.read_sql_query(query2, conn, params=(operator2,))
    
    print(f"Operator {operator1} has {len(df_times1)} unique departure_time/date combinations")
    print(f"Operator {operator2} has {len(df_times2)} unique departure_time/date combinations")
    
    # Check for matches
    matches = pd.merge(df_times1, df_times2, on=['departure_time', 'date_of_journey'])
    print(f"Found {len(matches)} matching departure_time/date combinations")
    
    if not matches.empty:
        print("\nSample of matching times:")
        print(matches.head(5))
    else:
        print("\nNo matching times found. Checking if departure_time values are NULL:")
        
        # Check for NULL departure_time values
        query = """
        SELECT COUNT(*) as null_count
        FROM seat_prices_with_dt
        WHERE departure_time IS NULL
        """
        null_count = pd.read_sql_query(query, conn)
        print(f"Records with NULL departure_time: {null_count['null_count'].iloc[0]}")
        
        # Check sample of departure_time values
        query = """
        SELECT operator_id, departure_time, date_of_journey
        FROM seat_prices_with_dt
        LIMIT 10
        """
        sample = pd.read_sql_query(query, conn)
        print("\nSample of departure_time values:")
        print(sample)

conn.close()
