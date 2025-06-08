import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from joblib import load
from pathlib import Path

def predict_injury():
    try:
        # Set up paths
        BASE_DIR = Path(__file__).resolve().parent.parent
        ENV_PATH = BASE_DIR / ".env"
        MODEL_PATH = BASE_DIR / "ml_modeling" / "injury_model.pkl"
        ENCODERS_PATH = BASE_DIR / "ml_modeling" / "label_encoders.pkl"
        
        # Load environment variables
        load_dotenv(ENV_PATH)
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")

        # Create database engine
        engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

        # Load new data
        query = """
        SELECT * FROM traffic_accidents
        WHERE crash_id NOT IN (SELECT crash_id FROM injury_data);
        """
        df = pd.read_sql(query, engine)

        if df.empty:
            print("No new data to predict.")
            return

        # Prepare features
        drop_cols = ["crash_id", "crash_date"]
        df_model = df.drop(columns=drop_cols).fillna("UNKNOWN")

        # Load encoders and model
        label_encoders = load(ENCODERS_PATH)
        clf = load(MODEL_PATH)

        # Apply encoders
        for col in df_model.select_dtypes(include="object").columns:
            if col in label_encoders:
                le = label_encoders[col]
                # Handle unseen labels
                mask = ~df_model[col].isin(le.classes_)
                df_model.loc[mask, col] = 'UNKNOWN'
                df_model[col] = le.transform(df_model[col])

        # Predict
        preds = clf.predict(df_model)
        df['injury_occurred_pred'] = preds

        # Save predictions to database
        df[['crash_id', 'injury_occurred_pred']].to_sql(
            'injury_predictions', 
            engine, 
            if_exists='append', 
            index=False
        )
        print(f"Saved {len(df)} predictions to database")

    except Exception as e:
        print("Prediction failed:", str(e))
        raise

if __name__ == "__main__":
    predict_injury()