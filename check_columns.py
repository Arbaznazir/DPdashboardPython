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

# Check columns in seat_prices_with_dt
cur.execute("""
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'seat_prices_with_dt'
ORDER BY ordinal_position
""")

columns = cur.fetchall()
print("Columns in seat_prices_with_dt:")
for col in columns:
    print(f"- {col[0]}")

conn.close()
