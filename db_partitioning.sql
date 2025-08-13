-- SQL script to create partitioned tables for price comparison data
-- This will significantly improve query performance by partitioning data into 7-day chunks

-- First, create the function to manage partitions
CREATE OR REPLACE FUNCTION create_partitions_for_range(start_date DATE, end_date DATE) 
RETURNS void AS $$
DECLARE
    curr_date DATE := start_date;
    next_date DATE;
    partition_name TEXT;
BEGIN
    WHILE curr_date < end_date LOOP
        next_date := curr_date + INTERVAL '7 days';
        
        -- Format partition names
        partition_name := 'p' || to_char(curr_date, 'YYYY_MM_DD') || '_' || to_char(next_date, 'YYYY_MM_DD');
        
        -- Create partition for seat_prices_with_dt if it doesn't exist
        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_prices_%s PARTITION OF seat_prices_partitioned
            FOR VALUES FROM (%L) TO (%L)', partition_name, curr_date, next_date);
        
        -- Create partition for seat_wise_prices_with_dt if it doesn't exist
        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_wise_prices_%s PARTITION OF seat_wise_prices_partitioned
            FOR VALUES FROM (%L) TO (%L)', partition_name, curr_date, next_date);
        
        -- Create partition for seat_prices_raw if it doesn't exist
        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_prices_raw_%s PARTITION OF seat_prices_raw_partitioned
            FOR VALUES FROM (%L) TO (%L)', partition_name, curr_date, next_date);
        
        -- Create partition for seat_wise_prices_raw if it doesn't exist
        EXECUTE format('CREATE TABLE IF NOT EXISTS seat_wise_prices_raw_%s PARTITION OF seat_wise_prices_raw_partitioned
            FOR VALUES FROM (%L) TO (%L)', partition_name, curr_date, next_date);
        
        -- Note: We don't need to disable indexes as they will be created after data loading
        -- PostgreSQL doesn't support ALTER INDEX ALL ON table DISABLE syntax
        
        curr_date := next_date;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to create indexes on partitions after data loading
CREATE OR REPLACE FUNCTION create_partition_indexes(partition_name TEXT) 
RETURNS void AS $$
BEGIN
    -- Create indexes on the partitions
    -- For seat_prices_with_dt partition
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_prices_%s_query 
        ON seat_prices_%s (date_of_journey, schedule_id, seat_type, TimeAndDateStamp DESC)',
        partition_name, partition_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_prices_%s_schedules 
        ON seat_prices_%s (date_of_journey, schedule_id)',
        partition_name, partition_name);
    
    -- For seat_wise_prices_with_dt partition
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_%s_snapshots 
        ON seat_wise_prices_%s (schedule_id, seat_number, travel_date, TimeAndDateStamp DESC)',
        partition_name, partition_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_%s_join 
        ON seat_wise_prices_%s (schedule_id, seat_number, TimeAndDateStamp)',
        partition_name, partition_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_%s_type 
        ON seat_wise_prices_%s (seat_type)',
        partition_name, partition_name);
    
    -- For seat_prices_raw partition
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_prices_raw_%s_query 
        ON seat_prices_raw_%s (date_of_journey, schedule_id, seat_type, TimeAndDateStamp DESC)',
        partition_name, partition_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_prices_raw_%s_schedules 
        ON seat_prices_raw_%s (date_of_journey, schedule_id)',
        partition_name, partition_name);
    
    -- For seat_wise_prices_raw partition
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_raw_%s_snapshots 
        ON seat_wise_prices_raw_%s (schedule_id, seat_number, travel_date, TimeAndDateStamp DESC)',
        partition_name, partition_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_raw_%s_join 
        ON seat_wise_prices_raw_%s (schedule_id, seat_number, TimeAndDateStamp)',
        partition_name, partition_name);
    
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_raw_%s_type 
        ON seat_wise_prices_raw_%s (seat_type)',
        partition_name, partition_name);
    
    -- Note: PostgreSQL doesn't support ALTER INDEX ALL ON table ENABLE syntax
    -- Indexes are automatically enabled when created
    RAISE NOTICE 'Indexes created for partition %', partition_name;
END;
$$ LANGUAGE plpgsql;

-- Get table structure from existing tables and create partitioned tables
DO $$
DECLARE
    column_list_prices TEXT;
    column_list_seat_prices TEXT;
    column_list_prices_raw TEXT;
    column_list_seat_prices_raw TEXT;
