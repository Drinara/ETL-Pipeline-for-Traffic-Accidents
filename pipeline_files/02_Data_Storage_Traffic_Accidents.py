import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pathlib import Path

def main():
    try:
        # Set up paths
        BASE_DIR = Path(__file__).resolve().parent.parent
        ENV_PATH = BASE_DIR / ".env"
        CLEANED_PATH = BASE_DIR / "pipeline_files" / "cleaned_traffic_data.csv"
        
        # Load environment variables
        load_dotenv(ENV_PATH)
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT')
        DB_NAME = os.getenv('DB_NAME')

        # Load cleaned dataset
        df = pd.read_csv(CLEANED_PATH)
        print("Dataset Loaded. Data types:\n", df.dtypes)

        # Split dataset
        injury_cols = [
            'crash_id', 'injuries_total', 'injuries_fatal', 'injuries_incapacitating',
            'injuries_non_incapacitating', 'injuries_reported_not_evident',
            'injuries_no_indication', 'most_severe_injury'
        ]
        injury_df = df[injury_cols].copy()
        accidents_df = df.drop(columns=injury_cols[1:])

        # Create database engine
        engine = create_engine(
            f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        )
        
        # Push to PostgreSQL
        accidents_df.to_sql('traffic_accidents', engine, if_exists='replace', index=False)
        injury_df.to_sql('injury_data', engine, if_exists='replace', index=False)
        print("\nData pushed successfully to PostgreSQL!")

    except Exception as e:
        print("\nData storage failed:", str(e))
        raise

if __name__ == "__main__":
    main()