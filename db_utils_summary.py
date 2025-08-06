import pandas as pd
from db_utils import execute_query, get_schedule_ids_by_date, get_seat_types_by_schedule_id

def get_price_summary_by_date(date_of_journey):
    """
    Get summary of actual and model prices for all schedule IDs on a given date
    Returns total actual price, total model price, and delta for both seat_prices_raw and seat_wise_prices_raw
    """
    print(f"DEBUG: Getting price summary for date: {date_of_journey}")
    
    if not date_of_journey:
        print("DEBUG: No date of journey provided")
        return {
            'seat_prices': {'actual_sum': 0, 'model_sum': 0, 'delta': 0},
            'seat_wise_prices': {'actual_sum': 0, 'model_sum': 0, 'delta': 0}
        }
    
    try:
        # Get all schedule IDs for the selected date
        schedule_ids = get_schedule_ids_by_date(date_of_journey)
        print(f"DEBUG: Found schedule IDs for date {date_of_journey}: {schedule_ids}")
        
        if not schedule_ids:
            print(f"DEBUG: No schedule IDs found for date {date_of_journey}")
            return {
                'seat_prices': {'actual_sum': 0, 'model_sum': 0, 'delta': 0},
                'seat_wise_prices': {'actual_sum': 0, 'model_sum': 0, 'delta': 0}
            }
        
        # Format schedule_ids for SQL query
        if len(schedule_ids) == 1:
            # For a single ID, we need to ensure it's treated as a tuple in SQL
            schedule_ids_tuple = f"('{schedule_ids[0]}')"
            print(f"DEBUG: Single schedule ID: {schedule_ids_tuple}")
        else:
            schedule_ids_tuple = str(tuple(schedule_ids))
            print(f"DEBUG: Multiple schedule IDs: {schedule_ids_tuple}")
        
        # Query for seat_prices_raw - get latest prices for each schedule_id and seat_type
        # Using the approach from measures.py that's known to work
        seat_prices_query = f"""
        WITH latest_snapshots AS (
            -- Get the latest snapshot for each schedule_id and seat_type with hours_before_departure
            SELECT DISTINCT ON (sp.schedule_id, sp.seat_type) 
                sp.schedule_id, 
                sp.seat_type,
                sp."TimeAndDateStamp"
            FROM seat_prices_raw sp
            JOIN dateofjourney doj ON sp.schedule_id = doj.schedule_id
            JOIN fnGetHoursBeforeDeparture hbd ON sp.schedule_id = hbd.schedule_id 
                AND sp."TimeAndDateStamp" = hbd."TimeAndDateStamp"
            WHERE sp.schedule_id IN {schedule_ids_tuple}
            AND doj.date_of_journey = '{date_of_journey}'
            ORDER BY sp.schedule_id, sp.seat_type, hbd."TimeAndDateStamp" DESC
        )
        SELECT 
            sp.schedule_id,
            sp.seat_type,
            CAST(sp.actual_fare AS NUMERIC) as actual_price,
            CAST(sp.price AS NUMERIC) as model_price
        FROM seat_prices_raw sp
        JOIN latest_snapshots ls ON 
            sp.schedule_id = ls.schedule_id AND 
            sp.seat_type = ls.seat_type AND 
            sp."TimeAndDateStamp" = ls."TimeAndDateStamp"
        """
        
        # Query for seat_wise_prices_raw - get latest prices for each schedule_id and seat_number
        # Using the approach from measures.py that's known to work
        seat_wise_prices_query = f"""
        WITH latest_snapshots AS (
            -- Get the latest snapshot for each schedule_id and seat_number with hours_before_departure
            SELECT DISTINCT ON (swp.schedule_id, swp.seat_number) 
                swp.schedule_id, 
                swp.seat_number,
                swp."TimeAndDateStamp"
            FROM seat_wise_prices_raw swp
            JOIN dateofjourney doj ON swp.schedule_id = doj.schedule_id
            JOIN fnGetHoursBeforeDeparture hbd ON swp.schedule_id = hbd.schedule_id 
                AND swp."TimeAndDateStamp" = hbd."TimeAndDateStamp"
            WHERE swp.schedule_id IN {schedule_ids_tuple}
            AND doj.date_of_journey = '{date_of_journey}'
            ORDER BY swp.schedule_id, swp.seat_number, hbd."TimeAndDateStamp" DESC
        )
        SELECT 
            swp.schedule_id,
            swp.seat_number,
            CAST(swp.actual_fare AS NUMERIC) as actual_price,
            CAST(swp.final_price AS NUMERIC) as model_price
        FROM seat_wise_prices_raw swp
        JOIN latest_snapshots ls ON 
            swp.schedule_id = ls.schedule_id AND 
            swp.seat_number = ls.seat_number AND 
            swp."TimeAndDateStamp" = ls."TimeAndDateStamp"
        """
        
        # Execute queries
        print(f"DEBUG: Executing seat_prices_query: {seat_prices_query}")
        seat_prices_df = execute_query(seat_prices_query)
        print(f"DEBUG: Seat prices query result shape: {seat_prices_df.shape if seat_prices_df is not None else 'None'}")
        
        print(f"DEBUG: Executing seat_wise_prices_query: {seat_wise_prices_query}")
        seat_wise_prices_df = execute_query(seat_wise_prices_query)
        print(f"DEBUG: Seat wise prices query result shape: {seat_wise_prices_df.shape if seat_wise_prices_df is not None else 'None'}")
        
        # Calculate sums for seat_prices_raw
        seat_prices_summary = {
            'actual_sum': 0,
            'model_sum': 0,
            'delta': 0
        }
        
        if seat_prices_df is not None and not seat_prices_df.empty:
            print(f"DEBUG: Seat prices dataframe columns: {seat_prices_df.columns.tolist()}")
            print(f"DEBUG: First few rows of seat_prices_df:\n{seat_prices_df.head()}")
            
            # Convert to numeric and handle NaN values
            seat_prices_df['actual_price'] = pd.to_numeric(seat_prices_df['actual_price'], errors='coerce').fillna(0)
            seat_prices_df['model_price'] = pd.to_numeric(seat_prices_df['model_price'], errors='coerce').fillna(0)
            
            seat_prices_summary['actual_sum'] = seat_prices_df['actual_price'].sum()
            seat_prices_summary['model_sum'] = seat_prices_df['model_price'].sum()
            seat_prices_summary['delta'] = seat_prices_summary['actual_sum'] - seat_prices_summary['model_sum']
            
            print(f"DEBUG: Calculated seat_prices_summary: {seat_prices_summary}")
        
        # Calculate sums for seat_wise_prices_raw
        seat_wise_prices_summary = {
            'actual_sum': 0,
            'model_sum': 0,
            'delta': 0
        }
        
        if seat_wise_prices_df is not None and not seat_wise_prices_df.empty:
            print(f"DEBUG: Seat wise prices dataframe columns: {seat_wise_prices_df.columns.tolist()}")
            print(f"DEBUG: First few rows of seat_wise_prices_df:\n{seat_wise_prices_df.head()}")
            
            # Convert to numeric and handle NaN values
            seat_wise_prices_df['actual_price'] = pd.to_numeric(seat_wise_prices_df['actual_price'], errors='coerce').fillna(0)
            seat_wise_prices_df['model_price'] = pd.to_numeric(seat_wise_prices_df['model_price'], errors='coerce').fillna(0)
            
            seat_wise_prices_summary['actual_sum'] = seat_wise_prices_df['actual_price'].sum()
            seat_wise_prices_summary['model_sum'] = seat_wise_prices_df['model_price'].sum()
            seat_wise_prices_summary['delta'] = seat_wise_prices_summary['actual_sum'] - seat_wise_prices_summary['model_sum']
            
            print(f"DEBUG: Calculated seat_wise_prices_summary: {seat_wise_prices_summary}")
        
        return {
            'seat_prices': seat_prices_summary,
            'seat_wise_prices': seat_wise_prices_summary
        }
        
    except Exception as e:
        print(f"Error calculating price summary: {e}")
        return {
            'seat_prices': {'actual_sum': 0, 'model_sum': 0, 'delta': 0},
            'seat_wise_prices': {'actual_sum': 0, 'model_sum': 0, 'delta': 0}
        }
