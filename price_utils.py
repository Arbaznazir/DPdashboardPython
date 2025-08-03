import pandas as pd
import calendar
from db_utils import execute_query, get_seat_types_by_schedule_id
from datetime import datetime
import numpy as np

def get_prices_by_schedule_and_hour(schedule_id, hours_before_departure):
    """
    Get actual and model prices for all seat types for a specific schedule ID and hour before departure
    
    Args:
        schedule_id (str): The schedule ID
        hours_before_departure (int): Hours before departure
        
    Returns:
        dict: Dictionary with seat types as keys and price data as values
    """
    # Ensure schedule_id is a string
    schedule_id = str(schedule_id)
    
    # Get all seat types for this schedule
    seat_types = get_seat_types_by_schedule_id(schedule_id)
    
    if not seat_types:
        print(f"No seat types found for schedule_id={schedule_id}")
        return {}
    
    # Get the snapshot time for the given hours_before_departure
    snapshot_query = """
    SELECT "TimeAndDateStamp" as "SnapshotDateTime"
    FROM fnGetHoursBeforeDeparture
    WHERE "schedule_id" = %(schedule_id)s AND "hours_before_departure" = %(hours_before_departure)s
    ORDER BY "TimeAndDateStamp" DESC
    LIMIT 1
    """
    
    snapshot_params = {
        'schedule_id': schedule_id,
        'hours_before_departure': hours_before_departure
    }
    
    snapshot_df = execute_query(snapshot_query, snapshot_params)
    
    if snapshot_df is None or snapshot_df.empty:
        print(f"No snapshot time found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
        return {}
    
    snapshot_time = snapshot_df['SnapshotDateTime'].iloc[0]
    
    # Initialize result dictionary
    result = {}
    
    # For each seat type, get actual and model prices
    for seat_type in seat_types:
        # Get actual price data
        actual_price_query = """
        SELECT "actual_fare" as "price"
        FROM actual_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        AND "TimeAndDateStamp" <= %(snapshot_time)s
        ORDER BY "TimeAndDateStamp" DESC
        LIMIT 1
        """
        
        actual_price_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'snapshot_time': snapshot_time
        }
        
        actual_price_df = execute_query(actual_price_query, actual_price_params)
        
        # Get model price data
        model_price_query = """
        SELECT "price"
        FROM model_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        AND "TimeAndDateStamp" <= %(snapshot_time)s
        ORDER BY "TimeAndDateStamp" DESC
        LIMIT 1
        """
        
        model_price_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'snapshot_time': snapshot_time
        }
        
        model_price_df = execute_query(model_price_query, model_price_params)
        
        # Extract prices or set to None if not available
        actual_price = None
        model_price = None
        
        if actual_price_df is not None and not actual_price_df.empty:
            actual_price = actual_price_df['price'].iloc[0]
            
        if model_price_df is not None and not model_price_df.empty:
            model_price = model_price_df['price'].iloc[0]
        
        # Store in result dictionary
        result[seat_type] = {
            'actual_price': actual_price,
            'model_price': model_price
        }
    
    return result