BEGIN
    -- Get column definitions for seat_prices_with_dt
    SELECT string_agg(column_name || ' ' || data_type || 
                     CASE WHEN character_maximum_length IS NOT NULL 
                          THEN '(' || character_maximum_length || ')' 
                          ELSE '' END, 
                     ', ') 
    INTO column_list_prices
    FROM information_schema.columns 
    WHERE table_name = 'seat_prices_with_dt';

    -- Get column definitions for seat_wise_prices_with_dt
    SELECT string_agg(column_name || ' ' || data_type || 
                     CASE WHEN character_maximum_length IS NOT NULL 
                          THEN '(' || character_maximum_length || ')' 
                          ELSE '' END, 
                     ', ') 
    INTO column_list_seat_prices
    FROM information_schema.columns 
    WHERE table_name = 'seat_wise_prices_with_dt';
    
    -- Get column definitions for seat_prices_raw
    SELECT string_agg(column_name || ' ' || data_type || 
                     CASE WHEN character_maximum_length IS NOT NULL 
                          THEN '(' || character_maximum_length || ')' 
                          ELSE '' END, 
                     ', ') 
    INTO column_list_prices_raw
    FROM information_schema.columns 
    WHERE table_name = 'seat_prices_raw';

    -- Get column definitions for seat_wise_prices_raw
    SELECT string_agg(column_name || ' ' || data_type || 
                     CASE WHEN character_maximum_length IS NOT NULL 
                          THEN '(' || character_maximum_length || ')' 
                          ELSE '' END, 
                     ', ') 
    INTO column_list_seat_prices_raw
    FROM information_schema.columns 
    WHERE table_name = 'seat_wise_prices_raw';

    -- Drop existing tables if they exist
    EXECUTE 'DROP TABLE IF EXISTS seat_prices_partitioned CASCADE';
    EXECUTE 'DROP TABLE IF EXISTS seat_wise_prices_partitioned CASCADE';
    EXECUTE 'DROP TABLE IF EXISTS seat_prices_raw_partitioned CASCADE';
    EXECUTE 'DROP TABLE IF EXISTS seat_wise_prices_raw_partitioned CASCADE';
    
    -- Create partitioned seat_prices_with_dt table
    EXECUTE 'CREATE TABLE seat_prices_partitioned (' || 
            column_list_prices || 
            ', PRIMARY KEY (date_of_journey, schedule_id, seat_type, TimeAndDateStamp)' ||
            ') PARTITION BY RANGE (date_of_journey)';

    -- Create partitioned seat_wise_prices_with_dt table
    EXECUTE 'CREATE TABLE seat_wise_prices_partitioned (' || 
            column_list_seat_prices || 
            ', PRIMARY KEY (travel_date, schedule_id, seat_number, TimeAndDateStamp)' ||
            ') PARTITION BY RANGE (travel_date)';
    
    -- Create partitioned seat_prices_raw table
    EXECUTE 'CREATE TABLE seat_prices_raw_partitioned (' || 
            column_list_prices_raw || 
            ', PRIMARY KEY (date_of_journey, schedule_id, seat_type, TimeAndDateStamp)' ||
            ') PARTITION BY RANGE (date_of_journey)';

    -- Create partitioned seat_wise_prices_raw table
    EXECUTE 'CREATE TABLE seat_wise_prices_raw_partitioned (' || 
            column_list_seat_prices_raw || 
            ', PRIMARY KEY (travel_date, schedule_id, seat_number, TimeAndDateStamp)' ||
            ') PARTITION BY RANGE (travel_date)';
    
    RAISE NOTICE 'Partitioned tables created successfully';
END $$;

-- Function to find the minimum date in the data
CREATE OR REPLACE FUNCTION get_min_date() 
RETURNS DATE AS $$
DECLARE
    min_date_prices DATE;
    min_date_seat_prices DATE;
    min_date_prices_raw DATE;
    min_date_seat_prices_raw DATE;
    result_date DATE;
BEGIN
    -- Get minimum date from seat_prices_with_dt
    SELECT MIN(date_of_journey) INTO min_date_prices
    FROM seat_prices_with_dt;
    
    -- Get minimum date from seat_wise_prices_with_dt
    SELECT MIN(travel_date) INTO min_date_seat_prices
    FROM seat_wise_prices_with_dt;
    
    -- Get minimum date from seat_prices_raw
    SELECT MIN(date_of_journey) INTO min_date_prices_raw
    FROM seat_prices_raw;
    
    -- Get minimum date from seat_wise_prices_raw
    SELECT MIN(travel_date) INTO min_date_seat_prices_raw
    FROM seat_wise_prices_raw;
    
    -- Return the earliest date from all tables
    result_date := min_date_prices;
    
    IF result_date IS NULL OR (min_date_seat_prices IS NOT NULL AND min_date_seat_prices < result_date) THEN
        result_date := min_date_seat_prices;
    END IF;
    
    IF result_date IS NULL OR (min_date_prices_raw IS NOT NULL AND min_date_prices_raw < result_date) THEN
        result_date := min_date_prices_raw;
    END IF;
    
    IF result_date IS NULL OR (min_date_seat_prices_raw IS NOT NULL AND min_date_seat_prices_raw < result_date) THEN
        result_date := min_date_seat_prices_raw;
    END IF;
    
    -- If still NULL, use a default date
    IF result_date IS NULL THEN
        result_date := CURRENT_DATE - INTERVAL '30 days';
    END IF;
    
    RETURN result_date;
