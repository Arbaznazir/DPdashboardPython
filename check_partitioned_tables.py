from db_utils import execute_query

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    query = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = '{table_name}'
    )
    """
    result = execute_query(query, [])
    return result.iloc[0][0] if result is not None and not result.empty else False

def check_table_columns(table_name):
    """Get column information for a table"""
    query = f"""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    result = execute_query(query, [])
    return result if result is not None and not result.empty else []

def main():
    """Check the existence and structure of partitioned tables"""
    # Tables to check
    tables = [
        'seat_prices_partitioned',
        'seat_wise_prices_partitioned',
        'seat_prices_with_dt_partitioned',
        'seat_wise_prices_with_dt_partitioned'
    ]
    
    print("Checking partitioned tables in the database...\n")
    
    for table in tables:
        exists = check_table_exists(table)
        print(f"Table '{table}': {'EXISTS' if exists else 'DOES NOT EXIST'}")
        
        if exists:
            columns = check_table_columns(table)
            print(f"  Columns in '{table}':")
            for _, row in columns.iterrows():
                print(f"    - {row['column_name']} ({row['data_type']})")
        print()

if __name__ == "__main__":
    main()
