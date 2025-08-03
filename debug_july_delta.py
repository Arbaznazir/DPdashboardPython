"""
Enhanced debug script to test July 2025 monthly delta calculation
"""
import pandas as pd
import calendar
import traceback
from price_utils import get_monthly_delta, execute_query

# Test for July 2025
month = 7  # July
year = 2025

print(f"Testing monthly delta for {calendar.month_name[month]} {year}")

# First, let's check if there are any schedule IDs with zero hours before departure in July 2025
start_date = f"{year}-{month:02d}-01"
_, last_day = calendar.monthrange(year, month)
end_date = f"{year}-{month:02d}-{last_day}"

print(f"Checking for schedule IDs between {start_date} and {end_date}")

# Direct query to check for schedule IDs
schedule_query = """
SELECT DISTINCT "schedule_id"
FROM fnGetHoursBeforeDeparture
WHERE "hours_before_departure" = 0
AND "TimeAndDateStamp" >= %(start_date)s
AND "TimeAndDateStamp" <= %(end_date)s
"""

schedule_params = {
    'start_date': start_date,
    'end_date': end_date
}

try:
    print("Executing direct query to check for schedule IDs...")

    schedule_df = execute_query(schedule_query, schedule_params)
    
    if schedule_df is None or schedule_df.empty:
        print(f"No schedule IDs found for {calendar.month_name[month]} {year} with zero hours before departure")

        # Let's check if there are any schedule IDs at all for this month
        all_schedules_query = """
        SELECT DISTINCT "schedule_id"
        FROM fnGetHoursBeforeDeparture
        WHERE "TimeAndDateStamp" >= %(start_date)s
        AND "TimeAndDateStamp" <= %(end_date)s
        """
        
        all_schedules_df = execute_query(all_schedules_query, schedule_params)
        
        if all_schedules_df is None or all_schedules_df.empty:
            print(f"No schedule IDs found at all for {calendar.month_name[month]} {year}")

        else:
            print(f"Found {len(all_schedules_df)} schedule IDs for {calendar.month_name[month]} {year} (any hours before departure)")

            print(f"Sample schedule IDs: {all_schedules_df['schedule_id'].head(5).tolist()}")

            
            # Check if there are any with hours_before_departure
            hours_query = """
            SELECT DISTINCT "hours_before_departure"
            FROM fnGetHoursBeforeDeparture
            WHERE "TimeAndDateStamp" >= %(start_date)s
            AND "TimeAndDateStamp" <= %(end_date)s
            ORDER BY "hours_before_departure"
            """
            
            hours_df = execute_query(hours_query, schedule_params)
            
            if hours_df is not None and not hours_df.empty:
                print(f"Available hours before departure: {hours_df['hours_before_departure'].tolist()}")

                
                # If 0 is not available, let's try with the minimum available hour
                if 0 not in hours_df['hours_before_departure'].tolist() and not hours_df.empty:
                    min_hour = hours_df['hours_before_departure'].min()
                    print(f"Zero hours not found, trying with minimum hour: {min_hour}")

                    
                    min_hour_query = """
                    SELECT DISTINCT "schedule_id"
                    FROM fnGetHoursBeforeDeparture
                    WHERE "hours_before_departure" = %(min_hour)s
                    AND "TimeAndDateStamp" >= %(start_date)s
                    AND "TimeAndDateStamp" <= %(end_date)s
                    """
                    
                    min_hour_params = {
                        'min_hour': min_hour,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    
                    min_hour_df = execute_query(min_hour_query, min_hour_params)
                    
                    if min_hour_df is not None and not min_hour_df.empty:
                        print(f"Found {len(min_hour_df)} schedule IDs with {min_hour} hours before departure")

    else:
        print(f"Found {len(schedule_df)} schedule IDs for {calendar.month_name[month]} {year} with zero hours before departure")

        print(f"Schedule IDs: {schedule_df['schedule_id'].tolist()}")

except Exception as e:
    print(f"Error executing query: {str(e)}")

    traceback.print_exc()

# Now get the monthly delta data
print("\nNow testing get_monthly_delta function...")

try:
    monthly_data = get_monthly_delta(month, year)
except Exception as e:
    print(f"Error in get_monthly_delta: {str(e)}")

    traceback.print_exc()

# Print the results
print(f"\nResults for {calendar.month_name[month]} {year}:")
print(f"Monthly data: {monthly_data}")

if monthly_data:
    # Print seat_prices results
    seat_prices = monthly_data.get('seat_prices', {})
    print("\n1. SEAT PRICES DATA:")
    print(f"   Schedule Count: {seat_prices.get('schedule_count')}")
    print(f"   Total Actual Price: {seat_prices.get('total_actual_price')}")
    print(f"   Total Model Price: {seat_prices.get('total_model_price')}")
    print(f"   Price Difference: {seat_prices.get('price_difference')}")
    
    # Print seat_wise_prices results
    seat_wise_prices = monthly_data.get('seat_wise_prices', {})
    print("\n2. SEAT WISE PRICES DATA:")
    print(f"   Schedule Count: {seat_wise_prices.get('schedule_count')}")
    print(f"   Total Actual Price: {seat_wise_prices.get('total_actual_price')}")
    print(f"   Total Model Price: {seat_wise_prices.get('total_model_price')}")
    print(f"   Price Difference: {seat_wise_prices.get('price_difference')}")
else:
    print("No data returned from get_monthly_delta")
