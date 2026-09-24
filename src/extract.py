import pandas as pd


def extract_data(file_path):
    print("Extracting raw data...")

    df = pd.read_csv(file_path)

    print(f"Extracted records: {len(df)}")

    return df