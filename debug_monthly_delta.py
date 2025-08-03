"""
Debug script to test the Monthly Delta calculation for July 2025
"""
import pandas as pd
import calendar
import sys
import traceback
from price_utils import get_monthly_delta
from kpis import create_monthly_delta_kpis

def debug_monthly_delta():
    """Test the monthly delta calculation for July 2025"""
    # Force flush print statements
    sys.stdout.reconfigure(line_buffering=True)
    
    print("\n" + "="*50)
    print("DEBUGGING MONTHLY DELTA CALCULATION FOR JULY 2025")
    print("="*50)
    
    # Test for July 2025
    month = 7  # July
    year = 2025
    
    print(f"\nTesting get_monthly_delta({month}, {year})...")
    try:
        monthly_data = get_monthly_delta(month, year)
        
        print("\nRESULTS FROM get_monthly_delta:")
        print(f"Month: {calendar.month_name[month]} {year}")
        
        if monthly_data:
            print(f"\nFull monthly_data: {monthly_data}")
            
            # Print seat_prices results
            seat_prices = monthly_data.get('seat_prices', {})
            print("\n1. SEAT PRICES DATA:")
            print(f"   Schedule Count: {seat_prices.get('schedule_count', 'N/A')}")
            print(f"   Total Actual Price: {seat_prices.get('total_actual_price', 'N/A')}")
            print(f"   Total Model Price: {seat_prices.get('total_model_price', 'N/A')}")
            print(f"   Price Difference: {seat_prices.get('price_difference', 'N/A')}")
            
            # Print seat_wise_prices results
            seat_wise_prices = monthly_data.get('seat_wise_prices', {})
            print("\n2. SEAT WISE PRICES DATA:")
            print(f"   Schedule Count: {seat_wise_prices.get('schedule_count', 'N/A')}")
            print(f"   Total Actual Price: {seat_wise_prices.get('total_actual_price', 'N/A')}")
            print(f"   Total Model Price: {seat_wise_prices.get('total_model_price', 'N/A')}")
            print(f"   Price Difference: {seat_wise_prices.get('price_difference', 'N/A')}")
        else:
            print("No data returned from get_monthly_delta")
    except Exception as e:
        print(f"\nERROR in get_monthly_delta: {str(e)}")
        traceback.print_exc()
    
    # Test the KPI creation function
    print("\nTesting create_monthly_delta_kpis...")
    try:
        kpis = create_monthly_delta_kpis(month, year)
        print("KPIs created successfully")
    except Exception as e:
        print(f"Error creating KPIs: {str(e)}")
        traceback.print_exc()
    
    print("\n" + "="*50)
    print("DEBUG COMPLETE")
    print("="*50)

if __name__ == "__main__":
    debug_monthly_delta()
