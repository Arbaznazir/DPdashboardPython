"""
Script to apply database indexes for improving query performance
in the price comparison module.
"""
import os
import sys
from db_utils import get_connection

def apply_indexes(conn=None):
    """Apply the database indexes from the SQL script
    
    Args:
        conn: Optional database connection. If None, a new connection will be created.
        
    Returns:
        bool: True if indexes were applied successfully, False otherwise.
    """
    print("\n🔍 Applying database indexes for query optimization...")
    
    # Get the path to the SQL script
    script_path = os.path.join(os.path.dirname(__file__), 'db_indexes.sql')
    
    # Read the SQL script
    with open(script_path, 'r') as f:
        sql_script = f.read()
    
    # Split the script into individual statements
    # (simple split by semicolon, might need refinement for complex SQL)
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
    
    # Determine if we need to create and manage our own connection
    manage_connection = conn is None
    
    if manage_connection:
        # Connect to the database
        conn = get_connection()
        if not conn:
            print("❌ Failed to connect to the database.")
            return False
    
    try:
        cursor = conn.cursor()
        
        # Check if raw tables exist before applying indexes
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'seat_prices_raw')")
        seat_prices_raw_exists = cursor.fetchone()[0]
        
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'seat_wise_prices_raw')")
        seat_wise_prices_raw_exists = cursor.fetchone()[0]
        
        # Execute each statement separately
        for statement in statements:
            if statement:  # Skip empty statements
                # Skip statements for tables that don't exist
                if ('seat_prices_raw' in statement and not seat_prices_raw_exists) or \
                   ('seat_wise_prices_raw' in statement and not seat_wise_prices_raw_exists):
                    continue
                    
                # Print a shortened version of the statement for logging
                statement_preview = statement.replace('\n', ' ')[:60]
                print(f"  ➤ {statement_preview}...")
                cursor.execute(statement)
        
        # Commit the changes if we're managing the connection
        if manage_connection:
            conn.commit()
        print("✅ Database indexes applied successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error applying indexes: {e}")
        if manage_connection:
            conn.rollback()
        return False
    
    finally:
        # Close the cursor and connection if we created it
        if 'cursor' in locals():
            cursor.close()
        if manage_connection and conn:
            conn.close()

# Function to check if this script was imported by load_to_postgres.py
def is_imported_by_load_script():
    for frame in sys._current_frames().values():
        while frame:
            if frame.f_code.co_filename.endswith('load_to_postgres.py'):
                return True
            frame = frame.f_back
    return False

if __name__ == "__main__":
    # Only run automatically if not imported by load_to_postgres.py
    if not is_imported_by_load_script():
        apply_indexes()
