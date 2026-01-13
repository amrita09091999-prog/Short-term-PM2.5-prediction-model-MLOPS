import os
from datetime import date

DATASET_NAME = "historical_weather_aqi_table"
POSTGRES_USERNAME = "postgres"
POSTGRES_PASSWORD = "1234"
POSTGRES_PORT = "5432"
DATABASE_NAME = "postgres"
POSTGRES_HOST = "localhost"
POSTGRES_SCHEMA = "schema"

POSTGRES_CONNECTION_URL = (
    f"postgresql+psycopg2://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"
)

PIPELINE_NAME: str = ""
ARTIFACT_DIR: str = "artifact"

MODEL_FILE_NAME = "model.pkl"

TARGET_COLUMN = "Target"
CURRENT_YEAR = date.today().year
PREPROCSSING_OBJECT_FILE_NAME = "preprocessing.pkl"

FILE_NAME: str = "data.csv"
TRAIN_FILE_NAME: str = "train.csv"
VAL_FILE_NAME: str = "val.csv"
TEST_FILE_NAME: str = "test.csv"
SCHEMA_FILE_PATH = os.path.join("config", "schema.yaml")


AWS_ACCESS_KEY_ID_ENV_KEY = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY_ENV_KEY = "AWS_SECRET_ACCESS_KEY"
REGION_NAME = "us-east-1"


"""
Data Ingestion related constant start with DATA_INGESTION VAR NAME
"""
DATA_INGESTION_DIR_NAME: str = "data_ingestion"
DATA_INGESTION_FEATURE_STORE_DIR: str = "feature_store"
DATA_INGESTION_INGESTED_DIR: str = "ingested"
TRAIN_WEIGHT: float = 0.9
VAL_WEIGHT: float = 0.91
TRAIN_TEST_SPLIT: float = 0.1

"""
Data Validation realted contant start with DATA_VALIDATION VAR NAME
"""
DATA_VALIDATION_DIR_NAME: str = "data_validation"
DATA_VALIDATION_REPORT_FILE_NAME: str = "report.yaml"

"""
Data Transformation ralated constant start with DATA_TRANSFORMATION VAR NAME
"""
DATA_TRANSFORMATION_DIR_NAME: str = "data_transformation"
DATA_TRANSFORMATION_TRANSFORMED_DATA_DIR: str = "transformed"
DATA_TRANSFORMATION_TRANSFORMED_OBJECT_DIR: str = "transformed_object"

"""
MODEL TRAINER related constant start with MODEL_TRAINER var name
"""
MODEL_TRAINER_DIR_NAME: str = "model_trainer"
MODEL_TRAINER_TRAINED_MODEL_DIR: str = "trained_model"
MODEL_TRAINER_TRAINED_MODEL_NAME: str = "model.pkl"
MODEL_TRAINER_MODEL_CONFIG_FILE_PATH: str = os.path.join("config", "model.yaml")
PARAMETERS_FILE_PATH: str = os.path.join("config", "parameters.yaml")
DAGSHUB_REPO_OWNER: str = "amrita09091999-prog"
DAGSHUB_REPO_NAME: str = "Short-term-PM2.5-prediction-model-MLOPS"
MLFLOW_EXPERIMENT_NAME: str = "PM2.5-Model-Training-2"
BASE_ADJUSTED_R2_SCORE: float = 0.8

"""
MODEL Evaluation related constants
"""
MODEL_EVALUATION_CHANGED_THRESHOLD_SCORE: float = 0.02
MODEL_BUCKET_NAME = "my-model-mlopsproj"
MODEL_PUSHER_S3_KEY = "model-registry"


APP_HOST = "0.0.0.0"
APP_PORT = 5000