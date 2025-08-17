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
    """Get unique schedule IDs from seat_prices_partitioned table"""
    query = """
    SELECT DISTINCT "schedule_id" 
    FROM seat_prices_partitioned
    ORDER BY "schedule_id"
    """
    df = execute_query(query)
    if df is not None:
        return df["schedule_id"].tolist()
    return []

def get_operators():
    """Get unique operators from seat_prices_partitioned table"""
    query = """
    SELECT DISTINCT "operator_id" 
    FROM seat_prices_partitioned
    ORDER BY "operator_id"
    """
    df = execute_query(query)
    if df is not None:
        return df["operator_id"].tolist()
    return []

def get_seat_types():
    """Get unique seat types from seat_prices_partitioned table"""
    query = """
    SELECT DISTINCT "seat_type" 
    FROM seat_prices_partitioned
    ORDER BY "seat_type"
    """
    df = execute_query(query)
    if df is not None:
        return df["seat_type"].tolist()
    return []

def get_seat_types_by_schedule_id(schedule_id):
    """Get unique seat types for a specific schedule_id from seat_wise_prices_partitioned table"""
    if not schedule_id:
        return []
        
    query = """
    SELECT DISTINCT "seat_type" 
    FROM seat_wise_prices_partitioned
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
        FROM seat_prices_partitioned
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
        FROM seat_wise_prices_partitioned
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
    
    This function joins seat_prices_raw and seat_wise_prices_partitioned tables to get the correct data
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
            FROM seat_prices_partitioned
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
            FROM seat_wise_prices_partitioned
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
                FROM seat_wise_prices_partitioned
                WHERE "schedule_id" = %(schedule_id)s
                ORDER BY "TimeAndDateStamp" DESC
                LIMIT 1
            )
            SELECT DISTINCT ON ("seat_number") "seat_number", "actual_fare", "final_price"
            FROM seat_wise_prices_partitioned
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

    # Ensure schedule_id is a string (tables store IDs as text)
    schedule_id = str(schedule_id)

    try:
        print(
            f"Getting actual price (seat_prices_partitioned) for schedule_id={schedule_id}, "
            f"seat_type={seat_type}, hours_before_departure={hours_before_departure}"
        )

        # Directly query the partitioned table, matching hours_before_departure with tolerance
        query = """
        SELECT
            ("actual_fare")::numeric AS price
        FROM seat_prices_partitioned
        WHERE "schedule_id" = %(schedule_id)s
          AND "seat_type" = %(seat_type)s
          AND ABS(("hours_before_departure")::float - %(hours_before_departure)s) < 0.01
        ORDER BY "TimeAndDateStamp" DESC
        LIMIT 1
        """

        params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'hours_before_departure': float(hours_before_departure),
        }

        df = execute_query(query, params)

        if df is None or df.empty or df.get('price').isna().all():
            print(
                f"No actual price found for schedule_id={schedule_id}, seat_type={seat_type}, "
                f"hours_before_departure={hours_before_departure}"
            )
            return None

        price = float(df['price'].iloc[0])
        print(f"Found actual price={price}")
        return price

    except Exception as e:
        print(f"Error getting actual price: {e}")
        return None


def get_model_price(schedule_id, seat_type, hours_before_departure):
    """
    Get model price based on schedule_id, seat_type, and hours_before_departure
    """
    if not schedule_id or not seat_type or hours_before_departure is None:
        print("Missing required parameters for get_model_price")
        return None

    # Ensure schedule_id is a string (tables store IDs as text)
    schedule_id = str(schedule_id)

    try:
        print(
            f"Getting model price (seat_prices_partitioned) for schedule_id={schedule_id}, "
            f"seat_type={seat_type}, hours_before_departure={hours_before_departure}"
        )

        query = """
        SELECT
            COALESCE(("price")::numeric, ("actual_fare")::numeric) AS price
        FROM seat_prices_partitioned
        WHERE "schedule_id" = %(schedule_id)s
          AND "seat_type" = %(seat_type)s
          AND ABS(("hours_before_departure")::float - %(hours_before_departure)s) < 0.01
        ORDER BY "TimeAndDateStamp" DESC
        LIMIT 1
        """

        params = {
            'schedule_id': schedule_id,
            'seat_type': seat_type,
            'hours_before_departure': float(hours_before_departure),
        }

        df = execute_query(query, params)

        if df is None or df.empty or df.get('price').isna().all():
            print(
                f"No model price found for schedule_id={schedule_id}, seat_type={seat_type}, "
                f"hours_before_departure={hours_before_departure}"
            )
            return None

        price = float(df['price'].iloc[0])
        print(f"Found model price={price}")
        return price

    except Exception as e:
        print(f"Error getting model price: {e}")
        return None

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
    
    # If hours_before_departure is specified, add it to the WHERE clause directly
    if hours_before_departure is not None:
        try:
            hours_before_departure_str = str(hours_before_departure)
            # Since hours_before_departure is stored as TEXT, do a direct string comparison
            # or try to cast both sides safely
            where_clauses.append("""
                (CASE 
                    WHEN "hours_before_departure" ~ '^[0-9]+(\.[0-9]+)?$' 
                    THEN ABS("hours_before_departure"::float - %(hours_before_departure)s) < 0.01
                    ELSE "hours_before_departure" = %(hours_before_departure_str)s
                END)
            """)
            params['hours_before_departure'] = float(hours_before_departure)
            params['hours_before_departure_str'] = hours_before_departure_str
            print(f"Added hours_before_departure filter: {hours_before_departure}")
        except (ValueError, TypeError) as e:
            print(f"Error converting hours_before_departure: {e}")
            # Fallback to string comparison
            where_clauses.append('"hours_before_departure" = %(hours_before_departure)s')
            params['hours_before_departure'] = str(hours_before_departure)

    # If date_of_journey is specified, filter directly in SQL rather than merging later
    if date_of_journey is not None:
        where_clauses.append('"date_of_journey" = %(date_of_journey)s')
        params['date_of_journey'] = date_of_journey
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Get the data from seat_prices_partitioned with all filters applied directly in SQL
    query = f"""
    SELECT 
        sp.*
    FROM seat_prices_partitioned sp
    WHERE {where_clause}
    ORDER BY "TimeAndDateStamp" DESC
    """
    
    df = execute_query(query, params)
    
    # Debug output
    print(f"Query: {query}")
    print(f"Params: {params}")
    print(f"Where clause: {where_clause}")
    
    # If df is empty after filtering, return None
    if df is None or df.empty:
        print("No data found for the selected filters")
        return None
    
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
        FROM seat_wise_prices_partitioned
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

def get_distinct_prices_by_date_operator_time(date_of_journey, operator_id, departure_time):
    """Get distinct prices from seat_prices_with_dt_partitioned filtered by date, operator, and departure time"""
    try:
        # First check if the table exists
        table_check_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'seat_prices_with_dt_partitioned'
        )
        """
        table_exists_df = execute_query(table_check_query, [])
        table_exists = table_exists_df.iloc[0][0] if table_exists_df is not None and not table_exists_df.empty else False
        
        if not table_exists:
            print("WARNING: seat_prices_with_dt_partitioned table does not exist")
            # Try to use seat_prices_partitioned as a fallback
            # Don't use COALESCE with numeric values on TEXT columns
            fallback_query = """
            SELECT DISTINCT ON (schedule_id, seat_type, hours_before_departure)
                schedule_id,
                seat_type,
                hours_before_departure,
                actual_fare,
                CASE WHEN price IS NOT NULL AND price != '' THEN price ELSE actual_fare END AS price,
                CASE WHEN actual_occupancy IS NOT NULL AND actual_occupancy != '' THEN actual_occupancy ELSE '0' END AS actual_occupancy,
                CASE WHEN expected_occupancy IS NOT NULL AND expected_occupancy != '' THEN expected_occupancy ELSE '0' END AS expected_occupancy,
                "TimeAndDateStamp" as timeanddatestamp
            FROM seat_prices_partitioned
            WHERE date_of_journey = %s
              AND operator_id = %s
              AND departure_time = %s
            ORDER BY schedule_id, seat_type, hours_before_departure, "TimeAndDateStamp" DESC;
            """
            print(f"Using fallback query on seat_prices_partitioned")
            params = [date_of_journey, operator_id, departure_time]
            df = execute_query(fallback_query, params)
        else:
            # Original query on seat_prices_with_dt_partitioned
            # Don't use COALESCE with numeric values on TEXT columns
            query = """
            SELECT DISTINCT ON (schedule_id, seat_type, hours_before_departure)
                schedule_id,
                seat_type,
                hours_before_departure,
                actual_fare,
                actual_fare AS price, -- For non-dynamic pricing operator, use actual_fare
                "TimeAndDateStamp",
                CASE WHEN actual_occupancy IS NOT NULL AND actual_occupancy != '' THEN actual_occupancy ELSE '0' END AS actual_occupancy,
                CASE WHEN expected_occupancy IS NOT NULL AND expected_occupancy != '' THEN expected_occupancy ELSE '0' END AS expected_occupancy
            FROM seat_prices_with_dt_partitioned
            WHERE date_of_journey = %s
              AND operator_id = %s
              AND departure_time = %s
            ORDER BY schedule_id, seat_type, hours_before_departure, "TimeAndDateStamp" DESC;
            """
            
            params = [date_of_journey, operator_id, departure_time]
            
            print(f"Executing distinct prices query with params: date={date_of_journey}, operator={operator_id}, time={departure_time}")
            df = execute_query(query, params)
        
        if df is not None and not df.empty:
            print(f"Retrieved {len(df)} distinct price records")
            # Ensure all required columns exist - use string defaults for TEXT columns
            if 'actual_fare' not in df.columns:
                df['actual_fare'] = '0'  # String default for TEXT column
            if 'price' not in df.columns:
                df['price'] = df['actual_fare'].copy() if 'actual_fare' in df.columns else '0'
            if 'actual_occupancy' not in df.columns:
                df['actual_occupancy'] = '0'  # String default for TEXT column
            if 'expected_occupancy' not in df.columns:
                df['expected_occupancy'] = '0'  # String default for TEXT column
        else:
            print("No distinct price records found")
            
        return df
    except Exception as e:
        print(f"Error in get_distinct_prices_by_date_operator_time: {str(e)}")
        return None


