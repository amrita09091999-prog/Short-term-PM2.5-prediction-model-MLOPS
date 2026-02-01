from src.prediction_utils import utils
from src.constants import MODEL_BUCKET_NAME, MODEL_FILE_NAME,WEATHER_API_URL,AQI_API_URL,COORIDNATES_API_URL 
from src.exception import MyException
from src.logger import logging
import requests 

class Geoencoding:
    def __init__(self,city):
        logging.info(f"getting coordinates for - {city}")
        try:
            url = COORIDNATES_API_URL 
            params = {
                'name':city,
                'count':1,
                'countryCode':'IN'
            }
            response = requests.get(url = url,params = params).json()
            return response['latitude'], response['longitude']
        except Exception as e:
            raise MyException(e, sys)

class WeatherClient:
    def __init__(self,date,latitude, longitude):
        logging.info(f"fetching today's weather for {latitude}, {longitude}")
        try:
            url = WEATHER_API_URL
            params = {
                'latitude' = latitude,
                "longitude":longitude,
                'start_date':date,
                'end_date':date,
                'daily':['temperature_2m_max','temperature_2m_min','apparent_temperature_max','apparent_temperature_min','precipitation_sum','rain_sum','snowfall_sum','precipitation_hours','sunshine_duration','daylight_duration','wind_speed_10m_max','wind_gusts_10m_max','shortwave_radiation_sum','et0_fao_evapotranspiration'],
                'timezone':'auto'
            }
            response = requests.get(url = url,params = params).json()
            return response['daily']
        except Exception as e:
            raise MyException(e, sys)

class AQIClient:
    logging.info(f"fetching today's photochemical data - for {latitude}, {longitude}")
    def __init__(self,date,latitude, longitude):
        try:
            url = AQI_API_URL
            params = {
                'latitude' = latitude,
                "longitude":longitude,
                'start_date':date,
                'end_date':date,
                'hourly':["pm10",'carbon_monoxide','nitrogen_dioxide','sulphur_dioxide','ozone','carbon_dioxide','ammonia','aerosol_optical_depth','methane','dust','uv_index','uv_index_clear_sky','alder_pollen'],
                'timezone':'auto'
            }
            response = requests.get(url = url,params = params).json()
            return response['hourly']
        except Exception as e:
            raise MyException(e, sys)

class PM25Client:
    logging.info(f"fetching today's photochemical data - for {latitude}, {longitude}")
    def __init__(self,date,latitude, longitude):
        try:
            url = AQI_API_URL
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = start_dt - timedelta(days=14)
            start_date = end_dt.strftime("%Y-%m-%d")
            params = {
                'latitude' = latitude,
                "longitude":longitude,
                'start_date':start_date,
                'end_date':date,
                'hourly':['pm2_5'],
                'timezone':'auto'
            }
            response = requests.get(url = url,params = params).json()
            return response['hourly']
        
        except Exception as e:
            raise MyException(e, sys)

class PredictionModule:
    def __init__(self,state,city,date):
        self.state = state
        self.city = city
        self.date = date

    def preprocess_data(self):
        latitude, longitude = Geoencoding(self.city)
        weather_response= WeatherClient(self.date,latitude,longitude)
        logging.info("Preprocessing weather data")
        try:
            weather_data = pd.DataFrame(weather_response)
            if weather_data.empty:
                raise Exception("Weather API returned empty response")
            weather_data['state'] = self.state
            weather_data['city'] = self.city
            weather_data['latitude'] = latitude
            weather_data['longitude'] = longitude
            weather_data = weather_data[['state','place','latitude','longitude']+list(weather_data.columns[:-4])]
        except Exception as e:
            raise MyException(e, sys)

        logging.info("Preprocessing aqi data")
        try:
            aqi_response = AQIClient(self.date,latitude, longitude)
            photochemical_data = pd.DataFrame(aqi_response)
            photochemical_data['time'] = pd.to_datetime(photochemical_data['time']).dt.date
            photochemical_data = (
            photochemical_data
            .groupby('time')
            .agg(['mean','std', 'max', 'min'])
            .reset_index()
            )
            photochemical_data.fillna(0,inplace=True)
            photochemical_data.columns = [f"{col[0]}_{col[1]}" for col in photochemical_data.columns]
            photochemical_data.rename(columns = {'time_':'date'},inplace=True)
            photochemical_data['state'] = self.state
            photochemical_data['city'] = self.city
            photochemical_data['latitude'] = latitude
            photochemical_data['longitude'] = longitude
            photochemical_data = photochemical_data[['state','place','latitude','longitude']+list(photochemical_data.columns[:-4])]
        except Exception as e:
            raise MyException(e, sys)
        
        logging.info("Preprocessing last 14 day aqi data data")
        try:
            aqi_response = PM25Client(self.date,latitude, longitude)
            aqi_data = pd.DataFrame(aqi_response)
            aqi_data['time'] = pd.to_datetime(aqi_data['time']).dt.date
            aqi_data = (
            aqi_data
            .groupby('time')
            .agg(['mean','std', 'max', 'min'])
            .reset_index()
            )
            aqi_data.fillna(0,inplace=True)
            aqi_data.columns = [f"{col[0]}_{col[1]}" for col in aqi_data.columns]
            aqi_data.rename(columns = {'time_':'date'},inplace=True)
            aqi_data['state'] = self.state
            aqi_data['city'] = self.city
            aqi_data['latitude'] = latitude
            aqi_data['longitude'] = longitude
            aqi_data = aqi_data[['state','place','latitude','longitude']+list(aqi_data.columns[:-4])]

        except Exception as e:
            raise MyException(e, sys)
    
    

        







        






        


