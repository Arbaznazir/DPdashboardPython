# This is a temporary file to fix the actual seat-wise price query
# Replace the actual_seat_wise_query in price_comparison.py with this:

actual_seat_wise_query = """
WITH relevant_schedules AS (
    SELECT schedule_id 
    FROM seat_prices_with_dt 
    WHERE date_of_journey = %s 
        AND operator_id = %s 
        AND departure_time = %s
),
latest_snapshots AS (
    SELECT DISTINCT ON (swp.schedule_id, swp.seat_number)
        swp.schedule_id,
        swp.seat_number,
        swp."TimeAndDateStamp"
    FROM seat_wise_prices_with_dt swp
    JOIN relevant_schedules rs ON swp.schedule_id = rs.schedule_id
    WHERE swp.travel_date = %s
    ORDER BY swp.schedule_id, swp.seat_number, swp."TimeAndDateStamp" DESC
)
SELECT 
    swp.seat_number,
    swp.seat_type,
    swp.actual_fare as final_price,
    swp.schedule_id
FROM seat_wise_prices_with_dt swp
JOIN latest_snapshots ls 
    ON swp.schedule_id = ls.schedule_id 
    AND swp.seat_number = ls.seat_number 
    AND swp."TimeAndDateStamp" = ls."TimeAndDateStamp"
"""
