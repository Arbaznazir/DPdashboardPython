-- SQL script to create indexes for price comparison queries
-- These indexes will significantly improve query performance

-- Indexes for seat_prices_with_dt table
-- Main index for price queries (covers filtering, sorting, and DISTINCT ON operations)
CREATE INDEX IF NOT EXISTS idx_seat_prices_query 
ON seat_prices_with_dt 
(date_of_journey, operator_id, departure_time, schedule_id, seat_type, "TimeAndDateStamp" DESC);

-- Index for the relevant_schedules subquery
CREATE INDEX IF NOT EXISTS idx_seat_prices_schedules 
ON seat_prices_with_dt 
(date_of_journey, operator_id, departure_time, schedule_id);

-- Indexes for seat_wise_prices_with_dt table
-- Index for the latest_snapshots subquery
CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_snapshots 
ON seat_wise_prices_with_dt 
(schedule_id, seat_number, travel_date, "TimeAndDateStamp" DESC);

-- Index for the main join conditions
CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_join 
ON seat_wise_prices_with_dt 
(schedule_id, seat_number, "TimeAndDateStamp");

-- Additional index to speed up seat_type filtering and sorting
CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_type 
ON seat_wise_prices_with_dt 
(seat_type);

-- Indexes for seat_prices_raw table
-- Main index for price queries on raw table
CREATE INDEX IF NOT EXISTS idx_seat_prices_raw_query 
ON seat_prices_raw 
(date_of_journey, operator_id, schedule_id, seat_type, "TimeAndDateStamp" DESC);

-- Index for filtering on raw table
CREATE INDEX IF NOT EXISTS idx_seat_prices_raw_schedules 
ON seat_prices_raw 
(date_of_journey, operator_id, schedule_id);

-- Indexes for seat_wise_prices_raw table
-- Index for the latest snapshots on raw table
CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_raw_snapshots 
ON seat_wise_prices_raw 
(schedule_id, seat_number, travel_date, "TimeAndDateStamp" DESC);

-- Index for the main join conditions on raw table
CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_raw_join 
ON seat_wise_prices_raw 
(schedule_id, seat_number, "TimeAndDateStamp");

-- Additional index for seat_type on raw table
CREATE INDEX IF NOT EXISTS idx_seat_wise_prices_raw_type 
ON seat_wise_prices_raw 
(seat_type);

-- Note: After creating these indexes, you may need to run ANALYZE on the tables
-- to update the database statistics for the query planner
ANALYZE seat_prices_with_dt;
ANALYZE seat_wise_prices_with_dt;
ANALYZE seat_prices_raw;
ANALYZE seat_wise_prices_raw;
