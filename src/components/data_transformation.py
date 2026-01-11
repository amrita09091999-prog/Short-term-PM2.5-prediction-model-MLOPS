import sys
import numpy as np
import pandas as pd
from imblearn.combine import SMOTEENN
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.compose import ColumnTransformer

from src.constants import TARGET_COLUMN, SCHEMA_FILE_PATH, CURRENT_YEAR
from src.entity.config_entity import DataTransformationConfig
from src.entity.artifact_entity import DataTransformationArtifact, DataIngestionArtifact, DataValidationArtifact
from src.exception import MyException
from src.logger import logging
from src.utils.main_utils import save_object, save_numpy_array_data, read_yaml_file


class DataTransformation:
    def __init__(self, data_ingestion_artifact: DataIngestionArtifact,
                 data_transformation_config: DataTransformationConfig,
                 data_validation_artifact: DataValidationArtifact):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_transformation_config = data_transformation_config
            self.data_validation_artifact = data_validation_artifact
            self._schema_config = read_yaml_file(file_path=SCHEMA_FILE_PATH)
        except Exception as e:
            raise MyException(e, sys)

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise MyException(e, sys)
    
    def _create_temporal_features(self, data):
        """Create month ,week, weekday columns using date"""
        logging.info("Creating temporal features")
        data['date'] = pd.to_datetime(data['date'])
        data['week'] = data['date'].dt.isocalendar().week
        data['weekday'] = data['date'].dt.weekday
        data['month'] = data['date'].dt.month
        return data

    def _create_target_lag_columns(self, data):
        """Creating 7 day shifted PM_25 information and rolling window of 7 and 14 days."""
        logging.info("Creating shifted and rolling features using target variable")
        data[f"pm2_5_mean_lag"] = (
                data
                .groupby(['state','place','latitude','longitude'])["pm2_5_mean"]
                .shift(7)
        )
        for window in [7,14]:
            data[f"pm25_rolling_mean_{window}"] = (
            data
            .groupby(['state','place','latitude','longitude'])["pm2_5_mean"]
            .rolling(window=window)
            .mean()
            .reset_index(level=[0,1,2,3], drop=True)
            )
        data = data.dropna()
        return data

    def _create_interaction_features(self, data):
        """Creating interaction features using existing model fetures"""
        logging.info("Creating interaction features using existing model fetures")
        data['temp_range'] = data['temperature_2m_max'] - data['temperature_2m_min']
        data['app_temp_range'] = data['apparent_temperature_max'] - data['apparent_temperature_min']
        data['photochemical_activity_index'] = data['shortwave_radiation_sum']*((data['temperature_2m_max']+data['temperature_2m_min']/2))
        data['radiation_rate'] = data['shortwave_radiation_sum']/(data['sunshine_duration']+0.001)
        data['uv_index_temp'] = data['apparent_temperature_max']*data['uv_index_max']
        data['ozone_temp_max'] = data['ozone_mean']* data['temperature_2m_max']
        data['ozone_uv_mean'] = data['ozone_mean']* data['uv_index_mean']
        data['ozone_sunshine'] = data['ozone_max'] * data['sunshine_duration']
        data['dust_wind_speed'] = data['dust_mean']*data['wind_speed_10m_max']
        return data

    def _create_target_column(self, data,target):
        """Create target column - next day's pm2_5 level."""
        logging.info("Create target column - next day's pm2_5 level.")
        data = data.sort_values(['state','place','latitude','longitude',"date"]).reset_index(drop=True)
        data[target] = (
        data.groupby(['state','place','latitude','longitude'])["pm2_5_mean"]
        .shift(-1)
        )
        data= data.dropna(subset=[target])
        return data
    
    def _drop_redundant_columns(self, data):
        """Drop redundant columns."""
        logging.info("Dropping redundant columns.")

        drop_cols = self._schema_config.get("drop_columns", [])

        # Ensure it's always a list
        if isinstance(drop_cols, str):
            drop_cols = [drop_cols]

        # Drop only columns that actually exist
        cols_to_drop = [col for col in drop_cols if col in data.columns]

        if cols_to_drop:
            data = data.drop(columns=cols_to_drop)

        return data

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        """
        Initiates the data transformation component for the pipeline.
        """
        try:
            logging.info("Data Transformation Started !!!")
            if not self.data_validation_artifact.validation_status:
                raise Exception(self.data_validation_artifact.message)

            # Load train and test data
            train_df = self.read_data(file_path=self.data_ingestion_artifact.trained_file_path)
            test_df = self.read_data(file_path=self.data_ingestion_artifact.test_file_path)
            logging.info("Train-Test data loaded")

            # Apply custom transformations in specified sequence
            train_data_with_target_df = self._create_target_column(train_df,TARGET_COLUMN)
            train_data_with_target_df = self._create_temporal_features(train_data_with_target_df)
            train_data_with_target_df = self._create_target_lag_columns(train_data_with_target_df)
            train_data_with_target_df = self._create_interaction_features(train_data_with_target_df)
            train_data_with_target_df = self._drop_redundant_columns(train_data_with_target_df)

            test_data_with_target_df = self._create_target_column(test_df,TARGET_COLUMN)
            test_data_with_target_df = self._create_temporal_features(test_data_with_target_df)
            test_data_with_target_df = self._create_target_lag_columns(test_data_with_target_df)
            test_data_with_target_df = self._create_interaction_features(test_data_with_target_df)
            test_data_with_target_df = self._drop_redundant_columns(test_data_with_target_df)
            logging.info("Custom transformations applied to train and test data")

            input_feature_train_df = train_data_with_target_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_train_df = train_data_with_target_df[TARGET_COLUMN]

            input_feature_test_df = test_data_with_target_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_test_df = test_data_with_target_df[TARGET_COLUMN]
            logging.info("Input and Target cols defined for both train and test df.")

            train_arr = np.c_[np.array(input_feature_train_df), np.array(target_feature_train_df)]
            test_arr = np.c_[np.array(input_feature_test_df), np.array(target_feature_test_df)]
            print(f"Train dataset size - {train_arr.shape}")
            print(f"Test dataset size - {test_arr.shape}")
            logging.info("feature-target concatenation done for train-test df.")

            save_numpy_array_data(self.data_transformation_config.transformed_train_file_path, array=train_arr)
            save_numpy_array_data(self.data_transformation_config.transformed_test_file_path, array=test_arr)
            logging.info("Saving transformation object and transformed files.")

            logging.info("Data transformation completed successfully")
            return DataTransformationArtifact(
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path
            )

        except Exception as e:
            raise MyException(e, sys) from e