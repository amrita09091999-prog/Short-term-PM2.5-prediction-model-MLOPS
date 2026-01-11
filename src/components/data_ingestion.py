import os
import sys

from pandas import DataFrame
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact
from src.exception import MyException
from src.logger import logging
from src.data_access.project_raw_data import RawData

class DataIngestion:
    def __init__(self,data_ingestion_config:DataIngestionConfig=DataIngestionConfig()):
        """
        :param data_ingestion_config: configuration for data ingestion
        """
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise MyException(e,sys)
        

    def export_data_into_feature_store(self)->DataFrame:
        """
        Method Name :   export_data_into_feature_store
        Description :   This method exports data from postgres to csv file
        
        Output      :   data is returned as artifact of data ingestion components
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            logging.info(f"Exporting data from postgres")
            my_data = RawData()
            dataframe = my_data.export_table_as_dataframe(table_name=self.data_ingestion_config.dataset_name)
            logging.info(f"Shape of dataframe: {dataframe.shape}")
            feature_store_file_path  = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path,exist_ok=True)
            logging.info(f"Saving exported data into feature store file path: {feature_store_file_path}")
            dataframe.to_csv(feature_store_file_path,index=False,header=True)
            return dataframe

        except Exception as e:
            raise MyException(e,sys)
    
    def add_time_splits(self,df,train_weight,date_col="date"):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        if df[date_col].isna().any():
            raise ValueError("Date column contains invalid datetime values")

        df = df.sort_values(date_col)

        min_date = df[date_col].min()
        max_date = df[date_col].max()
        total_duration = max_date - min_date

        train_end = min_date + total_duration * train_weight
        df["split"] = "test"
        df.loc[df[date_col] <= train_end, "split"] = "train"
        
        return df
        #val_end = min_date + total_duration * 0.91
    
    def assign_splits(self,row, train_end):
        if row['date'] <= train_end:
            return 'train'
        else:
            return 'test'

    def split_data_as_train_test(self,dataframe: DataFrame) ->None:
        """
        Method Name :   split_data_as_train_test
        Description :   This method splits the dataframe into train set and test set based on split ratio 
        
        Output      :   Folder is created in s3 bucket
        On Failure  :   Write an exception log and then raise an exception
        """
        logging.info("Entered split_data_as_train_test method of Data_Ingestion class")

        try:
            #calculating train, val , test splits and then saving it as a dataframe
            dataframe= self.add_time_splits(dataframe,self.data_ingestion_config.train_weight)
            #dataframe['split'] = dataframe.apply(self.assign_splits(train_end = self.data_ingestion_config.train_weight), axis=1)
            logging.info("Performed train test split on the dataframe")
            logging.info(
                "Exited split_data_as_train_test method of Data_Ingestion class"
            )
            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path,exist_ok=True)
            
            logging.info(f"Exporting train and test file path.")
            train_data = dataframe[dataframe['split']=='train'].drop(columns = ['split'])
            test_data = dataframe[dataframe['split']=='test'].drop(columns = ['split'])
            train_data.to_csv(self.data_ingestion_config.training_file_path,index=False,header=True)
            test_data.to_csv(self.data_ingestion_config.testing_file_path,index=False,header=True)

            logging.info(f"Exported train, validation and test file path.")
        except Exception as e:
            raise MyException(e, sys) from e

    def initiate_data_ingestion(self) ->DataIngestionArtifact:
        """
        Method Name :   initiate_data_ingestion
        Description :   This method initiates the data ingestion components of training pipeline 
        
        Output      :   train set and test set are returned as the artifacts of data ingestion components
        On Failure  :   Write an exception log and then raise an exception
        """
        logging.info("Entered initiate_data_ingestion method of Data_Ingestion class")

        try:
            dataframe = self.export_data_into_feature_store()

            logging.info("Got the data from Postgres")

            self.split_data_as_train_test(dataframe)

            logging.info("Performed train,validation and test split on the dataset")

            logging.info(
                "Exited initiate_data_ingestion method of Data_Ingestion class"
            )

            data_ingestion_artifact = DataIngestionArtifact(trained_file_path=self.data_ingestion_config.training_file_path,
            test_file_path=self.data_ingestion_config.testing_file_path)
            
            logging.info(f"Data ingestion artifact: {data_ingestion_artifact}")
            return data_ingestion_artifact
        except Exception as e:
            raise MyException(e, sys) from e