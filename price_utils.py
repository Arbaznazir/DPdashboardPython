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
    # Ensure schedule_id is a string and hours_before_departure is a float
    schedule_id = str(schedule_id)
    
    # Convert hours_before_departure to float to ensure consistent type
    try:
        hours_before_departure = float(hours_before_departure)
        print(f"Converted hours_before_departure to float: {hours_before_departure}")
    except (ValueError, TypeError) as e:
        print(f"Error converting hours_before_departure to float: {e}")
        return {}
    
    # Get all seat types for this schedule
    seat_types = get_seat_types_by_schedule_id(schedule_id)
    
    if not seat_types:
        print(f"No seat types found for schedule_id={schedule_id}")
        return {}
    
    # Get the snapshot time for the given hours_before_departure directly from seat_prices_partitioned
    snapshot_query = """
    SELECT "TimeAndDateStamp" as "SnapshotDateTime"
    FROM seat_prices_partitioned
    WHERE "schedule_id" = %(schedule_id)s 
    AND ABS("hours_before_departure"::float - %(hours_before_departure)s) < 0.01
    ORDER BY "TimeAndDateStamp" DESC
    LIMIT 1
    """
    
    snapshot_params = {
        'schedule_id': schedule_id,
        'hours_before_departure': hours_before_departure
    }
    
    print(f"DEBUG: Executing snapshot query for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
    snapshot_df = execute_query(snapshot_query, snapshot_params)
    
    if snapshot_df is None or snapshot_df.empty:
        print(f"No snapshot time found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
        # Try with a broader range as a fallback
        broader_query = """
        SELECT "TimeAndDateStamp" as "SnapshotDateTime", "hours_before_departure"
        FROM seat_prices_partitioned
        WHERE "schedule_id" = %(schedule_id)s 
        ORDER BY ABS("hours_before_departure"::float - %(hours_before_departure)s) ASC, "TimeAndDateStamp" DESC
        LIMIT 1
        """
        broader_df = execute_query(broader_query, snapshot_params)
        
        if broader_df is None or broader_df.empty:
            print(f"Still no snapshot time found with broader query")
            return {}
        
        snapshot_time = broader_df['SnapshotDateTime'].iloc[0]
        found_hours = broader_df['hours_before_departure'].iloc[0]
        print(f"Found closest hours_before_departure: {found_hours} (requested: {hours_before_departure})")
    else:
        snapshot_time = snapshot_df['SnapshotDateTime'].iloc[0]
        print(f"Found snapshot time: {snapshot_time}")
    
    # Initialize result dictionary
    result = {}
    
    # For each seat type, get actual and model prices from seat_prices_partitioned
    for seat_type in seat_types:
        # Get price data directly from seat_prices_partitioned
        price_query = """
        SELECT 
            CAST("actual_fare" AS NUMERIC) as "actual_price",
            CASE 
                WHEN "price" IS NOT NULL THEN CAST("price" AS NUMERIC)
                WHEN "final_price" IS NOT NULL THEN CAST("final_price" AS NUMERIC)
                ELSE CAST("actual_fare" AS NUMERIC) -- Fallback to actual_fare if neither price nor final_price exists
            END as "model_price"
        FROM seat_prices_partitioned
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        AND "TimeAndDateStamp" = %(snapshot_time)s
        LIMIT 1
        """
        
        price_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'snapshot_time': snapshot_time
        }
        
        price_df = execute_query(price_query, price_params)
        
        # Extract prices or set to None if not available
        actual_price = None
        model_price = None
        
        if price_df is not None and not price_df.empty:
            actual_price = price_df['actual_price'].iloc[0]
            model_price = price_df['model_price'].iloc[0]
            
            # Store in result dictionary
            result[seat_type] = {
                'actual_price': actual_price,
                'model_price': model_price
            }
        else:
            print(f"No price data found for schedule_id={schedule_id}, seat_type={seat_type}, snapshot_time={snapshot_time}")
    
    return result

def get_price_by_seat_type(schedule_id, seat_type, hours_before_departure=None):
    """
    Get actual and model prices for a specific seat type
    
    Args:
        schedule_id (str): The schedule ID
        seat_type (str): The seat type
        hours_before_departure (int, optional): Hours before departure. If None, uses the latest.
        
    Returns:
        tuple: (actual_price, model_price)
    """
    # Get all prices
    prices = get_prices_by_schedule_and_hour(schedule_id, hours_before_departure)
    
    # Return prices for the specified seat type
    if seat_type in prices:
        return prices[seat_type]['actual_price'], prices[seat_type]['model_price']
    else:
        return None, None


def get_total_seat_prices(schedule_id=None, hours_before_departure=None, date_of_journey=None):
    """
    Get total actual and model prices for all seats in a schedule
    
    Args:
        schedule_id (str): The schedule ID
        hours_before_departure (float): Hours before departure
        date_of_journey (str): Date of journey
        
    Returns:
        dict: Dictionary with total prices
    """
    from db_utils import get_seat_wise_data
    
    # Get seat-wise data
    df = get_seat_wise_data(schedule_id, hours_before_departure, date_of_journey)
    
    if df is None or df.empty:
        print(f"No seat-wise data found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
        return {
            'total_actual_price': 0,
            'total_model_price': 0,
            'price_difference': 0,
            'seat_count': 0
        }
    
    # Calculate totals
    total_actual_price = df['actual_fare'].sum()
    total_model_price = df['final_price'].sum()
    price_difference = total_actual_price - total_model_price
    seat_count = len(df)
    
    return {
        'total_actual_price': total_actual_price,
        'total_model_price': total_model_price,
        'price_difference': price_difference,
        'seat_count': seat_count
    }


def get_monthly_delta(month, year):
    """
    Get monthly delta between actual and model prices
    
    Args:
        month (int): Month number (1-12)
        year (int): Year
        
    Returns:
        dict: Dictionary with monthly delta data
    """
    print(f"Calculating monthly delta for {calendar.month_name[month]} {year}")
    
    # Query to get all schedules for the month
    schedules_query = """
    SELECT DISTINCT schedule_id
    FROM dateofjourney
    WHERE EXTRACT(MONTH FROM date_of_journey::date) = %(month)s
    AND EXTRACT(YEAR FROM date_of_journey::date) = %(year)s
    """
    
    schedules_params = {
        'month': month,
        'year': year
    }
    
    schedules_df = execute_query(schedules_query, schedules_params)
    
    if schedules_df is None or schedules_df.empty:
        print(f"No schedules found for {calendar.month_name[month]} {year}")
        return None
    
    schedule_ids = schedules_df['schedule_id'].tolist()
    schedule_count = len(schedule_ids)
    
    print(f"Found {schedule_count} schedules for {calendar.month_name[month]} {year}")
    
    # Initialize result dictionary
    result = {
        'seat_prices': {
            'schedule_count': schedule_count,
            'total_actual_price': 0,
            'total_model_price': 0,
            'price_difference': 0
        },
        'seat_wise_prices': {
            'schedule_count': schedule_count,
            'total_actual_price': 0,
            'total_model_price': 0,
            'price_difference': 0
        }
    }
    
    # Query for seat prices
    if schedule_ids:
        schedule_ids_tuple = tuple(schedule_ids) if len(schedule_ids) > 1 else f"('{schedule_ids[0]}')" 
        
        # Query for seat_prices_partitioned
        seat_prices_query = f"""
        WITH latest_snapshots AS (
            -- Get the latest snapshot for each schedule_id with hours_before_departure
            SELECT DISTINCT ON (sp.schedule_id) 
                sp.schedule_id, 
                sp."TimeAndDateStamp",
                sp.hours_before_departure
            FROM seat_prices_partitioned sp
            WHERE sp.schedule_id IN {schedule_ids_tuple}
            ORDER BY sp.schedule_id, sp.hours_before_departure ASC
        )
        SELECT 
            SUM(CAST(sp.actual_fare AS NUMERIC)) as total_actual_price,
            SUM(CAST(sp.final_price AS NUMERIC)) as total_model_price
        FROM seat_prices_partitioned sp
        JOIN latest_snapshots ls ON 
            sp.schedule_id = ls.schedule_id AND 
            sp."TimeAndDateStamp" = ls."TimeAndDateStamp"
        """
        
        seat_prices_df = execute_query(seat_prices_query)
        
        if seat_prices_df is not None and not seat_prices_df.empty:
            total_actual_price = seat_prices_df['total_actual_price'].iloc[0] or 0
            total_model_price = seat_prices_df['total_model_price'].iloc[0] or 0
            price_difference = total_actual_price - total_model_price
            
            result['seat_prices']['total_actual_price'] = total_actual_price
            result['seat_prices']['total_model_price'] = total_model_price
            result['seat_prices']['price_difference'] = price_difference
        
        # Query for seat_wise_prices_partitioned
        seat_wise_prices_query = f"""
        WITH latest_snapshots AS (
            -- Get the latest snapshot for each schedule_id and seat_number with hours_before_departure
            SELECT DISTINCT ON (swp.schedule_id, swp.seat_number) 
                swp.schedule_id, 
                swp.seat_number,
                swp."TimeAndDateStamp",
                swp.hours_before_departure
            FROM seat_wise_prices_partitioned swp
            WHERE swp.schedule_id IN {schedule_ids_tuple}
            ORDER BY swp.schedule_id, swp.seat_number, swp.hours_before_departure ASC
        )
        SELECT 
            SUM(CAST(swp.actual_fare AS NUMERIC)) as total_actual_price,
            SUM(CAST(swp.final_price AS NUMERIC)) as total_model_price
        FROM seat_wise_prices_partitioned swp
        JOIN latest_snapshots ls ON 
            swp.schedule_id = ls.schedule_id AND 
            swp.seat_number = ls.seat_number AND 
            swp."TimeAndDateStamp" = ls."TimeAndDateStamp"
        """
        
        seat_wise_prices_df = execute_query(seat_wise_prices_query)
        
        if seat_wise_prices_df is not None and not seat_wise_prices_df.empty:
            total_actual_price = seat_wise_prices_df['total_actual_price'].iloc[0] or 0
            total_model_price = seat_wise_prices_df['total_model_price'].iloc[0] or 0
            price_difference = total_actual_price - total_model_price
            
            result['seat_wise_prices']['total_actual_price'] = total_actual_price
            result['seat_wise_prices']['total_model_price'] = total_model_price
            result['seat_wise_prices']['price_difference'] = price_difference
    
    return result
