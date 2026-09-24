import random
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import os


# -----------------------------------------
# Configuration
# -----------------------------------------

fake = Faker()

NUM_RECORDS = 20_000


HOTELS = [
    "Ocean View Hotel",
    "Grand Palace Hotel",
    "City Garden Hotel",
    "Sunrise Resort",
    "Blue Lagoon Hotel",
    "Royal Beach Resort",
    "Mountain View Hotel",
    "Green Valley Resort",
]


ROOM_TYPES = [
    "Standard",
    "Deluxe",
    "Suite",
    "Family",
    "Executive",
]


COUNTRIES = [
    "Sri Lanka",
    "India",
    "United Kingdom",
    "Australia",
    "Germany",
    "Singapore",
    "Canada",
    "United States",
]


STATUSES = [
    "Confirmed",
    "Cancelled",
    "Completed",
    "Pending",
]


# -----------------------------------------
# Generate random booking date
# -----------------------------------------

def random_booking_date():
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 9, 1)

    days = (end_date - start_date).days

    return start_date + timedelta(
        days=random.randint(0, days)
    )


# -----------------------------------------
# Generate one clean record
# -----------------------------------------

def generate_clean_record(booking_id):
    return {
        "booking_id": booking_id,
        "customer_name": fake.name(),
        "hotel_name": random.choice(HOTELS),
        "country": random.choice(COUNTRIES),
        "room_type": random.choice(ROOM_TYPES),
        "price": round(random.uniform(50, 500), 2),
        "rating": round(random.uniform(1, 5), 1),
        "booking_date": random_booking_date().strftime("%Y-%m-%d"),
        "status": random.choice(STATUSES),
    }


# -----------------------------------------
# Introduce dirty data
# -----------------------------------------

def introduce_dirty_data(df):

    # -------------------------------------
    # 1. Missing customer names
    # -------------------------------------

    missing_indices = random.sample(
        list(df.index),
        200
    )

    for index in missing_indices:
        df.loc[index, "customer_name"] = None


    # -------------------------------------
    # 2. Inconsistent country formatting
    # -------------------------------------

    country_indices = random.sample(
        list(df.index),
        500
    )

    for index in country_indices:

        country = df.loc[index, "country"]

        if country == "Sri Lanka":
            df.loc[index, "country"] = random.choice([
                "sri lanka",
                "SRI LANKA",
                " Sri Lanka",
                "Sri Lanka ",
            ])

        elif country == "India":
            df.loc[index, "country"] = random.choice([
                "india",
                "INDIA",
                " India",
                "India ",
            ])

        elif country == "United Kingdom":
            df.loc[index, "country"] = random.choice([
                "united kingdom",
                "UNITED KINGDOM",
                " United Kingdom",
                "United Kingdom ",
            ])

        elif country == "Australia":
            df.loc[index, "country"] = random.choice([
                "australia",
                "AUSTRALIA",
                " Australia",
                "Australia ",
            ])

        elif country == "Germany":
            df.loc[index, "country"] = random.choice([
                "germany",
                "GERMANY",
                " Germany",
                "Germany ",
            ])

        elif country == "Singapore":
            df.loc[index, "country"] = random.choice([
                "singapore",
                "SINGAPORE",
                " Singapore",
                "Singapore ",
            ])

        elif country == "Canada":
            df.loc[index, "country"] = random.choice([
                "canada",
                "CANADA",
                " Canada",
                "Canada ",
            ])

        elif country == "United States":
            df.loc[index, "country"] = random.choice([
                "united states",
                "UNITED STATES",
                " United States",
                "United States ",
            ])


    # -------------------------------------
    # 3. Invalid prices
    # -------------------------------------

    # Allow strings such as "N/A" and "unknown"
    df["price"] = df["price"].astype(object)

    invalid_price_indices = random.sample(
        list(df.index),
        100
    )

    for index in invalid_price_indices:
        df.loc[index, "price"] = random.choice([
            "N/A",
            "",
            None,
            "unknown"
        ])


    # -------------------------------------
    # 4. Invalid ratings
    # -------------------------------------

    # Allow invalid values
    df["rating"] = df["rating"].astype(object)

    invalid_rating_indices = random.sample(
        list(df.index),
        100
    )

    for index in invalid_rating_indices:
        df.loc[index, "rating"] = random.choice([
            -1,
            6,
            10,
            None
        ])


    # -------------------------------------
    # 5. Inconsistent date formats
    # -------------------------------------

    date_indices = random.sample(
        list(df.index),
        500
    )

    for index in date_indices:

        original_date = pd.to_datetime(
            df.loc[index, "booking_date"]
        )

        df.loc[index, "booking_date"] = random.choice([
            original_date.strftime("%d/%m/%Y"),
            original_date.strftime("%d-%b-%Y"),
            original_date.strftime("%d-%m-%Y"),
            original_date.strftime("%Y/%m/%d"),
        ])


    # -------------------------------------
    # 6. Duplicate records
    # -------------------------------------

    duplicate_rows = df.sample(
        300,
        random_state=42
    )

    df = pd.concat(
        [df, duplicate_rows],
        ignore_index=True
    )


    # -------------------------------------
    # 7. Shuffle dataset
    # -------------------------------------

    df = df.sample(
        frac=1,
        random_state=42
    ).reset_index(drop=True)


    return df


# -----------------------------------------
# Main function
# -----------------------------------------

def main():

    print("Generating dataset...")

    # -------------------------------------
    # Generate 20,000 clean records
    # -------------------------------------

    records = []

    for booking_id in range(
        10001,
        10001 + NUM_RECORDS
    ):

        records.append(
            generate_clean_record(booking_id)
        )


    # Convert records to DataFrame
    df = pd.DataFrame(records)

    print(
        f"Generated clean records: {len(df)}"
    )


    # -------------------------------------
    # Add dirty data
    # -------------------------------------

    df = introduce_dirty_data(df)

    print(
        f"Records after adding duplicates: {len(df)}"
    )


    # -------------------------------------
    # Create output directory
    # -------------------------------------

    output_directory = "data/raw"

    os.makedirs(
        output_directory,
        exist_ok=True
    )


    # -------------------------------------
    # Save CSV
    # -------------------------------------

    output_path = (
        f"{output_directory}/hotel_bookings.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )


    print(
        f"Dataset saved to: {output_path}"
    )

    print(
        f"Final record count: {len(df)}"
    )


# -----------------------------------------
# Run program
# -----------------------------------------

if __name__ == "__main__":
    main()