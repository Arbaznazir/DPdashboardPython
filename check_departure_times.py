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

# Check if departure_time column has any non-null values
cur.execute("SELECT COUNT(*) FROM seat_prices_with_dt WHERE departure_time IS NOT NULL")
non_null_count = cur.fetchone()[0]
print(f"Records with non-NULL departure_time: {non_null_count}")

# Check sample of departure_time values
cur.execute("SELECT operator_id, date_of_journey, departure_time FROM seat_prices_with_dt WHERE departure_time IS NOT NULL LIMIT 5")
sample = cur.fetchall()
print("\nSample of departure_time values:")
for row in sample:
    print(f"Operator: {row[0]}, Date: {row[1]}, Time: {row[2]}")

# Check if there are any matching departure times between operators
cur.execute("""
SELECT a.operator_id as op1, b.operator_id as op2, a.date_of_journey, a.departure_time, COUNT(*) as match_count
FROM seat_prices_with_dt a
JOIN seat_prices_with_dt b ON a.departure_time = b.departure_time AND a.date_of_journey = b.date_of_journey
WHERE a.operator_id != b.operator_id
AND a.departure_time IS NOT NULL
GROUP BY a.operator_id, b.operator_id, a.date_of_journey, a.departure_time
LIMIT 5
""")
matches = cur.fetchall()
print("\nMatching departure times between operators:")
if matches:
    for match in matches:
        print(f"Operator1: {match[0]}, Operator2: {match[1]}, Date: {match[2]}, Time: {match[3]}, Count: {match[4]}")
else:
    print("No matching departure times found between different operators")

conn.close()
