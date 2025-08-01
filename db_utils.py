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
