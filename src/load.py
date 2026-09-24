import psycopg2
from psycopg2.extras import execute_values

import os
from dotenv import load_dotenv
load_dotenv()


def load_to_postgres(df):

    print("Loading data into PostgreSQL...")

    connection = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "hotel_etl"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
)

    cursor = connection.cursor()

    # Create table
    create_table_query = """
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
    """

    cursor.execute(create_table_query)

    # Insert records
    insert_query = """
    INSERT INTO hotel_bookings (
        booking_id,
        customer_name,
        hotel_name,
        country,
        room_type,
        price,
        rating,
        booking_date,
        status
    )
    VALUES %s
    ON CONFLICT (booking_id)
    DO NOTHING;
    """

    records = []

    for _, row in df.iterrows():

        records.append((
            int(row["booking_id"]),
            str(row["customer_name"]),
            str(row["hotel_name"]),
            str(row["country"]),
            str(row["room_type"]),
            float(row["price"]),
            float(row["rating"]),
            row["booking_date"].date(),
            str(row["status"])
        ))

    if records:

        execute_values(
            cursor,
            insert_query,
            records
        )

    connection.commit()

    cursor.close()
    connection.close()

    print(
        f"Loaded {len(records)} records into PostgreSQL."
    )