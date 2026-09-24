import os
import pandas as pd

from src.extract import extract_data
from src.transform import transform_data
from src.validate import (
    remove_duplicates,
    validate_data
)
from src.load import load_to_postgres
from src.s3_utils import upload_file


RAW_FILE = "data/raw/hotel_bookings.csv"

REJECTED_FILE = "logs/rejected_records.csv"

CLEANED_FILE = "data/cleaned/hotel_bookings_cleaned.csv"


def main():

    print()
    print("=" * 60)
    print("HOTEL BOOKING ETL PIPELINE")
    print("=" * 60)

    # --------------------------------
    # 1. EXTRACT
    # --------------------------------

    df = extract_data(RAW_FILE)

    raw_record_count = len(df)

    upload_file(RAW_FILE, "raw") 

    # --------------------------------
    # 2. TRANSFORM
    # --------------------------------

    df = transform_data(df)

    # --------------------------------
    # 3. REMOVE DUPLICATES
    # --------------------------------

    df, duplicate_records = remove_duplicates(df)

    # --------------------------------
    # 4. VALIDATE
    # --------------------------------

    valid_df, rejected_df = validate_data(df)

    # --------------------------------
    # 5. COMBINE REJECTED RECORDS
    # --------------------------------

    if not duplicate_records.empty:

        rejected_df = pd.concat(
            [
                rejected_df,
                duplicate_records
            ],
            ignore_index=True
        )

    # --------------------------------
    # 6. SAVE REJECTED RECORDS
    # --------------------------------

    os.makedirs(
        "logs",
        exist_ok=True
    )

    rejected_df.to_csv(
        REJECTED_FILE,
        index=False
    )

    upload_file(REJECTED_FILE, "rejected")

    print(
        f"Rejected records saved to: "
        f"{REJECTED_FILE}"
    )

    # --------------------------------
    # 7. SAVE CLEANED DATA
    # --------------------------------

    os.makedirs(
        "data/cleaned",
        exist_ok=True
    )

    valid_df.to_csv(
        CLEANED_FILE,
        index=False
    )

    upload_file(CLEANED_FILE, "processed")

    print(
        f"Cleaned data saved to: "
        f"{CLEANED_FILE}"
    )

    # --------------------------------
    # 8. LOAD INTO POSTGRESQL
    # --------------------------------

    load_to_postgres(valid_df)

    # --------------------------------
    # 9. SUMMARY
    # --------------------------------

    print()
    print("=" * 60)
    print("ETL PIPELINE COMPLETED")
    print("=" * 60)

    print(
        f"Raw records       : {raw_record_count}"
    )

    print(
        f"Duplicate records : {len(duplicate_records)}"
    )

    print(
        f"Rejected records  : {len(rejected_df)}"
    )

    print(
        f"Loaded records    : {len(valid_df)}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()