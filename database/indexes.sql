-- Index for date-based analytical queries
CREATE INDEX IF NOT EXISTS idx_booking_date
ON hotel_bookings(booking_date);


-- Index for country-based filtering/grouping
CREATE INDEX IF NOT EXISTS idx_country
ON hotel_bookings(country);


-- Index for booking status filtering
CREATE INDEX IF NOT EXISTS idx_status
ON hotel_bookings(status);


-- Index for hotel-based queries
CREATE INDEX IF NOT EXISTS idx_hotel_name
ON hotel_bookings(hotel_name);


-- Composite index for queries
-- filtering by status and booking date
CREATE INDEX IF NOT EXISTS idx_status_booking_date
ON hotel_bookings(status, booking_date);


-- Update PostgreSQL statistics
ANALYZE hotel_bookings;