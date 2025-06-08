import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from joblib import dump
import numpy as np

def main():
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

        # Create DB engine
        engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

        # Load data
        traffic_df = pd.read_sql("SELECT * FROM traffic_accidents;", engine)
        injury_df = pd.read_sql("SELECT * FROM injury_data;", engine)
        merged_df = pd.merge(traffic_df, injury_df, on='crash_id')

        # Create target column
        merged_df["injury_occurred"] = merged_df["injuries_total"].apply(lambda x: 1 if x > 0 else 0)

        # Prepare features
        drop_cols = [
            "crash_id", "crash_date",
            "injuries_total", "injuries_fatal", "injuries_incapacitating",
            "injuries_non_incapacitating", "injuries_reported_not_evident",
            "injuries_no_indication", "most_severe_injury"
        ]
        df_model = merged_df.drop(columns=drop_cols).fillna("UNKNOWN")

        # Label encoding
        label_encoders = {}
        for col in df_model.select_dtypes(include="object").columns:
            le = LabelEncoder()
            df_model[col] = le.fit_transform(df_model[col])
            label_encoders[col] = le

        # Save encoders
        dump(label_encoders, ENCODERS_PATH)

        # Train-test split
        X = df_model.drop("injury_occurred", axis=1)
        y = df_model["injury_occurred"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train model
        clf = RandomForestClassifier(random_state=42, n_jobs=-1)
        clf.fit(X_train, y_train)

        # Save model
        dump(clf, MODEL_PATH)

        # Evaluate
        y_pred = clf.predict(X_test)
        print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
        print("\nClassification Report:\n", classification_report(y_test, y_pred))
        print("Model training completed successfully.")

    except Exception as e:
        print("Model training failed:", str(e))
        raise

if __name__ == "__main__":
    main()