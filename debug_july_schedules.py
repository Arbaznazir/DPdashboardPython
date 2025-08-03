"""
Direct SQL debug script to verify July 2025 schedule IDs with 0 hours before departure
"""
import pandas as pd
import calendar
from db_utils import execute_query

def debug_july_schedules():
    """Check for July 2025 schedule IDs with 0 hours before departure"""
    month = 7  # July
    year = 2025
    
    # Get the start and end dates for the month
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    print(f"Checking for schedule IDs between {start_date} and {end_date}")
    
    # Direct query to check for schedule IDs with 0 hours before departure
    schedule_query = """
    SELECT DISTINCT "schedule_id"
    FROM fnGetHoursBeforeDeparture
    WHERE "hours_before_departure" = 0
    AND "TimeAndDateStamp" >= %(start_date)s::date
    AND "TimeAndDateStamp" <= %(end_date)s::date
    """
    
    schedule_params = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    schedule_df = execute_query(schedule_query, schedule_params)
    
    if schedule_df is None or schedule_df.empty:
        print(f"No schedule IDs found for {month}/{year} with 0 hours before departure")
    else:
        print(f"Found {len(schedule_df)} schedule IDs for {month}/{year} with 0 hours before departure:")
        print(schedule_df['schedule_id'].tolist())
    
    # Check if there are any schedule IDs at all for this month
    all_schedules_query = """
    SELECT DISTINCT "schedule_id"
    FROM fnGetHoursBeforeDeparture
    WHERE "TimeAndDateStamp" >= %(start_date)s::date
    AND "TimeAndDateStamp" <= %(end_date)s::date
    """
    
    all_schedules_df = execute_query(all_schedules_query, schedule_params)
    
    if all_schedules_df is None or all_schedules_df.empty:
        print(f"No schedule IDs found at all for {month}/{year}")
    else:
        print(f"Found {len(all_schedules_df)} total schedule IDs for {month}/{year} (any hours):")
        print(all_schedules_df['schedule_id'].head(5).tolist())
    
    # Check available hours before departure
    hours_query = """
    SELECT DISTINCT "hours_before_departure"
    FROM fnGetHoursBeforeDeparture
    WHERE "TimeAndDateStamp" >= %(start_date)s::date
    AND "TimeAndDateStamp" <= %(end_date)s::date
    ORDER BY "hours_before_departure"
    """
    
    hours_df = execute_query(hours_query, schedule_params)
    
    if hours_df is None or hours_df.empty:
        print(f"No hours before departure found for {month}/{year}")
    else:
        print(f"Available hours before departure for {month}/{year}:")
        print(hours_df['hours_before_departure'].tolist())

if __name__ == "__main__":
    debug_july_schedules()
