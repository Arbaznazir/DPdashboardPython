import psycopg2

# Connect to database
conn = psycopg2.connect(
    dbname="dynamic_pricing_db", 
    user="postgres", 
    password="Ghost143",
    host="localhost", 
    port="5432"
)

cur = conn.cursor()

# Check if seat_prices_with_dt table exists
cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'seat_prices_with_dt')")
table_exists = cur.fetchone()[0]
print(f"seat_prices_with_dt exists: {table_exists}")

if table_exists:
    # Check if table has data
    cur.execute("SELECT COUNT(*) FROM seat_prices_with_dt")
    count = cur.fetchone()[0]
    print(f"Records in seat_prices_with_dt: {count}")

conn.close()
