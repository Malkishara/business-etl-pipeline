import pandas as pd


VALID_ROOM_TYPES = {
    "Standard",
    "Deluxe",
    "Suite",
    "Family",
    "Executive"
}


VALID_STATUSES = {
    "Confirmed",
    "Cancelled",
    "Completed",
    "Pending"
}


REQUIRED_COLUMNS = [
    "booking_id",
    "customer_name",
    "hotel_name",
    "country",
    "room_type",
    "price",
    "rating",
    "booking_date",
    "status"
]


def remove_duplicates(df):
    print("Checking duplicates...")

    duplicate_mask = df.duplicated(
        subset=["booking_id"],
        keep="first"
    )

    duplicate_records = df[
        duplicate_mask
    ].copy()

    duplicate_records["rejection_reason"] = (
        "Duplicate booking_id"
    )

    clean_df = df[
        ~duplicate_mask
    ].copy()

    print(
        f"Duplicate records removed: "
        f"{len(duplicate_records)}"
    )

    return clean_df, duplicate_records


def validate_data(df):
    print("Validating records...")

    valid_records = []
    rejected_records = []

    for _, row in df.iterrows():

        errors = []

        # Check required fields
        for column in REQUIRED_COLUMNS:

            if pd.isna(row[column]):
                errors.append(
                    f"Missing {column}"
                )

        # Validate price
        if pd.notna(row["price"]):

            if row["price"] <= 0:
                errors.append(
                    "Price must be greater than 0"
                )

        # Validate rating
        if pd.notna(row["rating"]):

            if row["rating"] < 1 or row["rating"] > 5:
                errors.append(
                    "Rating must be between 1 and 5"
                )

        # Validate room type
        if pd.notna(row["room_type"]):

            if row["room_type"] not in VALID_ROOM_TYPES:
                errors.append(
                    "Invalid room type"
                )

        # Validate status
        if pd.notna(row["status"]):

            if row["status"] not in VALID_STATUSES:
                errors.append(
                    "Invalid status"
                )

        # Store rejected record
        if errors:

            rejected_record = row.to_dict()

            rejected_record["rejection_reason"] = (
                "; ".join(errors)
            )

            rejected_records.append(
                rejected_record
            )

        else:

            valid_records.append(
                row.to_dict()
            )

    valid_df = pd.DataFrame(
        valid_records
    )

    rejected_df = pd.DataFrame(
        rejected_records
    )

    print(
        f"Valid records: {len(valid_df)}"
    )

    print(
        f"Rejected records: {len(rejected_df)}"
    )

    return valid_df, rejected_df