import pandas as pd
from db_utils import get_connection, execute_query, get_actual_price, get_model_price, get_seat_types_by_schedule_id

def debug_price_data(schedule_id):
    """Debug function to check actual and model price data for a specific schedule ID"""
    # Convert schedule_id to string to match database type
    schedule_id = str(schedule_id)
    print(f"Debugging price data for schedule ID: {schedule_id}")
    
    # Get seat types for this schedule ID
    seat_types = get_seat_types_by_schedule_id(schedule_id)
    print(f"Seat types for schedule ID {schedule_id}: {seat_types}")
    
    # Get hours before departure for this schedule ID
    query = """
    SELECT DISTINCT "hours_before_departure" 
    FROM fnGetHoursBeforeDeparture
    WHERE "schedule_id" = %(schedule_id)s
    ORDER BY "hours_before_departure"
    """
    params = {'schedule_id': schedule_id}
    hours_df = execute_query(query, params)
    
    if hours_df is None or hours_df.empty:
        print(f"No hours before departure found for schedule ID {schedule_id}")
        return
    
    hours_before_departure_list = hours_df["hours_before_departure"].tolist()
    print(f"Hours before departure for schedule ID {schedule_id}: {hours_before_departure_list}")
    
    # For each seat type and hour before departure, get actual and model prices
    for seat_type in seat_types:
        print(f"\nSeat type: {seat_type}")
        for hours_before_departure in hours_before_departure_list:
            # Get actual price
            actual_price = get_actual_price(schedule_id, seat_type, hours_before_departure)
            
            # Get model price
            model_price = get_model_price(schedule_id, seat_type, hours_before_departure)
            
            print(f"  Hours before departure: {hours_before_departure}")
            print(f"    Actual price: {actual_price}")
            print(f"    Model price: {model_price}")
            
            # Check if prices are available
            if actual_price is None or model_price is None:
                print("    WARNING: One or both prices are None")
            
            # Check raw data from tables
            print("    Checking raw data from actual_price_sp table...")
            check_actual_price_query = """
            SELECT "schedule_id", "seat_type", "TimeAndDateStamp", "actual_fare"
            FROM actual_price_sp
            WHERE "schedule_id" = %(schedule_id)s
            AND "seat_type" = %(seat_type)s
            LIMIT 5
            """
            
            check_actual_params = {
                'schedule_id': schedule_id,
                'seat_type': seat_type
            }
            
            actual_df = execute_query(check_actual_price_query, check_actual_params)
            if actual_df is not None and not actual_df.empty:
                print(f"    Found {len(actual_df)} records in actual_price_sp")
                print(actual_df.head())
            else:
                print("    No records found in actual_price_sp")
            
            print("    Checking raw data from model_price_sp table...")
            check_model_price_query = """
            SELECT "schedule_id", "seat_type", "TimeAndDateStamp", "price"
            FROM model_price_sp
            WHERE "schedule_id" = %(schedule_id)s
            AND "seat_type" = %(seat_type)s
            LIMIT 5
            """
            
            check_model_params = {
                'schedule_id': schedule_id,
                'seat_type': seat_type
            }
            
            model_df = execute_query(check_model_price_query, check_model_params)
            if model_df is not None and not model_df.empty:
                print(f"    Found {len(model_df)} records in model_price_sp")
                print(model_df.head())
            else:
                print("    No records found in model_price_sp")

if __name__ == "__main__":
    # Use the schedule ID from the screenshot
    schedule_id = "62534293"
    debug_price_data(schedule_id)
