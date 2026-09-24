CREATE TABLE IF NOT EXISTS hotel_bookings (
    booking_id INTEGER PRIMARY KEY,

    customer_name VARCHAR(255) NOT NULL,

    hotel_name VARCHAR(255) NOT NULL,

    country VARCHAR(100) NOT NULL,

    room_type VARCHAR(50) NOT NULL,

    price NUMERIC(10, 2) NOT NULL
        CHECK (price > 0),

    rating NUMERIC(2, 1) NOT NULL
        CHECK (rating >= 1 AND rating <= 5),

    booking_date DATE NOT NULL,

    status VARCHAR(50) NOT NULL
        CHECK (
            status IN (
                'Confirmed',
                'Cancelled',
                'Completed',
                'Pending'
            )
        )
);