END;
$$ LANGUAGE plpgsql;

-- Function to find the maximum date in the data
CREATE OR REPLACE FUNCTION get_max_date() 
RETURNS DATE AS $$
DECLARE
    max_date_prices DATE;
    max_date_seat_prices DATE;
    max_date_prices_raw DATE;
    max_date_seat_prices_raw DATE;
    result_date DATE;
BEGIN
    -- Get maximum date from seat_prices_with_dt
    SELECT MAX(date_of_journey) INTO max_date_prices
    FROM seat_prices_with_dt;
    
    -- Get maximum date from seat_wise_prices_with_dt
    SELECT MAX(travel_date) INTO max_date_seat_prices
    FROM seat_wise_prices_with_dt;
    
    -- Get maximum date from seat_prices_raw
    SELECT MAX(date_of_journey) INTO max_date_prices_raw
    FROM seat_prices_raw;
    
    -- Get maximum date from seat_wise_prices_raw
    SELECT MAX(travel_date) INTO max_date_seat_prices_raw
    FROM seat_wise_prices_raw;
    
    -- Return the latest date from all tables
    result_date := max_date_prices;
    
    IF result_date IS NULL OR (max_date_seat_prices IS NOT NULL AND max_date_seat_prices > result_date) THEN
        result_date := max_date_seat_prices;
    END IF;
    
    IF result_date IS NULL OR (max_date_prices_raw IS NOT NULL AND max_date_prices_raw > result_date) THEN
        result_date := max_date_prices_raw;
    END IF;
    
    IF result_date IS NULL OR (max_date_seat_prices_raw IS NOT NULL AND max_date_seat_prices_raw > result_date) THEN
        result_date := max_date_seat_prices_raw;
    END IF;
    
    -- If still NULL, use a default date
    IF result_date IS NULL THEN
        result_date := CURRENT_DATE + INTERVAL '30 days';
    END IF;
    
    RETURN result_date;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate data in batches for a specific partition
CREATE OR REPLACE FUNCTION migrate_data_to_partition_batch(
    partition_name TEXT,
    start_date DATE,
    end_date DATE,
    batch_size INTEGER DEFAULT 500000
) RETURNS INTEGER AS $$
DECLARE
    total_migrated INTEGER := 0;
    batch_migrated INTEGER;
    prices_migrated INTEGER;
    seat_prices_migrated INTEGER;
    prices_raw_migrated INTEGER;
    seat_prices_raw_migrated INTEGER;
