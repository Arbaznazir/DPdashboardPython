import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from db_utils import get_demand_index, execute_query

def debug_demand_index():
    """Debug script to check demand_index column in seat_prices_raw table"""
    print("Debugging demand_index retrieval...")
    
    # Check table schema
    check_query = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'seat_prices_raw'
    """
    columns_df = execute_query(check_query)
    print(f"Available columns in seat_prices_raw: {columns_df['column_name'].tolist() if columns_df is not None and not columns_df.empty else 'None'}")
    
    # Get a sample schedule_id
    schedule_query = """
    SELECT DISTINCT "schedule_id" 
    FROM seat_prices_raw 
    LIMIT 5
    """
    schedules_df = execute_query(schedule_query)
    if schedules_df is not None and not schedules_df.empty:
        sample_schedules = schedules_df['schedule_id'].tolist()
        print(f"Sample schedule IDs: {sample_schedules}")
        
        # Try to get demand_index for each sample schedule
        for schedule_id in sample_schedules:
            print(f"\nTesting schedule_id: {schedule_id}")
            
            # Direct query to check demand_index
            direct_query = f"""
            SELECT * 
            FROM seat_prices_raw 
            WHERE "schedule_id" = '{schedule_id}'
            LIMIT 1
            """
            df = execute_query(direct_query)
            if df is not None and not df.empty:
                print(f"Columns in result: {df.columns.tolist()}")
                
                # Check for demand_index column with different case variations
                demand_index_col = None
                for col in df.columns:
                    if col.lower() == 'demand_index' or col.lower() == 'demandindex':
                        demand_index_col = col
                        break
                
                if demand_index_col:
                    print(f"Found demand index column: {demand_index_col}")
                    print(f"Value: {df[demand_index_col].iloc[0]}")
                else:
                    print("No demand index column found in the result")
                    
                # Print all columns and values for debugging
                print("\nAll columns and values:")
                for col in df.columns:
                    print(f"{col}: {df[col].iloc[0]}")
            else:
                print(f"No data found for schedule_id {schedule_id}")
            
            # Try using the get_demand_index function
            print("\nUsing get_demand_index function:")
            demand_index = get_demand_index(schedule_id)
            print(f"Result from get_demand_index: {demand_index}")
            
            # Try with hours_before_departure
            for hours in [24, 48, 72]:
                print(f"\nTesting with hours_before_departure={hours}:")
                demand_index = get_demand_index(schedule_id, hours)
                print(f"Result from get_demand_index with hours={hours}: {demand_index}")
    else:
        print("No schedule IDs found in seat_prices_raw table")

if __name__ == "__main__":
    debug_demand_index()
