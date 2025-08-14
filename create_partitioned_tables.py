"""
Script to directly create partitioned tables with the correct schema.
"""
import psycopg2
from sqlalchemy import create_engine, text
from db_utils import get_connection

def create_partitioned_tables():
    """Create partitioned tables directly"""
    print("Creating partitioned tables...")
    
    conn = get_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Create seat_prices_partitioned
        print("Creating seat_prices_partitioned...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seat_prices_partitioned (
                LIKE seat_prices_raw INCLUDING ALL,
                PRIMARY KEY (date_of_journey, schedule_id, seat_type, "TimeAndDateStamp")
            ) PARTITION BY RANGE (date_of_journey);
        """)
        
        # Create seat_wise_prices_partitioned
        print("Creating seat_wise_prices_partitioned...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seat_wise_prices_partitioned (
                LIKE seat_wise_prices_raw INCLUDING ALL,
                PRIMARY KEY (travel_date, schedule_id, seat_number, "TimeAndDateStamp")
            ) PARTITION BY RANGE (travel_date);
        """)
        
        # Create seat_prices_with_dt_partitioned
        print("Creating seat_prices_with_dt_partitioned...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seat_prices_with_dt_partitioned (
                LIKE seat_prices_with_dt INCLUDING ALL,
                PRIMARY KEY (date_of_journey, schedule_id, seat_type, "TimeAndDateStamp")
            ) PARTITION BY RANGE (date_of_journey);
        """)
        
        # Create seat_wise_prices_with_dt_partitioned
        print("Creating seat_wise_prices_with_dt_partitioned...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seat_wise_prices_with_dt_partitioned (
                LIKE seat_wise_prices_with_dt INCLUDING ALL,
                PRIMARY KEY (travel_date, schedule_id, seat_number, "TimeAndDateStamp")
            ) PARTITION BY RANGE (travel_date);
        """)
        
        conn.commit()
        print("✅ All partitioned tables created successfully")
        
        # Create partitions for a date range
        print("Creating partitions for date range...")
        cursor.execute("""
            SELECT MIN(date_of_journey) AS min_date FROM seat_prices_raw
            UNION ALL
            SELECT MIN(travel_date) AS min_date FROM seat_wise_prices_raw
            ORDER BY min_date
            LIMIT 1
        """)
        min_date = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT MAX(date_of_journey) AS max_date FROM seat_prices_raw
            UNION ALL
            SELECT MAX(travel_date) AS max_date FROM seat_wise_prices_raw
            ORDER BY max_date DESC
            LIMIT 1
        """)
        max_date = cursor.fetchone()[0]
        
        if min_date and max_date:
            print(f"Creating partitions from {min_date} to {max_date}...")
            
            # Create a function to create partitions for a date range
            cursor.execute("""
                CREATE OR REPLACE FUNCTION create_partitions_for_range(start_date DATE, end_date DATE) RETURNS void AS $$
                DECLARE
                    partition_start DATE;
                    partition_end DATE;
                    partition_name TEXT;
                BEGIN
                    partition_start := start_date;
                    WHILE partition_start <= end_date LOOP
                        partition_end := partition_start + INTERVAL '7 days';
                        
                        -- Format partition name
                        partition_name := 'p' || to_char(partition_start, 'YYYY_MM_DD') || '_' || to_char(partition_end, 'YYYY_MM_DD');
                        
                        -- Create partition for seat_prices_partitioned
                        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_prices_%s PARTITION OF seat_prices_partitioned 
                                      FOR VALUES FROM (%L) TO (%L)', 
                                      partition_name, partition_start, partition_end);
                        
                        -- Create partition for seat_wise_prices_partitioned
                        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_wise_prices_%s PARTITION OF seat_wise_prices_partitioned 
                                      FOR VALUES FROM (%L) TO (%L)', 
                                      partition_name, partition_start, partition_end);
                        
                        -- Create partition for seat_prices_with_dt_partitioned
                        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_prices_with_dt_%s PARTITION OF seat_prices_with_dt_partitioned 
                                      FOR VALUES FROM (%L) TO (%L)', 
                                      partition_name, partition_start, partition_end);
                        
                        -- Create partition for seat_wise_prices_with_dt_partitioned
                        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_wise_prices_with_dt_%s PARTITION OF seat_wise_prices_with_dt_partitioned 
                                      FOR VALUES FROM (%L) TO (%L)', 
                                      partition_name, partition_start, partition_end);
                        
                        partition_start := partition_end;
                    END LOOP;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Call the function to create partitions
            cursor.execute(f"SELECT create_partitions_for_range('{min_date}', '{max_date}');")
            conn.commit()
            print("✅ Partitions created successfully")
        
    except Exception as e:
        print(f"⚠️ Error creating partitioned tables: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    
    return True

if __name__ == "__main__":
    create_partitioned_tables()
