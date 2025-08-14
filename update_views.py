"""
Script to update database views to use the correct case-sensitive column name "TimeAndDateStamp".
"""
import psycopg2
from db_utils import get_connection

def update_views():
    """Update all views to use the correct case-sensitive column name"""
    print("Updating views to use correct case-sensitive column names...")
    
    conn = get_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Update seat_prices_latest view
        print("Updating seat_prices_latest view...")
        cursor.execute("""
        DROP VIEW IF EXISTS seat_prices_latest;
        CREATE VIEW seat_prices_latest AS
        SELECT sp.*
        FROM seat_prices_partitioned sp
        JOIN (
            SELECT 
                date_of_journey,
                schedule_id,
                seat_type,
                MAX("TimeAndDateStamp") as latest_timestamp
            FROM seat_prices_partitioned
            GROUP BY date_of_journey, schedule_id, seat_type
        ) latest ON 
            sp.date_of_journey = latest.date_of_journey AND
            sp.schedule_id = latest.schedule_id AND
            sp.seat_type = latest.seat_type AND
            sp."TimeAndDateStamp" = latest.latest_timestamp;
        """)
        
        # Update seat_wise_prices_latest view
        print("Updating seat_wise_prices_latest view...")
        cursor.execute("""
        DROP VIEW IF EXISTS seat_wise_prices_latest;
        CREATE VIEW seat_wise_prices_latest AS
        SELECT swp.*
        FROM seat_wise_prices_partitioned swp
        JOIN (
            SELECT 
                travel_date,
                schedule_id,
                seat_number,
                MAX("TimeAndDateStamp") as latest_timestamp
            FROM seat_wise_prices_partitioned
            GROUP BY travel_date, schedule_id, seat_number
        ) latest ON 
            swp.travel_date = latest.travel_date AND
            swp.schedule_id = latest.schedule_id AND
            swp.seat_number = latest.seat_number AND
            swp."TimeAndDateStamp" = latest.latest_timestamp;
        """)
        
        # Update seat_prices_with_dt_latest view
        print("Updating seat_prices_with_dt_latest view...")
        cursor.execute("""
        DROP VIEW IF EXISTS seat_prices_with_dt_latest;
        CREATE VIEW seat_prices_with_dt_latest AS
        SELECT sp.*
        FROM seat_prices_with_dt_partitioned sp
        JOIN (
            SELECT 
                date_of_journey,
                schedule_id,
                seat_type,
                MAX("TimeAndDateStamp") as latest_timestamp
            FROM seat_prices_with_dt_partitioned
            GROUP BY date_of_journey, schedule_id, seat_type
        ) latest ON 
            sp.date_of_journey = latest.date_of_journey AND
            sp.schedule_id = latest.schedule_id AND
            sp.seat_type = latest.seat_type AND
            sp."TimeAndDateStamp" = latest.latest_timestamp;
        """)
        
        # Update seat_wise_prices_with_dt_latest view
        print("Updating seat_wise_prices_with_dt_latest view...")
        cursor.execute("""
        DROP VIEW IF EXISTS seat_wise_prices_with_dt_latest;
        CREATE VIEW seat_wise_prices_with_dt_latest AS
        SELECT swp.*
        FROM seat_wise_prices_with_dt_partitioned swp
        JOIN (
            SELECT 
                travel_date,
                schedule_id,
                seat_number,
                MAX("TimeAndDateStamp") as latest_timestamp
            FROM seat_wise_prices_with_dt_partitioned
            GROUP BY travel_date, schedule_id, seat_number
        ) latest ON 
            swp.travel_date = latest.travel_date AND
            swp.schedule_id = latest.schedule_id AND
            swp.seat_number = latest.seat_number AND
            swp."TimeAndDateStamp" = latest.latest_timestamp;
        """)
        
        # Update other views that might be using the latest views
        print("Updating other views...")
        
        # Update fngethoursbeforedeparture view
        cursor.execute("""
        DROP VIEW IF EXISTS fngethoursbeforedeparture;
        CREATE VIEW fngethoursbeforedeparture AS
        SELECT 
            sp.date_of_journey,
            sp.schedule_id,
            sp.departure_time,
            sp."TimeAndDateStamp",
            EXTRACT(EPOCH FROM (sp.departure_time::time - sp."TimeAndDateStamp"::time)) / 3600 AS hours_before_departure
        FROM seat_prices_with_dt_latest sp;
        """)
        
        # Check if occupancy column exists
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'seat_prices_with_dt_partitioned' AND column_name = 'occupancy';
        """)
        has_occupancy = cursor.fetchone() is not None
        
        # Update occupancies view based on column existence
        print("Updating occupancies view...")
        if has_occupancy:
            cursor.execute("""
            DROP VIEW IF EXISTS occupancies;
            CREATE VIEW occupancies AS
            SELECT 
                sp.date_of_journey,
                sp.schedule_id,
                sp.operator_id,
                sp.departure_time,
                sp."TimeAndDateStamp",
                sp.occupancy
            FROM seat_prices_with_dt_latest sp;
            """)
        else:
            print("⚠️ occupancy column not found, creating view without it")
            cursor.execute("""
            DROP VIEW IF EXISTS occupancies;
            CREATE VIEW occupancies AS
            SELECT 
                sp.date_of_journey,
                sp.schedule_id,
                sp.operator_id,
                sp.departure_time,
                sp."TimeAndDateStamp",
                NULL::numeric AS occupancy
            FROM seat_prices_with_dt_latest sp;
            """)
        
        # Check if expected_occupancy column exists
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'seat_prices_with_dt_partitioned' AND column_name = 'expected_occupancy';
        """)
        has_expected_occupancy = cursor.fetchone() is not None
        
        # Update expected_occupancies view based on column existence
        print("Updating expected_occupancies view...")
        if has_expected_occupancy:
            cursor.execute("""
            DROP VIEW IF EXISTS expected_occupancies;
            CREATE VIEW expected_occupancies AS
            SELECT 
                sp.date_of_journey,
                sp.schedule_id,
                sp.operator_id,
                sp.departure_time,
                sp."TimeAndDateStamp",
                sp.expected_occupancy
            FROM seat_prices_with_dt_latest sp;
            """)
        else:
            print("⚠️ expected_occupancy column not found, creating view without it")
            cursor.execute("""
            DROP VIEW IF EXISTS expected_occupancies;
            CREATE VIEW expected_occupancies AS
            SELECT 
                sp.date_of_journey,
                sp.schedule_id,
                sp.operator_id,
                sp.departure_time,
                sp."TimeAndDateStamp",
                NULL::numeric AS expected_occupancy
            FROM seat_prices_with_dt_latest sp;
            """)
        
        # Update dateofjourney view
        cursor.execute("""
        DROP VIEW IF EXISTS dateofjourney;
        CREATE VIEW dateofjourney AS
        SELECT DISTINCT date_of_journey, schedule_id
        FROM seat_prices_with_dt_partitioned;
        """)
        
        # Update schedule_id_text view
        cursor.execute("""
        DROP VIEW IF EXISTS schedule_id_text;
        CREATE VIEW schedule_id_text AS
        SELECT DISTINCT schedule_id::text
        FROM seat_prices_with_dt_partitioned;
        """)
        
        # Update actual_price_sp view
        cursor.execute("""
        DROP VIEW IF EXISTS actual_price_sp;
        CREATE VIEW actual_price_sp AS
        SELECT 
            sp.date_of_journey,
            sp.schedule_id,
            sp.seat_type,
            sp."TimeAndDateStamp",
            sp.price
        FROM seat_prices_latest sp;
        """)
        
        # Check if model_price column exists
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'seat_prices_partitioned' AND column_name = 'model_price';
        """)
        has_model_price = cursor.fetchone() is not None
        
        # Update model_price_sp view based on column existence
        print("Updating model_price_sp view...")
        if has_model_price:
            cursor.execute("""
            DROP VIEW IF EXISTS model_price_sp;
            CREATE VIEW model_price_sp AS
            SELECT 
                sp.date_of_journey,
                sp.schedule_id,
                sp.seat_type,
                sp."TimeAndDateStamp",
                sp.model_price
            FROM seat_prices_latest sp;
            """)
        else:
            print("⚠️ model_price column not found, creating view with price as model_price")
            cursor.execute("""
            DROP VIEW IF EXISTS model_price_sp;
            CREATE VIEW model_price_sp AS
            SELECT 
                sp.date_of_journey,
                sp.schedule_id,
                sp.seat_type,
                sp."TimeAndDateStamp",
                sp.price AS model_price
            FROM seat_prices_latest sp;
            """)
        
        conn.commit()
        print("✅ All views updated successfully")
        
    except Exception as e:
        print(f"⚠️ Error updating views: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    
    return True

if __name__ == "__main__":
    update_views()
