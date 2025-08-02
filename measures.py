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
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['TimeAndDateStamp'] = pd.to_datetime(df['TimeAndDateStamp'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    df['actual_occupancy'] = pd.to_numeric(df['actual_occupancy'], errors='coerce')
    df['expected_occupancy'] = pd.to_numeric(df['expected_occupancy'], errors='coerce')
    
    # Calculate KPIs
    avg_actual_fare = df['actual_fare'].mean()
    avg_model_price = df['price'].mean()
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
    """Get occupancy data for charts"""
    df = get_filtered_data(schedule_id, operator_id, seat_type, hours_before_departure, date_of_journey)
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Rest of the occupancy data function would go here
    return df

def get_seat_wise_price_sum_by_hour(schedule_id):
    """Get sum of actual and model prices for all seats by hours before departure
    
    This function implements logic similar to the PowerBI DAX measures:
    - Gets the latest snapshot for each hours before departure
    - Sums up actual_fare and final_price for all seats
    - Groups by seat_type if multiple seat types exist
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
            FROM seat_prices_raw
            WHERE "schedule_id" = %(schedule_id)s
            ORDER BY "hours_before_departure" DESC
        ),
        all_seat_types AS (
            -- Get all distinct seat types for this schedule
            SELECT DISTINCT "seat_type"
            FROM seat_prices_raw
            WHERE "schedule_id" = %(schedule_id)s
        ),
        latest_snapshots AS (
            -- Get the latest snapshot for each hour before departure and seat type
            SELECT DISTINCT ON (sp."hours_before_departure", sp."seat_type") 
                sp."hours_before_departure", 
                sp."seat_type",
                sp."TimeAndDateStamp"
            FROM seat_prices_raw sp
            WHERE sp."schedule_id" = %(schedule_id)s
            ORDER BY sp."hours_before_departure", sp."seat_type", sp."TimeAndDateStamp" DESC
        )
        SELECT 
            ls."hours_before_departure",
            ls."seat_type",
            SUM(CAST(swp."actual_fare" AS NUMERIC)) as "total_actual_price",
            SUM(CAST(swp."final_price" AS NUMERIC)) as "total_model_price",
            COUNT(DISTINCT swp."seat_number") as "seat_count"
        FROM latest_snapshots ls
        JOIN seat_wise_prices_raw swp 
            ON swp."TimeAndDateStamp" = ls."TimeAndDateStamp" 
            AND swp."seat_type" = ls."seat_type"
            AND swp."schedule_id" = %(schedule_id)s
        GROUP BY ls."hours_before_departure", ls."seat_type"
        ORDER BY ls."hours_before_departure" DESC
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
