from db_utils import execute_query

def check_table(table_name):
    """Check if a table exists and print its columns"""
    # Check if table exists
    exists_query = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = '{table_name}'
    )
    """
    exists_df = execute_query(exists_query, [])
    exists = exists_df.iloc[0][0] if exists_df is not None and not exists_df.empty else False
    
    print(f"\nTable '{table_name}': {'EXISTS' if exists else 'DOES NOT EXIST'}")
    
    if exists:
        # Get column information
        columns_query = f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        columns_df = execute_query(columns_query, [])
        
        if columns_df is not None and not columns_df.empty:
            print(f"Columns in '{table_name}':")
            for _, row in columns_df.iterrows():
                print(f"  - {row['column_name']} ({row['data_type']})")
        else:
            print(f"No columns found for '{table_name}'")
    
    return exists

# Check each table individually
print("Checking seat_prices_partitioned...")
check_table('seat_prices_partitioned')

print("\nChecking seat_wise_prices_partitioned...")
check_table('seat_wise_prices_partitioned')

print("\nChecking seat_prices_with_dt_partitioned...")
check_table('seat_prices_with_dt_partitioned')

print("\nChecking seat_wise_prices_with_dt_partitioned...")
check_table('seat_wise_prices_with_dt_partitioned')
