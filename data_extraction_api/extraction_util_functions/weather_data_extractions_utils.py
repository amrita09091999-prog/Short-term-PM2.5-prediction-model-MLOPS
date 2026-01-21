import pandas as pd
import requests
import pickle
import time
import os
from datetime import datetime, timedelta
from src.constants import (
    COORDINATES_FILE_PATH,
    LAST_INDEX_FILE_PATH,
    WEATHER_TABLE_NAME,
    DATABASE_NAME,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USERNAME,
    POSTGRES_PASSWORD,
    WEATHER_API_URL)
import sys
from src.exception import MyException
from src.logger import logging

class WeatherAPIExtractionUtils:
    def __init__(self,data,data_extraction_duration,start_date):
        try:
            self.data_extraction_duration = data_extraction_duration
            self.start_date = start_date
            self.data = data

            # 1. Parse string → datetime
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

            # 2. Subtract duration
            end_dt = start_dt - timedelta(days=data_extraction_duration)

            # 3. Store end_date (string format)
            self.end_date = end_dt.strftime("%Y-%m-%d")
        except Exception as e:
            raise MyException(e, sys)
     
    def fetch_historical_weather(self,latitude,longitude):
        logging.info("fetching from API")
        url = WEATHER_API_URL
        params = {
            "latitude":latitude,
            "longitude":longitude,
            "start_date":self.end_date,
            'end_date':self.start_date,
            'daily':['temperature_2m_max','temperature_2m_min','apparent_temperature_max','apparent_temperature_min','precipitation_sum','rain_sum','snowfall_sum','precipitation_hours','sunshine_duration','daylight_duration','wind_speed_10m_max','wind_gusts_10m_max','shortwave_radiation_sum','et0_fao_evapotranspiration'],
            'timezone':'auto'
        }

        response = requests.get(url = url, params = params).json()
        if not response:
            return None
        else:
            return response
    
    def create_daily_from_hourly_data(self,response):
        data = pd.DataFrame(response['hourly'])
        data['time'] = pd.to_datetime(data['time']).dt.date
        daily_df = (
        data
        .groupby('time')
        .agg(['mean','std', 'max', 'min'])
        .reset_index()
        )
        daily_df.fillna(0,inplace=True)
        daily_df.columns = [f"{col[0]}_{col[1]}" for col in daily_df.columns]
        daily_df.rename(columns = {'time_':'date'},inplace=True)
        return daily_df

    def append_daily_data(self,response, coordinates_filetered, i):
        data = pd.DataFrame(response['daily'])
        if data.empty:
            return None, "empty"

        data['id'] = coordinates_filetered.loc[i, 'id']
        data['state'] = coordinates_filetered.loc[i, 'state']
        data['place'] = coordinates_filetered.loc[i, 'place']
        data['latitude'] = coordinates_filetered.loc[i, 'latitude']
        data['longitude'] = coordinates_filetered.loc[i, 'longitude']

        data = data[['id','state','place','latitude','longitude']+list(data.columns[:-5])]

        data = data.drop_duplicates(subset=["id", "place", "date"])

        return data, "success"

    def check_point(self,historical_weather_data, last_index,file_path,engine):
        historical_weather_data = historical_weather_data.drop_duplicates()
        print('\nproceeding to save in the database')
        historical_weather_data.to_sql(
        name=WEATHER_TABLE_NAME,
        con=engine,
        if_exists="append",
        index=False
    )
        with open(file_path, "w") as f:
            f.write(str(last_index))


