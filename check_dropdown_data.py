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

# Check operators
print("Checking operators...")
query = """
SELECT DISTINCT operator_id
FROM seat_prices_with_dt
ORDER BY operator_id
"""
df_operators = pd.read_sql_query(query, conn)
print(f"Operators found: {df_operators.to_dict('records')}")

# Check dates
print("\nChecking dates...")
query = """
SELECT DISTINCT date_of_journey
FROM seat_prices_with_dt
ORDER BY date_of_journey DESC
"""
df_dates = pd.read_sql_query(query, conn)
print(f"Dates found: {df_dates.head(5).to_dict('records')}")

# Check if departure_time column exists
print("\nChecking departure_time column...")
query = """
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'seat_prices_with_dt' AND column_name = 'departure_time'
"""
df_column = pd.read_sql_query(query, conn)
print(f"departure_time column exists: {not df_column.empty}")

# Check departure times for specific operators and date
print("\nChecking matching departure times...")
if not df_operators.empty and len(df_operators) >= 2 and not df_dates.empty:
    operator1 = df_operators.iloc[0]['operator_id']
    operator2 = df_operators.iloc[1]['operator_id'] if len(df_operators) > 1 else df_operators.iloc[0]['operator_id']
    date = df_dates.iloc[0]['date_of_journey']
    
    query = """
    SELECT DISTINCT a.departure_time
    FROM seat_prices_with_dt a
    JOIN seat_prices_with_dt b ON a.departure_time = b.departure_time
        AND a.date_of_journey = b.date_of_journey
    WHERE a.date_of_journey = %s
        AND a.operator_id = %s
        AND b.operator_id = %s
    ORDER BY a.departure_time
    """
    df_times = pd.read_sql_query(query, conn, params=(date, operator1, operator2))
    print(f"Date used: {date}")
    print(f"Operators used: {operator1}, {operator2}")
    print(f"Matching departure times: {df_times.to_dict('records')}")

conn.close()
