import pandas as pd
import requests
import pickle
import time
import os
import datetime 
import sys
from src.exception import MyException
from src.logger import logging
from data_extraction_api.extraction_util_functions import aqi_data_extraction_utils
from src.constants import COORDINATES_FILE_PATH,LAST_INDEX_FILE_PATH,AQI_TABLE_NAME
from src.data_access.project_raw_data import RawData

class ExtractAQIData:
    def __init__(self,start_date,extraction_duration):
        self.coordinates = pd.read_csv(COORDINATES_FILE_PATH,sep= ',')
        self.start_date = start_date
        self.extraction_duration = extraction_duration
        os.makedirs(os.path.dirname(LAST_INDEX_FILE_PATH), exist_ok=True)
        self.my_data = RawData()
        self.engine = self.my_data.engine
        if self.my_data.check_table_existance(table_name =AQI_TABLE_NAME):
            self.data = self.my_data.export_table_as_dataframe(AQI_TABLE_NAME)
            with open(LAST_INDEX_FILE_PATH ,'r') as f:
                self.index = int(f.read().strip())
        else:
            self.data = pd.DataFrame(columns = ['id','state','place','latitude','longitude','date',"pm10",'pm2_5','carbon_monoxide','nitrogen_dioxide','sulphur_dioxide','ozone','carbon_dioxide','ammonia','aerosol_optical_depth','methane','dust','uv_index','uv_index_clear_sky','alder_pollen'])
            self.index = 0

        self.aqi_utils_obj =aqi_data_extraction_utils.AQIAPIExtractionUtils(data = self.data,data_extraction_duration = self.extraction_duration,start_date=self.start_date) 
    
    def extract_data(self):
        start = self.index+1
        data = self.data
        coordinates = self.coordinates

        while start < len(coordinates):
            try:
                logging.info(
                    f"Extracting {coordinates.loc[start, 'state']}, "
                    f"{coordinates.loc[start, 'place']}"
                )

                latitude = coordinates.loc[start, 'latitude']
                longitude = coordinates.loc[start, 'longitude']

                logging.info("fetching from API")
                response = self.aqi_utils_obj.fetch_historical_aqi(latitude, longitude)

                if not response:
                    logging.info("Empty response, skipping")
                    start += 1
                    continue

                daily_df = self.aqi_utils_obj.create_daily_from_hourly_data(response)

                data, status = self.aqi_utils_obj.append_daily_data(
                    daily_df, coordinates, start
                )
                if status != "success":
                    logging.info(status)
                    datetime.datetime.now()
                    time.sleep(60)
                    datetime.datetime.now()
                    logging.info(f"Retrying index {start}")
                    continue  # retry SAME index

                # ✅ success path
                data = data.drop_duplicates()
                logging.info("Before checkpoint save")
                self.aqi_utils_obj.check_point(data, start,LAST_INDEX_FILE_PATH,self.engine)
                logging.info("After checkpoint save")
                start += 1
                time.sleep(0.2)

            except Exception as e:
                logging.error(e)
                time.sleep(10)
                logging.info(f"Retrying index {start}")  # retry same index

                    