BEGIN
    -- Migrate seat_prices_with_dt data in batches
    LOOP
        EXECUTE format('
            WITH moved AS (
                SELECT * FROM seat_prices_with_dt
                WHERE date_of_journey >= %L AND date_of_journey < %L
                LIMIT %s
            )
            INSERT INTO seat_prices_%s
            SELECT * FROM moved
            ON CONFLICT DO NOTHING
        ', start_date, end_date, batch_size, partition_name);
        
        GET DIAGNOSTICS prices_migrated = ROW_COUNT;
        total_migrated := total_migrated + prices_migrated;
        
        RAISE NOTICE 'Migrated % rows to seat_prices_%', prices_migrated, partition_name;
        
        EXIT WHEN prices_migrated < batch_size;
    END LOOP;
    
    -- Migrate seat_wise_prices_with_dt data in batches
    LOOP
        EXECUTE format('
            WITH moved AS (
                SELECT * FROM seat_wise_prices_with_dt
                WHERE travel_date >= %L AND travel_date < %L
                LIMIT %s
            )
            INSERT INTO seat_wise_prices_%s
            SELECT * FROM moved
            ON CONFLICT DO NOTHING
        ', start_date, end_date, batch_size, partition_name);
        
        GET DIAGNOSTICS seat_prices_migrated = ROW_COUNT;
        total_migrated := total_migrated + seat_prices_migrated;
        
        RAISE NOTICE 'Migrated % rows to seat_wise_prices_%', seat_prices_migrated, partition_name;
        
        EXIT WHEN seat_prices_migrated < batch_size;
    END LOOP;
    
    -- Migrate seat_prices_raw data in batches
    LOOP
        EXECUTE format('
            WITH moved AS (
                SELECT * FROM seat_prices_raw
                WHERE date_of_journey >= %L AND date_of_journey < %L
                LIMIT %s
            )
            INSERT INTO seat_prices_raw_%s
            SELECT * FROM moved
            ON CONFLICT DO NOTHING
        ', start_date, end_date, batch_size, partition_name);
        
        GET DIAGNOSTICS prices_raw_migrated = ROW_COUNT;
        total_migrated := total_migrated + prices_raw_migrated;
        
        RAISE NOTICE 'Migrated % rows to seat_prices_raw_%', prices_raw_migrated, partition_name;
        
        EXIT WHEN prices_raw_migrated < batch_size;
    END LOOP;
    
    -- Migrate seat_wise_prices_raw data in batches
    LOOP
        EXECUTE format('
            WITH moved AS (
                SELECT * FROM seat_wise_prices_raw
                WHERE travel_date >= %L AND travel_date < %L
                LIMIT %s
            )
            INSERT INTO seat_wise_prices_raw_%s
            SELECT * FROM moved
            ON CONFLICT DO NOTHING
        ', start_date, end_date, batch_size, partition_name);
        
        GET DIAGNOSTICS seat_prices_raw_migrated = ROW_COUNT;
        total_migrated := total_migrated + seat_prices_raw_migrated;
        
        RAISE NOTICE 'Migrated % rows to seat_wise_prices_raw_%', seat_prices_raw_migrated, partition_name;
        
        EXIT WHEN seat_prices_raw_migrated < batch_size;
    END LOOP;
    
    RETURN total_migrated;
END;
$$ LANGUAGE plpgsql;

-- Function to create partitions from min to max date and migrate data
CREATE OR REPLACE FUNCTION create_partitions_and_migrate_data(
    batch_size INTEGER DEFAULT 500000
) RETURNS void AS $$
DECLARE
    min_date DATE;
    max_date DATE;
    curr_date DATE;
    next_date DATE;
    partition_name TEXT;
    total_migrated INTEGER := 0;
    partition_migrated INTEGER;
BEGIN
    -- Get min and max dates from data
    min_date := get_min_date();
    max_date := get_max_date();
    
    -- Round min_date down to the nearest Monday
    min_date := min_date - EXTRACT(DOW FROM min_date)::INTEGER;
    
    -- Add a buffer to max_date
    max_date := max_date + INTERVAL '30 days';
    
    RAISE NOTICE 'Creating partitions from % to %', min_date, max_date;
    
    -- Create partitions
    PERFORM create_partitions_for_range(min_date, max_date);
    
    -- Migrate data to each partition
    curr_date := min_date;
    WHILE curr_date < max_date LOOP
        next_date := curr_date + INTERVAL '7 days';
        
        -- Format partition name
        partition_name := 'p' || to_char(curr_date, 'YYYY_MM_DD') || '_' || to_char(next_date, 'YYYY_MM_DD');
        
        RAISE NOTICE 'Migrating data to partition % (% to %)', partition_name, curr_date, next_date;
        
        -- Migrate data to this partition
        partition_migrated := migrate_data_to_partition_batch(partition_name, curr_date, next_date, batch_size);
        total_migrated := total_migrated + partition_migrated;
        
        -- Create indexes for this partition
        PERFORM create_partition_indexes(partition_name);
        
        curr_date := next_date;
    END LOOP;
    
    RAISE NOTICE 'Total rows migrated: %', total_migrated;
    
    -- Create views to maintain backward compatibility
    CREATE OR REPLACE VIEW seat_prices_with_dt_view AS
    SELECT * FROM seat_prices_partitioned;
    
    CREATE OR REPLACE VIEW seat_wise_prices_with_dt_view AS
    SELECT * FROM seat_wise_prices_partitioned;
    
    CREATE OR REPLACE VIEW seat_prices_raw_view AS
    SELECT * FROM seat_prices_raw_partitioned;
    
    CREATE OR REPLACE VIEW seat_wise_prices_raw_view AS
    SELECT * FROM seat_wise_prices_raw_partitioned;
    
    -- Analyze the new tables to update statistics
    ANALYZE seat_prices_partitioned;
    ANALYZE seat_wise_prices_partitioned;
    ANALYZE seat_prices_raw_partitioned;
    ANALYZE seat_wise_prices_raw_partitioned;
END;
$$ LANGUAGE plpgsql;
