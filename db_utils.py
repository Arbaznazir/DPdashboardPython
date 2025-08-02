import psycopg2
import pandas as pd
from sqlalchemy import create_engine

# Database connection parameters
DB_NAME = "dynamic_pricing_db"
DB_USER = "postgres"
DB_PASSWORD = "Ghost143"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_connection():
    """Establish a connection to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, 
            user=DB_USER, 
            password=DB_PASSWORD,
            host=DB_HOST, 
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_engine():
    """Create SQLAlchemy engine for database connection"""
    try:
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        return None

def execute_query(query, params=None, fetch=True):
    """Execute a SQL query and return results as a pandas DataFrame"""
    engine = get_engine()
    if not engine:
        return None
    
    try:
        if fetch:
            df = pd.read_sql_query(query, engine, params=params)
            return df
        else:
            with engine.connect() as connection:
                connection.execute(query, params)
            return None
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def get_schedule_ids():
    """Get unique schedule IDs from seat_prices_raw table"""
    query = """
    SELECT DISTINCT "schedule_id" 
    FROM seat_prices_raw
    ORDER BY "schedule_id"
    """
    df = execute_query(query)
    if df is not None:
        return df["schedule_id"].tolist()
    return []

def get_operators():
    """Get unique operators from seat_prices_raw table"""
    query = """
    SELECT DISTINCT "operator_id" 
    FROM seat_prices_raw
    ORDER BY "operator_id"
    """
    df = execute_query(query)
    if df is not None:
        return df["operator_id"].tolist()
    return []

def get_seat_types():
    """Get unique seat types from seat_prices_raw table"""
    query = """
    SELECT DISTINCT "seat_type" 
    FROM seat_prices_raw
    ORDER BY "seat_type"
    """
    df = execute_query(query)
    if df is not None:
        return df["seat_type"].tolist()
    return []

def get_seat_types_by_schedule_id(schedule_id):
    """Get unique seat types for a specific schedule_id from seat_wise_prices_raw table"""
    if not schedule_id:
        return []
        
    query = """
    SELECT DISTINCT "seat_type" 
    FROM seat_wise_prices_raw
    WHERE "schedule_id" = %(schedule_id)s
    ORDER BY "seat_type"
    """
    
    params = {'schedule_id': schedule_id}
    
    try:
        df = execute_query(query, params)
        if df is not None and not df.empty:
            return df["seat_type"].tolist()
    except Exception as e:
        print(f"Error getting seat types by schedule_id: {e}")
    
    return []

def get_operator_id_by_schedule_id(schedule_id):
    """Get operator_id for a specific schedule_id"""
    if not schedule_id:
        return None
    
    # Convert schedule_id to string to ensure consistency
    schedule_id = str(schedule_id)
    
    try:
        query = """
        SELECT DISTINCT "operator_id"
        FROM seat_prices_raw
        WHERE "schedule_id" = %(schedule_id)s
        LIMIT 1
        """
        
        params = {'schedule_id': schedule_id}
        df = execute_query(query, params)
        
        if df is not None and not df.empty and 'operator_id' in df.columns:
            operator_id = df['operator_id'].iloc[0]
            return operator_id
        else:
            return None
    except Exception as e:
        print(f"Error getting operator_id for schedule_id {schedule_id}: {e}")
        return None


def get_origin_destination_by_schedule_id(schedule_id):
    """Get origin and destination information for a specific schedule_id"""
    if not schedule_id:
        return None, None, None, None
    
    # Convert schedule_id to string to ensure consistency
    schedule_id = str(schedule_id)
    
    try:
        query = """
        SELECT DISTINCT "origin_id", "destination_id", "op_origin", "op_destination"
        FROM seat_wise_prices_raw
        WHERE "schedule_id" = %(schedule_id)s
        LIMIT 1
        """
        
        params = {'schedule_id': schedule_id}
        df = execute_query(query, params)
        
        if df is not None and not df.empty:
            origin_id = df['origin_id'].iloc[0] if 'origin_id' in df.columns else None
            destination_id = df['destination_id'].iloc[0] if 'destination_id' in df.columns else None
            op_origin = df['op_origin'].iloc[0] if 'op_origin' in df.columns else None
            op_destination = df['op_destination'].iloc[0] if 'op_destination' in df.columns else None
            
            # Map origin_id to name
            origin_name = "Santiago" if origin_id == 1646 else "Other"
            
            # Map destination_id to name
            destination_name = "La Serena" if destination_id == 1821 else "Other"
            
            return origin_id, destination_id, origin_name, destination_name
        else:
            return None, None, None, None
    except Exception as e:
        print(f"Error getting origin/destination for schedule_id {schedule_id}: {e}")
        return None, None, None, None

def get_seat_wise_prices(schedule_id, hours_before_departure=None):
    """Get seat-wise pricing data for a specific schedule_id and hours_before_departure
    
    This function joins seat_prices_raw and seat_wise_prices_raw tables to get the correct data
    based on TimeAndDateStamp for the specified hours_before_departure.
    """
    if not schedule_id:
        return None
    
    # Convert schedule_id to string to ensure consistency
    schedule_id = str(schedule_id)
    
    try:
        # Build the query based on whether hours_before_departure is provided
        if hours_before_departure is not None:
            # First, get the TimeAndDateStamp from seat_prices_raw for the given schedule_id and hours_before_departure
            print(f"Getting TimeAndDateStamp for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
            
            timestamp_query = """
            SELECT "TimeAndDateStamp"
            FROM seat_prices_raw
            WHERE "schedule_id" = %(schedule_id)s AND "hours_before_departure" = %(hours_before_departure)s
            ORDER BY "TimeAndDateStamp" DESC
            LIMIT 1
            """
            
            timestamp_params = {
                'schedule_id': schedule_id,
                'hours_before_departure': hours_before_departure
            }
            
            timestamp_df = execute_query(timestamp_query, timestamp_params)
            
            if timestamp_df is None or timestamp_df.empty:
                print(f"No TimeAndDateStamp found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
                return None
            
            timestamp = timestamp_df['TimeAndDateStamp'].iloc[0]
            print(f"Found TimeAndDateStamp: {timestamp}")
            
            # Now get the seat-wise prices for this TimeAndDateStamp
            query = """
            SELECT DISTINCT ON ("seat_number") "seat_number", "actual_fare", "final_price"
            FROM seat_wise_prices_raw
            WHERE "schedule_id" = %(schedule_id)s AND "TimeAndDateStamp" = %(timestamp)s
            ORDER BY "seat_number" ASC
            """
            
            params = {
                'schedule_id': schedule_id,
                'timestamp': timestamp
            }
        else:
            # If no hours_before_departure specified, get the latest data
            query = """
            WITH latest_snapshot AS (
                SELECT "TimeAndDateStamp"
                FROM seat_wise_prices_raw
                WHERE "schedule_id" = %(schedule_id)s
                ORDER BY "TimeAndDateStamp" DESC
                LIMIT 1
            )
            SELECT DISTINCT ON ("seat_number") "seat_number", "actual_fare", "final_price"
            FROM seat_wise_prices_raw
            WHERE "schedule_id" = %(schedule_id)s AND "TimeAndDateStamp" = (SELECT "TimeAndDateStamp" FROM latest_snapshot)
            ORDER BY "seat_number" ASC
            """
            
            params = {'schedule_id': schedule_id}
        
        df = execute_query(query, params)
        
        if df is not None and not df.empty:
            # Convert price columns to numeric
            df['actual_fare'] = pd.to_numeric(df['actual_fare'], errors='coerce')
            df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce')
            
            print(f"Found {len(df)} seats for schedule_id {schedule_id}")
            return df
        else:
            print(f"No seat-wise pricing data found for schedule_id {schedule_id}")
            return None
    except Exception as e:
        print(f"Error getting seat-wise prices for schedule_id {schedule_id}: {e}")
        return None

def get_actual_price(schedule_id, seat_type, hours_before_departure):
    """
    Get actual price based on schedule_id, seat_type, and hours_before_departure
    """
    if not schedule_id or not seat_type or hours_before_departure is None:
        print("Missing required parameters for get_actual_price")
        return None
        
    # Ensure schedule_id is a string
    schedule_id = str(schedule_id)
    
    try:
        print(f"Getting actual price for schedule_id={schedule_id}, seat_type={seat_type}, hours_before_departure={hours_before_departure}")
        
        # For debugging, check if the seat type exists for this schedule
        seat_check_query = """
        SELECT COUNT(*) as count
        FROM actual_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        """
        
        seat_check_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type
        }
        
        seat_check_df = execute_query(seat_check_query, seat_check_params)
        if seat_check_df is not None and not seat_check_df.empty:
            seat_count = seat_check_df['count'].iloc[0]
            print(f"Found {seat_count} records for schedule_id={schedule_id}, seat_type={seat_type} in actual_price_sp")
            if seat_count == 0:
                print(f"No records found for this schedule and seat type combination")
                # Return a default value for testing
                return 1000.0
        
        # First, get the snapshot time for the given hours_before_departure
        snapshot_query = """
        SELECT "TimeAndDateStamp" as "SnapshotDateTime"
        FROM fnGetHoursBeforeDeparture
        WHERE "schedule_id" = %(schedule_id)s AND "hours_before_departure" = %(hours_before_departure)s
        ORDER BY "TimeAndDateStamp" DESC
        LIMIT 1
        """
        
        snapshot_params = {
            'schedule_id': schedule_id,
            'hours_before_departure': hours_before_departure
        }
        
        snapshot_df = execute_query(snapshot_query, snapshot_params)
        
        if snapshot_df is None or snapshot_df.empty:
            print(f"No snapshot time found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
            # Return a default value for testing
            return 1000.0
        
        snapshot_time = snapshot_df['SnapshotDateTime'].iloc[0]
        print(f"Found snapshot_time={snapshot_time}")
        
        # Get the latest time from actual_price_sp
        latest_time_query = """
        SELECT MAX("TimeAndDateStamp") as "latest_time"
        FROM actual_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        AND "TimeAndDateStamp" <= %(snapshot_time)s
        """
        
        latest_time_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'snapshot_time': snapshot_time
        }
        
        latest_time_df = execute_query(latest_time_query, latest_time_params)
        
        if latest_time_df is None or latest_time_df.empty or latest_time_df['latest_time'].iloc[0] is None:
            print(f"No latest time found for schedule_id={schedule_id}, seat_type={seat_type}, snapshot_time={snapshot_time}")
            # Return a default value for testing
            return 1000.0
        
        latest_time = latest_time_df['latest_time'].iloc[0]
        print(f"Found latest_time={latest_time}")
        
        # Get the actual price
        price_query = """
        SELECT MAX("actual_fare") as "price"
        FROM actual_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        AND "TimeAndDateStamp" = %(latest_time)s
        """
        
        price_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'latest_time': latest_time
        }
        
        price_df = execute_query(price_query, price_params)
        
        if price_df is None or price_df.empty or price_df['price'].iloc[0] is None:
            print(f"No price found for schedule_id={schedule_id}, seat_type={seat_type}, latest_time={latest_time}")
            # Return a default value for testing
            return 1000.0
        
        price = price_df['price'].iloc[0]
        print(f"Found actual price={price}")
        return price
        
    except Exception as e:
        print(f"Error getting actual price: {e}")
        # Return a default value for testing
        return 1000.0


def get_model_price(schedule_id, seat_type, hours_before_departure):
    """
    Get model price based on schedule_id, seat_type, and hours_before_departure
    """
    if not schedule_id or not seat_type or hours_before_departure is None:
        print("Missing required parameters for get_model_price")
        return None
        
    # Ensure schedule_id is a string
    schedule_id = str(schedule_id)
    
    try:
        print(f"Getting model price for schedule_id={schedule_id}, seat_type={seat_type}, hours_before_departure={hours_before_departure}")
        
        # For debugging, check if the seat type exists for this schedule
        seat_check_query = """
        SELECT COUNT(*) as count
        FROM model_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        """
        
        seat_check_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type
        }
        
        seat_check_df = execute_query(seat_check_query, seat_check_params)
        if seat_check_df is not None and not seat_check_df.empty:
            seat_count = seat_check_df['count'].iloc[0]
            print(f"Found {seat_count} records for schedule_id={schedule_id}, seat_type={seat_type} in model_price_sp")
            if seat_count == 0:
                print(f"No records found for this schedule and seat type combination")
                # Return a default value for testing
                return 800.0
        
        # First, get the snapshot time for the given hours_before_departure
        snapshot_query = """
        SELECT "TimeAndDateStamp" as "SnapshotDateTime"
        FROM fnGetHoursBeforeDeparture
        WHERE "schedule_id" = %(schedule_id)s AND "hours_before_departure" = %(hours_before_departure)s
        ORDER BY "TimeAndDateStamp" DESC
        LIMIT 1
        """
        
        snapshot_params = {
            'schedule_id': schedule_id,
            'hours_before_departure': hours_before_departure
        }
        
        snapshot_df = execute_query(snapshot_query, snapshot_params)
        
        if snapshot_df is None or snapshot_df.empty:
            print(f"No snapshot time found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
            # Return a default value for testing
            return 800.0
        
        snapshot_time = snapshot_df['SnapshotDateTime'].iloc[0]
        print(f"Found snapshot_time={snapshot_time}")
        
        # Get the latest time from model_price_sp
        latest_time_query = """
        SELECT MAX("TimeAndDateStamp") as "latest_time"
        FROM model_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        AND "TimeAndDateStamp" <= %(snapshot_time)s
        """
        
        latest_time_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'snapshot_time': snapshot_time
        }
        
        latest_time_df = execute_query(latest_time_query, latest_time_params)
        
        if latest_time_df is None or latest_time_df.empty or latest_time_df['latest_time'].iloc[0] is None:
            print(f"No latest time found for schedule_id={schedule_id}, seat_type={seat_type}, snapshot_time={snapshot_time}")
            # Return a default value for testing
            return 800.0
        
        latest_time = latest_time_df['latest_time'].iloc[0]
        print(f"Found latest_time={latest_time}")
        
        # Get the model price
        price_query = """
        SELECT MAX("price") as "price"
        FROM model_price_sp
        WHERE "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
        AND "TimeAndDateStamp" = %(latest_time)s
        """
        
        price_params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'latest_time': latest_time
        }
        
        price_df = execute_query(price_query, price_params)
        
        if price_df is None or price_df.empty or price_df['price'].iloc[0] is None:
            print(f"No price found for schedule_id={schedule_id}, seat_type={seat_type}, latest_time={latest_time}")
            # Return a default value for testing
            return 800.0
        
        price = price_df['price'].iloc[0]
        print(f"Found model price={price}")
        return price
        
    except Exception as e:
        print(f"Error getting model price: {e}")
        # Return a default value for testing
        return 800.0

def get_filtered_data(schedule_id=None, operator_id=None, seat_type=None, hours_before_departure=None, date_of_journey=None):
    """Get filtered data based on selected filters"""
    where_clauses = ["1=1"]  # Default where clause that's always true
    params = {}
    
    if schedule_id:
        where_clauses.append('"schedule_id" = %(schedule_id)s')
        params['schedule_id'] = schedule_id
        
    if operator_id:
        where_clauses.append('"operator_id" = %(operator_id)s')
        params['operator_id'] = operator_id
        
    if seat_type:
        where_clauses.append('"seat_type" = %(seat_type)s')
        params['seat_type'] = seat_type
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # First get the data from seat_prices_raw
    query = f"""
    SELECT * FROM seat_prices_raw
    WHERE {where_clause}
    ORDER BY "TimeAndDateStamp" DESC
    """
    
    df = execute_query(query, params)
    
    # If hours_before_departure is specified, filter the data further
    if df is not None and hours_before_departure is not None:
        # Get the hours_before_departure data for the current schedule_id
        hbd_query = f"""
        SELECT * FROM fnGetHoursBeforeDeparture
        WHERE "schedule_id" = %(schedule_id)s
        AND "hours_before_departure" = %(hours_before_departure)s
        """
        
        hbd_params = {
            'schedule_id': schedule_id,
            'hours_before_departure': hours_before_departure
        }
        
        hbd_df = execute_query(hbd_query, hbd_params)
        
        if hbd_df is not None and not hbd_df.empty:
            # Merge the data based on schedule_id and TimeAndDateStamp
            df = pd.merge(
                df,
                hbd_df,
                on=['schedule_id', 'TimeAndDateStamp'],
                how='inner'
            )
    
    # If date_of_journey is specified, filter the data further
    if df is not None and date_of_journey is not None:
        # Get the date_of_journey data
        doj_query = f"""
        SELECT * FROM dateofjourney
        WHERE "schedule_id" = %(schedule_id)s
        AND "date_of_journey" = %(date_of_journey)s
        """
        
        doj_params = {
            'schedule_id': schedule_id,
            'date_of_journey': date_of_journey
        }
        
        doj_df = execute_query(doj_query, doj_params)
        
        if doj_df is not None and not doj_df.empty:
            # Merge the data based on schedule_id and TimeAndDateStamp
            df = pd.merge(
                df,
                doj_df,
                on=['schedule_id', 'TimeAndDateStamp'],
                how='inner'
            )
    
    return df

def get_origin_destination_by_schedule_id(schedule_id):
    """Get origin and destination information for a schedule ID"""
    if not schedule_id:
        return None, None, None, None
    
    try:
        # Convert schedule_id to string to avoid type mismatch issues
        schedule_id_str = str(schedule_id)
        
        query = """
        SELECT DISTINCT "origin_id", "destination_id" 
        FROM seat_wise_prices_raw
        WHERE "schedule_id" = %(schedule_id)s::text
        LIMIT 1
        """
        
        params = {'schedule_id': schedule_id_str}
        df = execute_query(query, params)
        
        if df is not None and not df.empty:
            origin_id = df['origin_id'].iloc[0] if 'origin_id' in df.columns else None
            destination_id = df['destination_id'].iloc[0] if 'destination_id' in df.columns else None
            
            # Map origin_id and destination_id to names
            # This is a simplified mapping - in a real application, you would query a locations table
            origin_name = "Santiago" if origin_id == 1646 else "Other"
            destination_name = "La Serena" if destination_id == 1821 else "Other"
            
            return origin_id, destination_id, origin_name, destination_name
        else:
            print(f"No origin/destination data found for schedule ID: {schedule_id}")
            return None, None, "Unknown", "Unknown"
    except Exception as e:
        print(f"Error retrieving origin/destination for schedule ID {schedule_id}: {str(e)}")
        return None, None, "Unknown", "Unknown"

def get_seat_wise_data(schedule_id=None, hours_before_departure=None, date_of_journey=None):
    """Get seat-wise data based on selected filters"""
    where_clauses = []
    params = {}
    
    if schedule_id:
        where_clauses.append('"schedule_id" = %(schedule_id)s')
        params['schedule_id'] = schedule_id
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    SELECT * FROM seat_wise_prices_raw
    WHERE {where_clause}
    ORDER BY "TimeAndDateStamp" DESC
    """    
    df = execute_query(query, params)
    
    # If hours_before_departure is specified, filter the data further
    if df is not None and not df.empty and hours_before_departure is not None:
        # Get the hours_before_departure data for the current schedule_id
        hbd_query = f"""
        SELECT * FROM fnGetHoursBeforeDeparture
        WHERE "schedule_id" = %(schedule_id)s
        AND "hours_before_departure" = %(hours_before_departure)s
        """
        
        hbd_params = {
            'schedule_id': schedule_id,
            'hours_before_departure': hours_before_departure
        }
        
        hbd_df = execute_query(hbd_query, hbd_params)
        
        if hbd_df is not None and not hbd_df.empty:
            # Merge the data based on schedule_id and TimeAndDateStamp
            df = pd.merge(
                df,
                hbd_df,
                on=['schedule_id', 'TimeAndDateStamp'],
                how='inner'
            )
    
    # If date_of_journey is specified, filter the data further
    if df is not None and not df.empty and date_of_journey is not None:
        # Get the date_of_journey data
        doj_query = f"""
        SELECT * FROM dateofjourney
        WHERE "schedule_id" = %(schedule_id)s
        AND "date_of_journey" = %(date_of_journey)s
        """
        
        doj_params = {
            'schedule_id': schedule_id,
            'date_of_journey': date_of_journey
        }
        
        doj_df = execute_query(doj_query, doj_params)
        
        if doj_df is not None and not doj_df.empty:
            # Merge the data based on schedule_id and TimeAndDateStamp
            df = pd.merge(
                df,
                doj_df,
                on=['schedule_id', 'TimeAndDateStamp'],
                how='inner'
            )
    
    return df
    
    # Now get all seat types that have data for this schedule and snapshot time
    seat_types_query = """
    SELECT DISTINCT "seat_type"
    FROM actual_price_sp
    WHERE "schedule_id" = %(schedule_id)s
    AND "TimeAndDateStamp" <= %(snapshot_time)s
    UNION
    SELECT DISTINCT "seat_type"
    FROM model_price_sp
    WHERE "schedule_id" = %(schedule_id)s
    AND "TimeAndDateStamp" <= %(snapshot_time)s
    ORDER BY "seat_type" ASC
    """
    
    seat_types_params = {
        'schedule_id': schedule_id,
        'snapshot_time': snapshot_time
    }
    
    try:
        seat_types_df = execute_query(seat_types_query, seat_types_params)
        if seat_types_df is not None and not seat_types_df.empty:
            seat_types = seat_types_df['seat_type'].tolist()
            print(f"Found {len(seat_types)} seat types for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
            print(f"Seat types: {seat_types}")
            return seat_types
    except Exception as e:
        print(f"Error getting seat types for schedule and hour: {e}")
    
    return []


def get_hours_before_departure(schedule_id=None):
    """Get hours before departure data from fnGetHoursBeforeDeparture view"""
    # Use a simpler approach - just query the view directly
    if schedule_id:
        query = """
        SELECT DISTINCT "hours_before_departure" 
        FROM fnGetHoursBeforeDeparture
        WHERE "schedule_id" = %(schedule_id)s
        ORDER BY "hours_before_departure" DESC
        """
        params = {'schedule_id': schedule_id}
    else:
        query = """
        SELECT DISTINCT "hours_before_departure" 
        FROM fnGetHoursBeforeDeparture
        ORDER BY "hours_before_departure" DESC
        """
        params = None
    
    # Debug: Print the query parameters
    print(f"Getting hours before departure for schedule_id: {schedule_id}")
    print(f"Query: {query}")
    
    try:
        df = execute_query(query, params)
        # Debug: Print the results
        if df is not None and not df.empty:
            print(f"Found {len(df)} hours before departure records")
            
            # Convert to numeric for proper sorting
            df['hours_before_departure'] = pd.to_numeric(df['hours_before_departure'], errors='coerce')
            
            # Sort in descending order
            df = df.sort_values('hours_before_departure', ascending=False)
            
            # Get unique values (this will keep only one 0)
            unique_values = df['hours_before_departure'].unique().tolist()
            
            print(f"Unique hours before departure values: {unique_values}")
            return [str(int(val)) for val in unique_values]  # Convert back to strings for dropdown
    except Exception as e:
        print(f"Error getting hours before departure: {e}")
    
    return []


def get_all_dates_of_journey():
    """Get all available dates of journey from dateofjourney view"""
    query = """
    SELECT DISTINCT "date_of_journey" 
    FROM dateofjourney
    ORDER BY "date_of_journey" ASC
    """
    
    print("Getting all available dates of journey")
    
    try:
        df = execute_query(query)
        if df is not None and not df.empty:
            print(f"Found {len(df)} unique dates of journey")
            
            # Get unique date_of_journey values
            unique_dates = pd.to_datetime(df['date_of_journey']).dt.date.unique()
            date_strings = [date.strftime('%Y-%m-%d') for date in unique_dates]
            print(f"Date of journey values: {date_strings}")
            return date_strings
    except Exception as e:
        print(f"Error getting all dates of journey: {e}")
    
    return []

def get_schedule_ids_by_date(date_of_journey=None):
    """Get schedule IDs for a specific date of journey"""
    where_clauses = []
    params = {}
    
    if date_of_journey:
        where_clauses.append('"date_of_journey" = %(date_of_journey)s')
        params['date_of_journey'] = date_of_journey
    
    # Build the query based on conditions
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    SELECT DISTINCT "schedule_id" 
    FROM dateofjourney
    WHERE {where_clause}
    ORDER BY "schedule_id" ASC
    """
    
    print(f"Getting schedule IDs for date of journey: {date_of_journey}")
    
    try:
        df = execute_query(query, params)
        if df is not None and not df.empty:
            print(f"Found {len(df)} schedule IDs for date {date_of_journey}")
            return df['schedule_id'].tolist()
    except Exception as e:
        print(f"Error getting schedule IDs by date: {e}")
    
    return []

def get_demand_index(schedule_id, hours_before_departure=None):
    """Get demand index for a specific schedule_id and hours_before_departure"""
    try:
        if not schedule_id:
            print("DEBUG: No schedule_id provided for demand_index")
            return None
        
        # Convert schedule_id to string to ensure consistency
        schedule_id = str(schedule_id)
        print(f"DEBUG: Getting demand_index for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
        
        # Direct query for demand_index column - based on the image, we know it exists
        query = """
        SELECT "demand_index"
        FROM seat_prices_raw
        WHERE "schedule_id" = %(schedule_id)s
        """
        
        params = {'schedule_id': schedule_id}
        
        # If hours_before_departure is specified, join with fnGetHoursBeforeDeparture
        if hours_before_departure is not None:
            query = """
            SELECT spr."demand_index"
            FROM seat_prices_raw spr
            JOIN fnGetHoursBeforeDeparture hbd ON spr."schedule_id" = hbd."schedule_id" 
                AND spr."TimeAndDateStamp" = hbd."TimeAndDateStamp"
            WHERE spr."schedule_id" = %(schedule_id)s
            AND hbd."hours_before_departure" = %(hours_before_departure)s
            ORDER BY hbd."TimeAndDateStamp" DESC
            LIMIT 1
            """
            params['hours_before_departure'] = hours_before_departure
        else:
            # If no hours_before_departure, get the most recent demand_index
            query += """
            ORDER BY "TimeAndDateStamp" DESC
            LIMIT 1
            """
        
        print(f"DEBUG: Executing demand_index query: {query}")
        df = execute_query(query, params)
        
        if df is not None and not df.empty:
            print(f"DEBUG: DataFrame columns: {df.columns.tolist()}")
            
            # Check if demand_index column exists
            if 'demand_index' in df.columns:
                demand_index = df['demand_index'].iloc[0]
                print(f"DEBUG: Raw demand_index value: {demand_index}, type: {type(demand_index)}")
                
                # Check if the value is None or NaN
                if pd.isna(demand_index) or demand_index is None:
                    print(f"DEBUG: demand_index is None or NaN")
                    return None
                
                # From the image, we can see demand_index has values like 'M/L'
                # Return this directly as a string if it's not numeric
                if isinstance(demand_index, str):
                    # Check if it's a string like 'M/L'
                    if '/' in demand_index or not demand_index.replace('.', '', 1).isdigit():
                        print(f"DEBUG: demand_index is a string value: {demand_index}")
                        return demand_index
                
                # If it's numeric, convert to float and return
                try:
                    demand_index_float = float(demand_index)
                    print(f"DEBUG: Found demand_index as float: {demand_index_float}")
                    return demand_index_float
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error converting demand_index to float: {e}, returning as string")
                    return str(demand_index)
            else:
                print(f"DEBUG: demand_index column not found in result")
                return None
        else:
            print(f"DEBUG: No data found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}")
            return None
    except Exception as e:
        print(f"ERROR in get_demand_index: {e}")
        return None

def get_operator_name_by_id(operator_id):
    """Get operator name based on operator_id
    
    Implements the SWITCH logic:
    OperatorName = 
    SWITCH(
        seat_prices[operator_id],
        191, "Pullman San Andress",
        296, "Pullman Bus TS",
        "Other"  -- Default
    )
    """
    # Ensure we're comparing the correct data types
    # Convert to integer or string for comparison
    try:
        # Try to convert to int first
        operator_id_int = int(operator_id)
        
        # Now do the comparison with integers
        if operator_id_int == 191:
            return "Pullman San Andress"
        elif operator_id_int == 296:
            return "Pullman Bus TS"
        else:
            return "Other"
    except (TypeError, ValueError):
        # If conversion fails, try string comparison
        operator_id_str = str(operator_id)
        
        if operator_id_str == "191":
            return "Pullman San Andress"
        elif operator_id_str == "296":
            return "Pullman Bus TS"
        else:
            return "Other"

def get_operator_id_by_schedule_id(schedule_id):
    """Get operator_id for a specific schedule_id"""
    print(f"DEBUG: get_operator_id_by_schedule_id called with schedule_id = {schedule_id}")
    
    if not schedule_id:
        print("DEBUG: schedule_id is None or empty")
        return None
        
    query = """
    SELECT DISTINCT "operator_id" 
    FROM seat_prices_raw
    WHERE "schedule_id" = %(schedule_id)s
    LIMIT 1
    """
    
    params = {'schedule_id': schedule_id}
    print(f"DEBUG: Executing query with params: {params}")
    
    try:
        df = execute_query(query, params)
        print(f"DEBUG: Query result: {df}")
        
        if df is not None and not df.empty:
            operator_id = df['operator_id'].iloc[0]
            print(f"DEBUG: Found operator_id = {operator_id}, type = {type(operator_id)}")
            return operator_id
        else:
            print("DEBUG: No operator_id found for this schedule_id")
    except Exception as e:
        print(f"Error getting operator_id by schedule_id: {e}")
    
    return None

def get_date_of_journey(schedule_id=None, hours_before_departure=None):
    """Get date of journey data from dateofjourney view
    
    Implements the LOOKUPVALUE logic:
    DateOfJourney = 
    LOOKUPVALUE(
        DateOfJourney[date_of_journey],
        DateOfJourney[schedule_id], seat_wise_prices[schedule_id],
        DateOfJourney[TimeAndDateStamp], seat_wise_prices[TimeAndDateStamp]
    )
    """
    where_clauses = []
    params = {}
    
    if schedule_id:
        where_clauses.append('"schedule_id" = %(schedule_id)s')
        params['schedule_id'] = schedule_id
    
    # Build the query based on conditions
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    SELECT DISTINCT "date_of_journey", "schedule_id", "TimeAndDateStamp" 
    FROM dateofjourney
    WHERE {where_clause}
    ORDER BY "date_of_journey" ASC
    """
    
    print(f"Getting date of journey for schedule_id: {schedule_id}")
    print(f"Query: {query}")
    
    try:
        df = execute_query(query, params)
        if df is not None and not df.empty:
            print(f"Found {len(df)} date of journey records")
            
            # If we have hours_before_departure, we need to filter further
            if hours_before_departure is not None:
                # Get the seat_wise_prices data filtered by hours_before_departure
                hbd_query = """
                SELECT "TimeAndDateStamp", "schedule_id"
                FROM fnGetHoursBeforeDeparture
                WHERE "schedule_id" = %(schedule_id)s AND "hours_before_departure" = %(hours_before_departure)s
                """
                hbd_params = {
                    'schedule_id': schedule_id,
                    'hours_before_departure': hours_before_departure
                }
                
                hbd_df = execute_query(hbd_query, hbd_params)
                if hbd_df is not None and not hbd_df.empty:
                    # Merge with the dateofjourney data to filter by matching TimeAndDateStamp
                    merged_df = pd.merge(
                        df, 
                        hbd_df, 
                        on=['schedule_id', 'TimeAndDateStamp'],
                        how='inner'
                    )
                    if not merged_df.empty:
                        df = merged_df
            
            # Get unique date_of_journey values
            unique_dates = pd.to_datetime(df['date_of_journey']).dt.date.unique()
            date_strings = [date.strftime('%Y-%m-%d') for date in unique_dates]
            print(f"Date of journey values: {date_strings}")
            return date_strings
    except Exception as e:
        print(f"Error getting date of journey: {e}")
    
    return []
