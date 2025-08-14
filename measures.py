import pandas as pd
import numpy as np
from db_utils import get_filtered_data, get_seat_wise_data, execute_query

def calculate_price_delta(actual_fare, model_price):
    """Calculate the delta between actual fare and model price"""
    if pd.isna(actual_fare) or pd.isna(model_price):
        return 0
    return float(actual_fare) - float(model_price)

def calculate_price_delta_percentage(actual_fare, model_price):
    """Calculate the percentage delta between actual fare and model price"""
    if pd.isna(actual_fare) or pd.isna(model_price) or float(model_price) == 0:
        return 0
    return (float(actual_fare) - float(model_price)) / float(model_price) * 100

def get_kpi_data(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Get KPI data for the dashboard"""
    try:
        df = get_filtered_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
        
        if df is None or df.empty:
            return {
                'avg_actual_fare': 0,
                'avg_model_price': 0,
                'avg_delta': 0,
                'avg_delta_percentage': 0,
                'avg_occupancy': 0,
                'avg_expected_occupancy': 0
            }
        
        # Convert columns to numeric and datetime
        df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce')
        
        # Handle both price and final_price columns for different tables
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            model_price_col = 'price'
        elif 'final_price' in df.columns:
            df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce')
            model_price_col = 'final_price'
        else:
            print("WARNING: Neither price nor final_price column found in dataframe")
            model_price_col = None
        
        # Handle TimeAndDateStamp more carefully
        if 'TimeAndDateStamp' in df.columns:
            try:
                df['TimeAndDateStamp'] = pd.to_datetime(df['TimeAndDateStamp'], errors='coerce')
            except Exception as e:
                print(f"Error converting TimeAndDateStamp: {str(e)}")
                # Continue without the conversion if it fails
                pass
                
        df['actual_occupancy'] = pd.to_numeric(df['actual_occupancy'], errors='coerce')
        df['expected_occupancy'] = pd.to_numeric(df['expected_occupancy'], errors='coerce')
        
        # Calculate KPIs
        avg_actual_fare = df['actual_fare'].mean()
        
        # Use the appropriate model price column
        if model_price_col and model_price_col in df.columns:
            avg_model_price = df[model_price_col].mean()
        else:
            avg_model_price = 0
            print(f"WARNING: Model price column not found in dataframe. Columns: {df.columns.tolist()}")
        
        avg_delta = avg_actual_fare - avg_model_price
        avg_delta_percentage = (avg_delta / avg_model_price * 100) if avg_model_price != 0 else 0
        avg_occupancy = df['actual_occupancy'].mean()
        avg_expected_occupancy = df['expected_occupancy'].mean()
        
        return {
            'avg_actual_fare': round(avg_actual_fare, 2),
            'avg_model_price': round(avg_model_price, 2),
            'avg_delta': round(avg_delta, 2),
            'avg_delta_percentage': round(avg_delta_percentage, 2),
            'avg_occupancy': round(avg_occupancy, 2),
            'avg_expected_occupancy': round(avg_expected_occupancy, 2)
        }
    except Exception as e:
        print(f"Error in get_kpi_data: {str(e)}")
        return {
            'avg_actual_fare': 0,
            'avg_model_price': 0,
            'avg_delta': 0,
            'avg_delta_percentage': 0,
            'avg_occupancy': 0,
            'avg_expected_occupancy': 0
        }
    


def get_price_trend_data(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Get price trend data for the chart"""
    df = get_filtered_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Convert columns to numeric and datetime
    df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    # Specify format explicitly to avoid warnings
    df['TimeAndDateStamp'] = pd.to_datetime(df['TimeAndDateStamp'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    
    # Sort by timestamp
    df = df.sort_values('TimeAndDateStamp')
    
    # Calculate delta
    df['delta'] = df.apply(lambda row: calculate_price_delta(row['actual_fare'], row['price']), axis=1)
    
    return df

def get_price_delta_data(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Get price delta data for the chart"""
    df = get_filtered_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Convert columns to numeric and datetime
    df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    # Specify format explicitly to avoid warnings
    df['TimeAndDateStamp'] = pd.to_datetime(df['TimeAndDateStamp'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    
    # Sort by timestamp
    df = df.sort_values('TimeAndDateStamp')
    
    # Calculate delta
    df['delta'] = df.apply(lambda row: calculate_price_delta(row['actual_fare'], row['price']), axis=1)
    
    return df

def get_occupancy_data(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Get occupancy data for charts - using partitioned table for better performance"""
    # Return empty DataFrame if no schedule_id is provided
    if schedule_id is None:
        return pd.DataFrame()
    
    # Query to get occupancy data with DISTINCT ON to get latest record per seat_type and hours_before_departure
    query = """
    WITH latest_snapshots AS (
        SELECT DISTINCT ON ("seat_type", "hours_before_departure") 
            "schedule_id",
            "hours_before_departure",
            "actual_occupancy"::NUMERIC(10,2) as "actual_occupancy",
            "expected_occupancy"::NUMERIC(10,2) as "expected_occupancy",
            "seat_type",
            "TimeAndDateStamp"
        FROM 
            seat_prices_partitioned
        WHERE 
            "schedule_id" = %(schedule_id)s
            AND "actual_occupancy" IS NOT NULL
            AND "expected_occupancy" IS NOT NULL
        ORDER BY 
            "seat_type", "hours_before_departure", "TimeAndDateStamp" DESC
    )
    SELECT * FROM latest_snapshots
    ORDER BY "seat_type", "hours_before_departure" DESC
    """
    
    params = {'schedule_id': schedule_id}
    df = execute_query(query, params)
    
    # Return empty DataFrame if no data was found
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Get the latest record for each seat_type and hours_before_departure combination
    # First, sort by TimeAndDateStamp in descending order (if available)
    if 'TimeAndDateStamp' in df.columns:
        df = df.sort_values(['seat_type', 'hours_before_departure', 'TimeAndDateStamp'], 
                           ascending=[True, True, False])
    
    # Then take the first record for each group (which will be the latest due to sorting)
    df = df.groupby(['seat_type', 'hours_before_departure']).first().reset_index()
    
    # Convert occupancy values to numeric and round to 2 decimal places
    df['actual_occupancy'] = pd.to_numeric(df['actual_occupancy'], errors='coerce').round(2)
    df['expected_occupancy'] = pd.to_numeric(df['expected_occupancy'], errors='coerce').round(2)
    
    # Drop any rows with NaN values after conversion
    df = df.dropna(subset=['actual_occupancy', 'expected_occupancy'])
    
    # Sort by seat_type and hours_before_departure in descending order (highest to lowest)
    df = df.sort_values(['seat_type', 'hours_before_departure'], ascending=[True, False])
    
    return df

def get_seat_wise_price_sum_by_hour(schedule_id):
    """Get sum of actual and model prices for all seats by hours before departure
    
    This function implements logic similar to the PowerBI DAX measures:
    - Gets the latest snapshot for each hours before departure
    - Sums up actual_fare and final_price for all seats
    - Groups by seat_type if multiple seat types exist
    - Uses partitioned tables for better performance
    """
    if not schedule_id:
        return pd.DataFrame()
        
    try:
        # Convert schedule_id to string to ensure consistency
        schedule_id = str(schedule_id)
        
        # Query to get the sum of actual_fare and final_price by hours before departure and seat_type
        query = """
        WITH all_hours AS (
            -- Get all distinct hours before departure for this schedule
            SELECT DISTINCT "hours_before_departure"
            FROM seat_prices_partitioned
            WHERE "schedule_id" = %(schedule_id)s
            ORDER BY "hours_before_departure" DESC
        ),
        all_seat_types AS (
            -- Get all distinct seat types for this schedule
            SELECT DISTINCT "seat_type"
            FROM seat_prices_partitioned
            WHERE "schedule_id" = %(schedule_id)s
        ),
        latest_snapshots AS (
            -- Get the latest snapshot for each hour before departure and seat type
            SELECT DISTINCT ON (sp."hours_before_departure", sp."seat_type") 
                sp."hours_before_departure", 
                sp."seat_type",
                sp."TimeAndDateStamp"
            FROM seat_prices_partitioned sp
            WHERE sp."schedule_id" = %(schedule_id)s
            ORDER BY sp."hours_before_departure", sp."seat_type", sp."TimeAndDateStamp" DESC
        ),
        latest_seat_data AS (
            -- Get the latest data for each seat number within each snapshot
            SELECT DISTINCT ON (swp."seat_number", ls."hours_before_departure", ls."seat_type")
                ls."hours_before_departure",
                ls."seat_type",
                swp."seat_number",
                CAST(swp."actual_fare" AS NUMERIC) as "actual_fare",
                CAST(swp."final_price" AS NUMERIC) as "final_price"
            FROM latest_snapshots ls
            JOIN seat_wise_prices_partitioned swp 
                ON swp."TimeAndDateStamp" = ls."TimeAndDateStamp" 
                AND swp."seat_type" = ls."seat_type"
                AND swp."schedule_id" = %(schedule_id)s
            ORDER BY 
                swp."seat_number", ls."hours_before_departure", ls."seat_type", swp."TimeAndDateStamp" DESC
        )
        SELECT 
            "hours_before_departure",
            "seat_type",
            SUM("actual_fare") as "total_actual_price",
            SUM("final_price") as "total_model_price",
            COUNT(DISTINCT "seat_number") as "seat_count"
        FROM latest_seat_data
        GROUP BY "hours_before_departure", "seat_type"
        ORDER BY "hours_before_departure" DESC
        """
        
        params = {'schedule_id': schedule_id}
        df = execute_query(query, params)
        
        if df is None or df.empty:
            print(f"No seat-wise price sum data found for schedule_id={schedule_id}")
            return pd.DataFrame()
            
        # Convert columns to numeric
        df['total_actual_price'] = pd.to_numeric(df['total_actual_price'], errors='coerce')
        df['total_model_price'] = pd.to_numeric(df['total_model_price'], errors='coerce')
        df['hours_before_departure'] = pd.to_numeric(df['hours_before_departure'], errors='coerce')
        
        # Sort by hours_before_departure
        df = df.sort_values('hours_before_departure', ascending=False)
        
        return df
    except Exception as e:
        print(f"Error getting seat-wise price sum data: {str(e)}")
        return pd.DataFrame()
    
    return df

def get_seat_wise_analysis(schedule_id=None, hours_before_departure=None, date_of_journey=None):
    """Get seat-wise analysis data"""
    df = get_seat_wise_data(schedule_id, hours_before_departure, date_of_journey)
    
    if df is None or df.empty:
        # Return an empty DataFrame with all required columns
        return pd.DataFrame({
            'actual_fare': [],
            'final_price': [],
            'sales_percentage': [],
            'seat_type': [],
            'seat_number': [],
            'delta': []
        })
    
    # Make sure required columns exist
    required_columns = ['actual_fare', 'sales_percentage', 'seat_type', 'seat_number']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 0 if col != 'seat_type' and col != 'seat_number' else 'Unknown'
    
    # Add final_price column for the scatter chart
    df['final_price'] = df['actual_fare']
    
    # Add delta column if it doesn't exist
    if 'delta' not in df.columns:
        df['delta'] = 0
    
    # Convert columns to numeric
    df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce')
    df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce')
    df['sales_percentage'] = pd.to_numeric(df['sales_percentage'], errors='coerce')
    df['delta'] = pd.to_numeric(df['delta'], errors='coerce')
    
    return df
