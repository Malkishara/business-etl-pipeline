import pandas as pd


# Every date format that appears in the raw data
DATE_FORMATS = [
    "%Y-%m-%d",    # 2026-03-05
    "%Y/%m/%d",    # 2026/03/05
    "%d/%m/%Y",    # 05/03/2026
    "%d-%m-%Y",    # 05-03-2026
    "%d-%b-%Y",    # 05-Mar-2026
]


def parse_dates(series):
    """Try each known format in turn. Dates matching none become NaT."""
    s = series.astype("string").str.strip()
    parsed = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        parsed = parsed.fillna(pd.to_datetime(s, format=fmt, errors="coerce"))
    return parsed


def transform_data(df):
    print("Transforming data...")

    df = df.copy()

    # Clean text columns
    text_columns = [
        "customer_name",
        "hotel_name",
        "country",
        "room_type",
        "status"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # Standardize country
    df["country"] = df["country"].str.title()

    # Standardize room type
    df["room_type"] = df["room_type"].str.title()

    # Standardize status
    df["status"] = df["status"].str.title()

    # Convert booking ID to numeric
    df["booking_id"] = pd.to_numeric(df["booking_id"], errors="coerce")

    # Convert price to numeric
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Convert rating to numeric
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # Convert booking date (handles all known formats)
    df["booking_date"] = parse_dates(df["booking_date"])

    print("Transformation completed.")

    return df