import pandas as pd
import numpy as np
import os
from pathlib import Path

def main():
    try:
        # Set up paths
        BASE_DIR = Path(__file__).resolve().parent.parent
        RAW_PATH = BASE_DIR / "pipeline_files" / "traffic_accidents.csv"
        CLEANED_PATH = BASE_DIR / "pipeline_files" / "cleaned_traffic_data.csv"
        
        # Load raw dataset
        df = pd.read_csv(RAW_PATH, nrows=50000)
        print("Original data shape:", df.shape)

        # Convert crash_date to datetime
        df['crash_date'] = pd.to_datetime(df['crash_date'], errors='coerce')
        print("Invalid dates found:", df['crash_date'].isna().sum())

        # Drop duplicate rows
        df = df.drop_duplicates()
        print("Shape after removing duplicates:", df.shape)

        # Standardize text columns
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].str.strip().str.upper()

        # Replace ambiguous values
        df.replace(
            ['UNKNOWN', 'UNKNOWN INTERSECTION TYPE', 'NOT REPORTED', 'OTHER', 'NOT APPLICABLE'],
            np.nan, inplace=True
        )

        # Drop rows with any nulls
        df = df.dropna()
        print("Shape after dropping rows with null values:", df.shape)

        # Clean lighting_condition
        df['lighting_condition'] = df['lighting_condition'].astype(str).str.replace(',', ' AND ')

        # Convert numeric columns
        numeric_cols = [
            'num_units', 'injuries_total', 'injuries_fatal', 'injuries_incapacitating',
            'injuries_non_incapacitating', 'injuries_reported_not_evident',
            'injuries_no_indication', 'crash_hour', 'crash_day_of_week', 'crash_month'
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Sort by date and create crash_id
        df = df.sort_values(by='crash_date').reset_index(drop=True)
        df['crash_id'] = ['cid' + str(i).zfill(6) for i in range(1, len(df) + 1)]
        df = df[['crash_id'] + [col for col in df.columns if col != 'crash_id']]

        # Validate crash_id
        if df['crash_id'].duplicated().any():
            print("Warning: Duplicate crash_id values found.")
        else:
            print("All crash_id values are unique.")

        # Map numeric values to names
        day_map = {1: 'MONDAY', 2: 'TUESDAY', 3: 'WEDNESDAY', 4: 'THURSDAY',
                   5: 'FRIDAY', 6: 'SATURDAY', 7: 'SUNDAY'}
        month_map = {1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL', 5: 'MAY', 6: 'JUNE',
                     7: 'JULY', 8: 'AUGUST', 9: 'SEPTEMBER', 10: 'OCTOBER', 11: 'NOVEMBER', 12: 'DECEMBER'}
        df['crash_day_of_week'] = df['crash_day_of_week'].map(day_map)
        df['crash_month'] = df['crash_month'].map(month_map)

        # Save cleaned dataset
        df.to_csv(CLEANED_PATH, index=False)
        print("Cleaned dataset saved successfully.")
        print(df.dtypes)

    except Exception as e:
        print("Data cleaning failed:", str(e))
        raise

if __name__ == "__main__":
    main()