def get_seat_wise_data(schedule_id=None, hours_before_departure=None, date_of_journey=None):
    """Get seat-wise data based on selected filters"""
    where_clauses = []
    params = {}
    
    if schedule_id:
        where_clauses.append('"schedule_id" = %(schedule_id)s')
        params['schedule_id'] = schedule_id
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    SELECT * FROM seat_wise_prices_partitioned
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
    """Get hours before departure data from seat_prices_partitioned table"""
    # Use the query directly from the seat_prices_partitioned table as provided by the user
    if schedule_id:
        query = """
        SELECT DISTINCT "hours_before_departure"
        FROM public.seat_prices_partitioned
        WHERE "schedule_id" = %(schedule_id)s
        ORDER BY "hours_before_departure" DESC
        """
        params = {'schedule_id': schedule_id}
    else:
        query = """
        SELECT DISTINCT "hours_before_departure"
        FROM public.seat_prices_partitioned
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
            
            # Remove NaN values
            df = df.dropna(subset=['hours_before_departure'])
            
            # Sort in descending order
            df = df.sort_values('hours_before_departure', ascending=False)
            
            # Get all unique values without any rounding
            unique_values = df['hours_before_departure'].unique().tolist()
            
            print(f"Unique hours before departure values: {unique_values}")
            
            # Return all values without any processing or rounding
            return [str(int(val)) if val.is_integer() else str(val) for val in unique_values]  # Format integers without decimal
    except Exception as e:
        print(f"Error getting hours before departure: {e}")
        return []
    
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

def get_occupancy_by_seat_type(schedule_id, seat_type, hours_before_departure=None):
    """
    Get occupancy data for a specific schedule_id, seat_type, and hours_before_departure
    """
    if schedule_id is None or seat_type is None:
        print("Error: schedule_id and seat_type are required for get_occupancy_by_seat_type")
        return {
            'actual_occupancy': 0,
            'expected_occupancy': 0
        }
    
    # Convert schedule_id to string to ensure consistency (DB stores as text)
    schedule_id = str(schedule_id)

    # Build query to get occupancy data for specific seat type
    query = """
    SELECT 
        "actual_occupancy"::NUMERIC(10,2) as "actual_occupancy",
        "expected_occupancy"::NUMERIC(10,2) as "expected_occupancy"
    FROM 
        seat_prices_partitioned
    WHERE 
        "schedule_id" = %(schedule_id)s
        AND "seat_type" = %(seat_type)s
    """
    
    # Add hours_before_departure filter if provided
    params = {'schedule_id': schedule_id, 'seat_type': seat_type}
    if hours_before_departure is not None:
        query += "AND ABS((\"hours_before_departure\")::float - %(hours_before_departure)s) < 0.01 "
        params['hours_before_departure'] = float(hours_before_departure)
    
    # Get the latest entry for this combination
    query += "ORDER BY \"TimeAndDateStamp\" DESC LIMIT 1"
    
    # Execute query
    df = execute_query(query, params)
    
    # Return default values if no data found
    if df is None or df.empty:
        print(f"No occupancy data found for schedule_id={schedule_id}, seat_type={seat_type}, hours_before_departure={hours_before_departure}")
        return {
            'actual_occupancy': 0,
            'expected_occupancy': 0
        }
    
    # Convert to numeric and round
    try:
        actual_occupancy = round(float(df['actual_occupancy'].iloc[0]), 2)
        expected_occupancy = round(float(df['expected_occupancy'].iloc[0]), 2)
    except (ValueError, TypeError) as e:
        print(f"Error converting occupancy values to float: {e}")
        return {
            'actual_occupancy': 0,
            'expected_occupancy': 0
        }
    
    return {
        'actual_occupancy': actual_occupancy,
        'expected_occupancy': expected_occupancy
    }

def get_demand_index(schedule_id, hours_before_departure=None, seat_type=None):
    """Get demand index for a specific schedule_id, hours_before_departure, and optionally seat_type"""
    try:
        if not schedule_id:
            print("DEBUG: No schedule_id provided for demand_index")
            return None
        
        # Convert schedule_id to string to ensure consistency
        schedule_id = str(schedule_id)
        print(f"DEBUG: Getting demand_index for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}, seat_type={seat_type}")
        
        params = {'schedule_id': schedule_id}
        
        # Build query variants based on filters
        if hours_before_departure is not None:
            params['hours_before_departure'] = float(hours_before_departure)
            if seat_type:
                params['seat_type'] = seat_type
                query = """
                SELECT ("demand_index") AS demand_index, "seat_type"
                FROM seat_prices_partitioned
                WHERE "schedule_id" = %(schedule_id)s
                  AND "seat_type" = %(seat_type)s
                  AND ABS(("hours_before_departure")::float - %(hours_before_departure)s) < 0.01
                ORDER BY "TimeAndDateStamp" DESC
                LIMIT 1
                """
            else:
                query = """
                SELECT DISTINCT ON ("seat_type")
                    "seat_type",
                    ("demand_index") AS demand_index
                FROM seat_prices_partitioned
                WHERE "schedule_id" = %(schedule_id)s
                  AND ABS(("hours_before_departure")::float - %(hours_before_departure)s) < 0.01
                ORDER BY "seat_type", "TimeAndDateStamp" DESC
                """
        else:
            if seat_type:
                params['seat_type'] = seat_type
                query = """
                SELECT ("demand_index") AS demand_index, "seat_type"
                FROM seat_prices_partitioned
                WHERE "schedule_id" = %(schedule_id)s
                  AND "seat_type" = %(seat_type)s
                ORDER BY "TimeAndDateStamp" DESC
                LIMIT 1
                """
            else:
                query = """
                SELECT DISTINCT ON ("seat_type")
                    "seat_type",
                    ("demand_index") AS demand_index
                FROM seat_prices_partitioned
                WHERE "schedule_id" = %(schedule_id)s
                ORDER BY "seat_type", "TimeAndDateStamp" DESC
                """
        
        print(f"DEBUG: Executing demand_index query: {query}")
        df = execute_query(query, params)
        
        if df is not None and not df.empty:
            print(f"DEBUG: DataFrame columns: {df.columns.tolist()}")
            
            # Check if demand_index column exists
            if 'demand_index' in df.columns:
                # If seat_type is provided, return a single demand index
                if seat_type or len(df) == 1:
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
                    # If no seat_type is provided, return a dictionary of demand indexes by seat type
                    demand_indexes = {}
                    for _, row in df.iterrows():
                        st = row['seat_type']
                        di = row['demand_index']
                        
                        # Skip None or NaN values
                        if pd.isna(di) or di is None:
                            continue
                            
                        # Process the demand index value
                        if isinstance(di, str):
                            if '/' in di or not di.replace('.', '', 1).isdigit():
                                demand_indexes[st] = di
                            else:
                                try:
                                    demand_indexes[st] = float(di)
                                except (ValueError, TypeError):
                                    demand_indexes[st] = str(di)
                        else:
                            try:
                                demand_indexes[st] = float(di)
                            except (ValueError, TypeError):
                                demand_indexes[st] = str(di)
                    
                    print(f"DEBUG: Found demand indexes by seat type: {demand_indexes}")
                    return demand_indexes
            else:
                print(f"DEBUG: demand_index column not found in result")
                return None
        else:
            print(f"DEBUG: No data found for schedule_id={schedule_id}, hours_before_departure={hours_before_departure}, seat_type={seat_type}")
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
    FROM seat_prices_partitioned
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

def get_seat_types_count(schedule_id):
    """
    Get the count of unique seat types for a specific schedule_id
    """
    try:
        if not schedule_id:
            print("DEBUG: No schedule_id provided for seat_types_count")
            return 0
        
        # Convert schedule_id to string to ensure consistency
        schedule_id = str(schedule_id)
        print(f"DEBUG: Getting seat types count for schedule_id={schedule_id}")
        
        # Query to count distinct seat types for the schedule ID
        query = """
        SELECT COUNT(DISTINCT "seat_type") as seat_types_count
        FROM seat_wise_prices_partitioned
        WHERE "schedule_id" = %(schedule_id)s
        """
        
        params = {'schedule_id': schedule_id}
        
        df = execute_query(query, params)
        
        if df is not None and not df.empty:
            seat_types_count = df['seat_types_count'].iloc[0]
            print(f"DEBUG: Found {seat_types_count} seat types for schedule_id={schedule_id}")
            return int(seat_types_count)
        else:
            print(f"DEBUG: No seat types found for schedule_id={schedule_id}")
            return 0
    except Exception as e:
        print(f"ERROR in get_seat_types_count: {e}")
        return 0

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
