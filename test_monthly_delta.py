"""
Test script to generate sample data for Monthly Delta KPI
"""
import pandas as pd
import calendar
from price_utils import get_monthly_delta
from kpis import create_monthly_delta_kpis

def generate_test_data(month, year):
    """Generate test data for a specific month and year"""
    print(f"Generating test data for {calendar.month_name[month]} {year}")
    
    # Create sample data for demonstration
    sample_data = {
        'seat_prices': {
            'total_actual_price': 25000.50,
            'total_model_price': 22500.75,
            'price_difference': 2499.75,  # actual - model
            'schedule_count': 5
        },
        'seat_wise_prices': {
            'total_actual_price': 24800.25,
            'total_model_price': 22300.50,
            'price_difference': 2499.75,  # actual - model
            'schedule_count': 5
        }
    }
    
    print(f"Generated sample data: {sample_data}")
    return sample_data

# Test with July 2025
month = 7
year = 2025

# Generate test data
test_data = generate_test_data(month, year)

# Create KPIs with test data
print("\nCreating KPIs with test data...")
try:
    # Import the function directly here to avoid circular imports
    from kpis import create_kpi_card, create_monthly_delta_kpis
    
    # Create a modified version of create_monthly_delta_kpis that uses our test data
    def test_create_monthly_delta_kpis(month, year):
        """Create KPI cards for monthly delta analysis using test data"""
        print(f"Creating Monthly Delta KPIs for {month}/{year} with test data")
        return create_monthly_delta_kpis(month, year, test_data=test_data)
    
    # Test the KPI creation
    kpis = test_create_monthly_delta_kpis(month, year)
    print("KPIs created successfully with test data")
    
except Exception as e:
    print(f"Error creating KPIs with test data: {str(e)}")

print("\nTest complete!")

# Instructions for integration:
print("""
To integrate this with the main dashboard:
1. Modify kpis.py to accept test_data parameter in create_monthly_delta_kpis
2. Update the callback in main.py to use the test data for July 2025
""")
