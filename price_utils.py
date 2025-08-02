import pandas as pd
from db_utils import execute_query, get_seat_types_by_schedule_id

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
        price_difference = abs(total_model_price - total_actual_price)
    
    return {
        'total_actual_price': total_actual_price,
        'total_model_price': total_model_price,
        'price_difference': price_difference
    }
