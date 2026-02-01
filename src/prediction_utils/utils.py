import sys
from src.entity.config_entity import AQIPredictorConfig
from src.entity.s3_estimator import Proj1Estimator
from src.exception import MyException
from src.logger import logging
from pandas import DataFrame
import json
import boto3
import joblib
import numpy as np
import pandas as pd
from io import BytesIO
from src.constants import MODEL_FILE_NAME,MODEL_BUCKET_NAME



"""
receive today's weather data 
receive today's photochemical data - excluding pm 25
receive 14 day pm 25 starting from today 
input to prediction pipeline will be the above 3 response in json format 

apply transformations on the data and make it ready for the modeling
get the model from s3 
predict using the model 
return the prediction
"""

class AirQualityPredictionPipeline:
    def __init__(self, s3_bucket, model_key, weather_client, photo_client, pm25_client):
        self.weather_client = weather_client
        self.photo_client = photo_client
        self.pm25_client = pm25_client
        self.aqi_predictor_config = AQIPredictorConfig()
        self.proj1_estimator = Proj1Estimator(bucket_name=self.aqi_predictor_config.model_bucket_name,
                                model_path=self.aqi_predictor_config.model_file_path)
        

    def get_today_weather(self):
        """Fetch today's weather data (JSON)"""
        return self.weather_client.fetch_today_weather()

    def get_today_photochemical_data(self):
        """Fetch today's photochemical data excluding PM2.5 (JSON)"""
        return self.photo_client.fetch_today_photochemical()

    def get_pm25_forecast_14_days(self):
        """Fetch 14-day PM2.5 forecast starting today (JSON)"""
        return self.pm25_client.fetch_pm25_14_days()
    
    def transform_inputs(self, weather_json, photo_json, pm25_json):
        """
        Transform raw JSON responses into model-ready features
        """
        # Example transformation logic (customize to your feature schema)
        weather_df = pd.DataFrame([weather_json])
        photo_df = pd.DataFrame([photo_json])
        pm25_df = pd.DataFrame(pm25_json)

        weather_df = pd.merge(weather_df, photo_df, on= ['state','place','latitude','longitude'],how='inner')

        weather_df['date'] = pd.to_datetime(weather_df['date'])
        weather_df['week'] = weather_df['date'].dt.isocalendar().week
        weather_df['weekday'] = weather_df['date'].dt.weekday
        weather_df['month'] = weather_df['date'].dt.month

        pm25_df[f"pm2_5_mean_lag"] = (
                pm25_df
                .groupby(['state','place','latitude','longitude'])["pm2_5_mean"]
                .shift(7)
        )

        for window in [7,14]:
            pm25_df[f"pm25_rolling_mean_{window}"] = (
            pm25_df
            .groupby(['state','place','latitude','longitude'])["pm2_5_mean"]
            .rolling(window=window)
            .mean()
            .reset_index(level=[0,1,2,3], drop=True)
            )
        weather_df['temp_range'] = weather_df['temperature_2m_max'] - weather_df['temperature_2m_min']
        weather_df['app_temp_range'] = weather_df['apparent_temperature_max'] - weather_df['apparent_temperature_min']
        weather_df['photochemical_activity_index'] = weather_df['shortwave_radiation_sum']*((weather_df['temperature_2m_max']+weather_df['temperature_2m_min']/2))
        weather_df['radiation_rate'] = weather_df['shortwave_radiation_sum']/(weather_df['sunshine_duration']+0.001)
        weather_df['uv_index_temp'] = weather_df['apparent_temperature_max']*weather_df['uv_index_max']
        weather_df['ozone_temp_max'] = weather_df['ozone_mean']* weather_df['temperature_2m_max']
        weather_df['ozone_uv_mean'] = weather_df['ozone_mean']* weather_df['uv_index_mean']
        weather_df['ozone_sunshine'] = weather_df['ozone_max'] * weather_df['sunshine_duration']
        weather_df['dust_wind_speed'] = weather_df['dust_mean']*weather_df['wind_speed_10m_max']

        weather_df['pm2_5_mean_lag'] = pm25_df['pm2_5_mean_lag']
        weather_df['pm25_rolling_mean_7'] =pm25_df['pm25_rolling_mean_7']
        weather_df['pm25_rolling_mean_14'] =pm25_df['pm25_rolling_mean_14']

        return weather_df 
    
    def load_model_from_s3(self):
        """Download model from S3 and load it"""
        return self.proj1_estimator.load_model()
    
    def predict(self, model,features_df):
        predictions = model.predict(features_df)
        return predictions




    


         



    

