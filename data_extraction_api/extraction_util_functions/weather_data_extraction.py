import pandas as pd
import requests
import pickle
import time
import os
import datetime 
import sys
from src.exception import MyException
from src.logger import logging
from data_extraction_api.extraction_util_functions import weather_data_extractions_utils
from src.constants import COORDINATES_FILE_PATH,LAST_INDEX_FILE_PATH,WEATHER_TABLE_NAME
from src.data_access.project_raw_data import RawData

class ExtractWeatherData:
    def __init__(self,start_date,extraction_duration):
        self.coordinates = pd.read_csv(COORDINATES_FILE_PATH,sep= ',')
        self.start_date = start_date
        self.extraction_duration = extraction_duration
        os.makedirs(os.path.dirname(LAST_INDEX_FILE_PATH), exist_ok=True)
        self.my_data = RawData()
        self.engine = self.my_data.engine
        if self.my_data.check_table_existance():
            self.data = self.my_data.export_table_as_dataframe(WEATHER_TABLE_NAME)
            with open(LAST_INDEX_FILE_PATH ,'r') as f:
                self.index = int(f.read().strip())
        else:
            self.data = pd.DataFrame(columns = ['id','state','place','latitude','longitude','date','temperature_2m_max','temperature_2m_min','apparent_temperature_max','apparent_temperature_min','precipitation_sum','rain_sum','snowfall_sum','precipitation_hours','sunshine_duration','daylight_duration','wind_speed_10m_max','wind_gusts_10m_max','shortwave_radiation_sum','et0_fao_evapotranspiration'])
            self.index = 0

        self.weather_utils_obj =weather_data_extractions_utils.WeatherAPIExtractionUtils(data = self.data,data_extraction_duration = self.extraction_duration,start_date=self.start_date) 
    
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
                response = self.weather_utils_obj.fetch_historical_weather(latitude, longitude)

                if not response:
                    logging.info("Empty response, skipping")
                    start += 1
                    continue

                data, status = self.weather_utils_obj.append_daily_data(
                    response, coordinates, start, data
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
                self.weather_utils_obj.check_point(data, start,LAST_INDEX_FILE_PATH,self.engine)
                logging.info("After checkpoint save")
                start += 1
                time.sleep(0.2)

            except Exception as e:
                logging.error(e)
                time.sleep(10)
                logging.info(f"Retrying index {start}")  # retry same index

                    







