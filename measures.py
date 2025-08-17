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

def get_kpi_data(df, model_price_col=None):
    """Get KPI data for the dashboard"""
    try:
        print(f"\n\n===== DEBUG: get_kpi_data called with: =====")
        print(f"DataFrame shape: {df.shape if df is not None else 'None'}")
        print(f"model_price_col: {model_price_col}")
        
        # Check if we have a valid DataFrame to work with
        if df is None or df.empty:
            print("DataFrame is None or empty, returning zeros")
            return {
                'avg_actual_fare': 0,
                'avg_model_price': 0,
                'avg_delta': 0,
                'avg_delta_pct': 0,
                'avg_occupancy': 0,
                'avg_expected_occupancy': 0
            }
        
        print(f"DataFrame shape: {df.shape}")
        print(f"DataFrame columns: {df.columns.tolist()}")
        print(f"First row: {df.iloc[0].to_dict() if not df.empty else 'Empty DataFrame'}")
        
        # Convert columns to numeric
        print("Converting columns to numeric")
        
        # Handle actual_fare column
        if 'actual_fare' in df.columns:
            df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce')
            print(f"actual_fare values: {df['actual_fare'].tolist()}")
        else:
            print("WARNING: actual_fare column not found")
            df['actual_fare'] = 0
        
        # Use the provided model_price_col or determine it from the DataFrame
        if model_price_col is None:
            # Auto-detect model price column if not provided
            if 'price' in df.columns:
                model_price_col = 'price'
                print(f"Auto-detected model_price_col: 'price'")
            elif 'final_price' in df.columns:
                model_price_col = 'final_price'
                print(f"Auto-detected model_price_col: 'final_price'")
            else:
                # If we have actual_fare but no model price, use actual_fare as model price
                if 'actual_fare' in df.columns:
                    print("Using actual_fare as model price")
                    df['price'] = df['actual_fare']
                    model_price_col = 'price'
                else:
                    print("WARNING: No suitable model price column found")
                    model_price_col = None
        
        # Ensure the model_price_col exists and convert to numeric
        if model_price_col and model_price_col in df.columns:
            df[model_price_col] = pd.to_numeric(df[model_price_col], errors='coerce')
            print(f"{model_price_col} values: {df[model_price_col].tolist()}")
        else:
            print(f"WARNING: Model price column '{model_price_col}' not found in dataframe. Columns: {df.columns.tolist()}")
            # Create a fallback if needed
            if 'actual_fare' in df.columns:
                df['price'] = df['actual_fare']
                model_price_col = 'price'
                print("Created fallback model price column using actual_fare")
            else:
                model_price_col = None
        
        # Handle TimeAndDateStamp more carefully
        # Check for both uppercase and lowercase versions of the column
        if 'timeanddatestamp' in df.columns:
            try:
                print("Found lowercase timeanddatestamp column")
                df['timeanddatestamp'] = pd.to_datetime(df['timeanddatestamp'], errors='coerce')
            except Exception as e:
                print(f"Error converting timeanddatestamp: {str(e)}")
        elif 'TimeAndDateStamp' in df.columns:
            try:
                print("Found uppercase TimeAndDateStamp column")
                df['TimeAndDateStamp'] = pd.to_datetime(df['TimeAndDateStamp'], errors='coerce')
            except Exception as e:
                print(f"Error converting TimeAndDateStamp: {str(e)}")
                # Continue without the conversion if it fails
                pass
        
        # Handle occupancy columns
        if 'actual_occupancy' in df.columns:
            df['actual_occupancy'] = pd.to_numeric(df['actual_occupancy'], errors='coerce')
        else:
            print("WARNING: actual_occupancy column not found")
            df['actual_occupancy'] = 0
            
        if 'expected_occupancy' in df.columns:
            df['expected_occupancy'] = pd.to_numeric(df['expected_occupancy'], errors='coerce')
        else:
            print("WARNING: expected_occupancy column not found")
            df['expected_occupancy'] = 0
        
        # Calculate KPIs
        print("Calculating KPIs")
        # Convert price columns to numeric to prevent string operation errors
        df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce').fillna(0)
        
        if model_price_col and model_price_col in df.columns:
            df[model_price_col] = pd.to_numeric(df[model_price_col], errors='coerce').fillna(0)
            avg_model_price = df[model_price_col].mean()
        else:
            avg_model_price = 0
            
        avg_actual_fare = df['actual_fare'].mean()
        
        # Calculate delta and delta percentage
        avg_delta = float(avg_actual_fare) - float(avg_model_price)
        
        # Avoid division by zero
        if avg_model_price != 0:
            avg_delta_pct = (avg_delta / avg_model_price) * 100
        else:
            avg_delta_pct = 0
            
        avg_occupancy = df['actual_occupancy'].mean()
        avg_expected_occupancy = df['expected_occupancy'].mean()
        
        print(f"KPI Calculation Results:")
        print(f"avg_actual_fare: {avg_actual_fare}")
        print(f"avg_model_price: {avg_model_price}")
        print(f"avg_delta: {avg_delta}")
        print(f"avg_delta_pct: {avg_delta_pct}")
        print(f"avg_occupancy: {avg_occupancy}")
        print(f"avg_expected_occupancy: {avg_expected_occupancy}")
        
        # Return the KPI data
        return {
            'avg_actual_fare': round(avg_actual_fare, 2) if not pd.isna(avg_actual_fare) else 0,
            'avg_model_price': round(avg_model_price, 2) if not pd.isna(avg_model_price) else 0,
            'avg_delta': round(avg_delta, 2) if not pd.isna(avg_delta) else 0,
            'avg_delta_pct': round(avg_delta_pct, 2) if not pd.isna(avg_delta_pct) else 0,
            'avg_occupancy': round(avg_occupancy, 2) if not pd.isna(avg_occupancy) else 0,
            'avg_expected_occupancy': round(avg_expected_occupancy, 2) if not pd.isna(avg_expected_occupancy) else 0
        }
    except Exception as e:
        print(f"Error in get_kpi_data: {str(e)}")
        return {
            'avg_actual_fare': 0,
            'avg_model_price': 0,
            'avg_delta': 0,
            'avg_delta_pct': 0,
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
