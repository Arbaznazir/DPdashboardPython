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
    
    # Get the snapshot time for the given hours_before_departure directly from seat_prices_partitioned
    snapshot_query = """
    SELECT "TimeAndDateStamp" as "SnapshotDateTime"
    FROM seat_prices_partitioned
    WHERE "schedule_id" = %(schedule_id)s 
    AND ABS("hours_before_departure" - %(hours_before_departure)s) < 0.01
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
        ORDER BY ABS("hours_before_departure" - %(hours_before_departure)s) ASC, "TimeAndDateStamp" DESC
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
            CAST("final_price" AS NUMERIC) as "model_price"
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
