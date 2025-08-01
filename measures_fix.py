import pandas as pd
import numpy as np
from db_utils import get_filtered_data, get_seat_wise_data

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
    
    # Convert columns to numeric
    df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
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
    
    # Convert columns to numeric and datetime
    df['actual_occupancy'] = pd.to_numeric(df['actual_occupancy'], errors='coerce')
    df['expected_occupancy'] = pd.to_numeric(df['expected_occupancy'], errors='coerce')
    # Specify format explicitly to avoid warnings
    df['TimeAndDateStamp'] = pd.to_datetime(df['TimeAndDateStamp'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    
    # Sort by timestamp
    df = df.sort_values('TimeAndDateStamp')
    
    return df

def get_seat_wise_analysis(schedule_id=None, hours_before_departure=None, date_of_journey=None):
    """Get seat-wise analysis data"""
    df = get_seat_wise_data(schedule_id, hours_before_departure, date_of_journey)
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Convert columns to numeric
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['sales_percentage'] = pd.to_numeric(df['sales_percentage'], errors='coerce')
    
    return df