def get_total_seat_prices(schedule_id, hours_before_departure):
    """
    Get the sum of actual_fare and final_price (model price) for all seats at a specific hour before departure
    
    Args:
        schedule_id (str): The schedule ID
        hours_before_departure (int): Hours before departure
        
    Returns:
        dict: Dictionary with total actual price, total model price, and price difference
    """
    # Ensure schedule_id is a string
    schedule_id = str(schedule_id)
    
    # Get the snapshot time for the given hours_before_departure
    snapshot_query = """
    SELECT "TimeAndDateStamp" as "SnapshotDateTime"
    FROM fnGetHoursBeforeDeparture
    WHERE "schedule_id" = %(schedule_id)s AND "hours_before_departure" = %(hours_before_departure)s
    ORDER BY "TimeAndDateStamp" DESC
    LIMIT 1
    """
    
    snapshot_params = {
        'schedule_id': schedule_id,
        'hours_before_departure': hours_before_departure
    }
    
    snapshot_df = execute_query(snapshot_query, snapshot_params)
    
    if snapshot_df is None or snapshot_df.empty:
        print(f"No snapshot time found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
        return {
            'total_actual_price': None,
            'total_model_price': None,
            'price_difference': None
        }
    
    snapshot_time = snapshot_df['SnapshotDateTime'].iloc[0]
    
    # Query to get the sum of actual_fare and final_price for all seats
    query = """
    SELECT 
        SUM(CAST("actual_fare" AS NUMERIC)) as total_actual_price,
        SUM(CAST("final_price" AS NUMERIC)) as total_model_price
    FROM seat_wise_prices_raw
    WHERE "schedule_id" = %(schedule_id)s
    AND "TimeAndDateStamp" = %(snapshot_time)s
    """
    
    params = {
        'schedule_id': schedule_id,
        'snapshot_time': snapshot_time
    }
    
    result_df = execute_query(query, params)
    
    if result_df is None or result_df.empty:
        print(f"No price data found for schedule_id={schedule_id}, snapshot_time={snapshot_time}")
        return {
            'total_actual_price': None,
            'total_model_price': None,
            'price_difference': None
        }
    
    total_actual_price = result_df['total_actual_price'].iloc[0]
    total_model_price = result_df['total_model_price'].iloc[0]
    
    # Calculate price difference
    price_difference = None
    if total_actual_price is not None and total_model_price is not None:
        price_difference = total_actual_price - total_model_price
    
    return {
        'total_actual_price': total_actual_price,
        'total_model_price': total_model_price,
        'price_difference': price_difference
    }

def get_monthly_delta(month, year):
    """
    Get the sum of actual and model prices for all unique schedule IDs with zero hours before departure
    for a specific month and year, from both seat_prices_raw and seat_wise_prices_raw tables.
    
    Args:
        month (int): Month number (1-12)
        year (int): Year (e.g., 2025)
        
    Returns:
        dict: Dictionary with total prices and deltas from both tables
    """
    # Validate inputs
    if not (1 <= month <= 12):
        print(f"Invalid month: {month}. Must be between 1 and 12.")
        return None
    
    # Get the start and end dates for the month
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    print(f"Calculating monthly delta for {calendar.month_name[month]} {year} ({start_date} to {end_date})")
    
    # First check if there are any schedule IDs with zero hours before departure
    schedule_query = """
    SELECT DISTINCT "schedule_id"
    FROM fnGetHoursBeforeDeparture
    WHERE "hours_before_departure" = 0
    AND "TimeAndDateStamp" >= %(start_date)s::timestamp
    AND "TimeAndDateStamp" <= %(end_date)s::timestamp
    """
    
    schedule_params = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    schedule_df = execute_query(schedule_query, schedule_params)
    
    # If no schedules with zero hours, try to find the minimum available hour
    hours_before_departure = 0  # Default to zero
    
    if schedule_df is None or schedule_df.empty:
        print(f"No schedule IDs found for {calendar.month_name[month]} {year} with zero hours before departure")
        
        # Check if there are any schedule IDs at all for this month with any hours
        hours_query = """
        SELECT DISTINCT "hours_before_departure"
        FROM fnGetHoursBeforeDeparture
        WHERE "TimeAndDateStamp" >= %(start_date)s::timestamp
        AND "TimeAndDateStamp" <= %(end_date)s::timestamp
        ORDER BY "hours_before_departure"
        """
        
        hours_df = execute_query(hours_query, schedule_params)
        
        if hours_df is not None and not hours_df.empty:
            print(f"Found hours before departure: {hours_df['hours_before_departure'].tolist()}")
            
            # Use the minimum available hour instead
            min_hour = hours_df['hours_before_departure'].min()
            print(f"Using minimum available hour: {min_hour}")
            
            # Update the query to use the minimum hour
            min_hour_query = """
            SELECT DISTINCT "schedule_id"
            FROM fnGetHoursBeforeDeparture
            WHERE "hours_before_departure" = %(min_hour)s
            AND "TimeAndDateStamp" >= %(start_date)s::timestamp
            AND "TimeAndDateStamp" <= %(end_date)s::timestamp
            """
            
            min_hour_params = {
                'min_hour': min_hour,
                'start_date': start_date,
                'end_date': end_date
            }
            
            schedule_df = execute_query(min_hour_query, min_hour_params)
            hours_before_departure = min_hour
            
            if schedule_df is None or schedule_df.empty:
                print(f"No schedule IDs found for {calendar.month_name[month]} {year} with {min_hour} hours before departure")
                return {
                    'seat_prices': {
                        'total_actual_price': None,
                        'total_model_price': None,
                        'price_difference': None,
                        'schedule_count': 0
                    },
                    'seat_wise_prices': {
                        'total_actual_price': None,
                        'total_model_price': None,
                        'price_difference': None,
                        'schedule_count': 0
                    }
                }
        else:
            print(f"No schedule IDs found at all for {calendar.month_name[month]} {year}")
            return {
                'seat_prices': {
                    'total_actual_price': None,
                    'total_model_price': None,
                    'price_difference': None,
                    'schedule_count': 0
                },
                'seat_wise_prices': {
                    'total_actual_price': None,
                    'total_model_price': None,
                    'price_difference': None,
                    'schedule_count': 0
                }
            }
    
    schedule_ids = schedule_df['schedule_id'].tolist()
    schedule_count = len(schedule_ids)
    print(f"Found {schedule_count} unique schedule IDs for {calendar.month_name[month]} {year}")
    
    # Format schedule IDs for SQL IN clause
    schedule_ids_str = "', '".join(str(sid) for sid in schedule_ids)
    schedule_ids_sql = f"('{schedule_ids_str}')"
    
    # Query to get sum of actual and model prices from seat_prices_raw
    # Group by schedule_id first to get the latest entry for each schedule at 0 hours
    # Then sum across all schedules
    seat_prices_query = """
    WITH latest_entries AS (
        SELECT 
            "schedule_id",
            MAX("TimeAndDateStamp") as latest_timestamp
        FROM seat_prices_raw
        WHERE "schedule_id" IN {}
        AND "hours_before_departure" = 0
        AND "TimeAndDateStamp" >= %(start_date)s::timestamp
        AND "TimeAndDateStamp" <= %(end_date)s::timestamp
        GROUP BY "schedule_id"
    ),
    schedule_prices AS (
        SELECT 
            sp."schedule_id",
            CAST(sp."actual_fare" AS NUMERIC) as actual_price,
            CAST(sp."model_price" AS NUMERIC) as model_price
        FROM seat_prices_raw sp
        JOIN latest_entries le ON sp."schedule_id" = le."schedule_id" AND sp."TimeAndDateStamp" = le.latest_timestamp
        WHERE sp."hours_before_departure" = 0
    )
    SELECT 
        SUM(actual_price) as total_actual_price,
        SUM(model_price) as total_model_price
    FROM schedule_prices
    """.format(schedule_ids_sql)
    
    print(f"DEBUG - Executing seat_prices_query with {len(schedule_ids)} schedule IDs")
    seat_prices_df = execute_query(seat_prices_query, schedule_params)
    
    # Query to get sum of actual and model prices from seat_wise_prices_raw
    # Group by schedule_id first to get the latest entry for each schedule
    # Then sum across all schedules
    seat_wise_prices_query = """
    WITH latest_timestamps AS (
        SELECT 
            "schedule_id",
            MAX("TimeAndDateStamp") as latest_timestamp
        FROM fnGetHoursBeforeDeparture
        WHERE "schedule_id" IN {}
        AND "hours_before_departure" = 0
        AND "TimeAndDateStamp" >= %(start_date)s::timestamp
        AND "TimeAndDateStamp" <= %(end_date)s::timestamp
        GROUP BY "schedule_id"
    ),
    schedule_seat_prices AS (
        SELECT 
            swp."schedule_id",
            CAST(swp."actual_fare" AS NUMERIC) as actual_price,
            CAST(swp."final_price" AS NUMERIC) as model_price
        FROM seat_wise_prices_raw swp
        JOIN latest_timestamps lt ON swp."schedule_id" = lt."schedule_id" 
        WHERE swp."TimeAndDateStamp" = lt.latest_timestamp
    )
    SELECT 
        SUM(actual_price) as total_actual_price,
        SUM(model_price) as total_model_price
    FROM schedule_seat_prices
    """.format(schedule_ids_sql)
    
    print(f"DEBUG - Executing seat_wise_prices_query with {len(schedule_ids)} schedule IDs")
    seat_wise_prices_df = execute_query(seat_wise_prices_query, schedule_params)
    
    # Process seat_prices_raw results
    seat_prices_result = {
        'total_actual_price': None,
        'total_model_price': None,
        'price_difference': None,
        'schedule_count': schedule_count
    }
    
    if seat_prices_df is not None and not seat_prices_df.empty:
        total_actual_price = seat_prices_df['total_actual_price'].iloc[0]
        total_model_price = seat_prices_df['total_model_price'].iloc[0]
        
        print(f"DEBUG - Raw seat_prices values: actual={total_actual_price}, model={total_model_price}")
        
        # Handle NaN values
        if pd.isna(total_actual_price):
            total_actual_price = None
            print("DEBUG - actual_price is NaN, setting to None")
        if pd.isna(total_model_price):
            total_model_price = None
            print("DEBUG - model_price is NaN, setting to None")
            
        price_difference = None
        if total_actual_price is not None and total_model_price is not None:
            # Calculate actual difference (not absolute value) to show if actual > model
            price_difference = total_actual_price - total_model_price
            print(f"DEBUG - Calculated price_difference: {price_difference}")
            
        seat_prices_result = {
            'total_actual_price': total_actual_price,
            'total_model_price': total_model_price,
            'price_difference': price_difference,
            'schedule_count': schedule_count
        }
    
    # Process seat_wise_prices_raw results
    seat_wise_prices_result = {
        'total_actual_price': None,
        'total_model_price': None,
        'price_difference': None,
        'schedule_count': schedule_count
    }
    
    if seat_wise_prices_df is not None and not seat_wise_prices_df.empty:
        total_actual_price = seat_wise_prices_df['total_actual_price'].iloc[0]
        total_model_price = seat_wise_prices_df['total_model_price'].iloc[0]
        
        print(f"DEBUG - Raw seat_wise_prices values: actual={total_actual_price}, model={total_model_price}")
        
        # Handle NaN values
        if pd.isna(total_actual_price):
            total_actual_price = None
            print("DEBUG - actual_price is NaN, setting to None")
        if pd.isna(total_model_price):
            total_model_price = None
            print("DEBUG - model_price is NaN, setting to None")
            
        price_difference = None
        if total_actual_price is not None and total_model_price is not None:
            # Calculate actual difference (not absolute value) to show if actual > model
            price_difference = total_actual_price - total_model_price
            print(f"DEBUG - Calculated price_difference: {price_difference}")
            
        seat_wise_prices_result = {
            'total_actual_price': total_actual_price,
            'total_model_price': total_model_price,
            'price_difference': price_difference,
            'schedule_count': schedule_count
        }
    
    # Print final results for debugging
    print(f"DEBUG - Final seat_prices result: {seat_prices_result}")
    print(f"DEBUG - Final seat_wise_prices result: {seat_wise_prices_result}")
    
    return {
        'seat_prices': seat_prices_result,
        'seat_wise_prices': seat_wise_prices_result
    }
