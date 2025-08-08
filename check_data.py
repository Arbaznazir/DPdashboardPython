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

# Check sample data
query = """
SELECT operator_id, date_of_journey, departure_time
FROM seat_prices_with_dt
LIMIT 10
"""
df = pd.read_sql_query(query, conn)
print("Sample data from seat_prices_with_dt:")
print(df)

# Check for NULL departure_time values
query = """
SELECT COUNT(*) as null_count
FROM seat_prices_with_dt
WHERE departure_time IS NULL
"""
null_count = pd.read_sql_query(query, conn)
print(f"\nRecords with NULL departure_time: {null_count['null_count'].iloc[0]}")

# Check distinct operator_id values
query = """
SELECT DISTINCT operator_id
FROM seat_prices_with_dt
"""
operators = pd.read_sql_query(query, conn)
print(f"\nDistinct operator_id values: {operators['operator_id'].tolist()}")

conn.close()
