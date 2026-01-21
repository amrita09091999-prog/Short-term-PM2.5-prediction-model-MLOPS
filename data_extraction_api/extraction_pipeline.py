from data_extraction_api.extraction_util_functions.weather_data_extraction import ExtractWeatherData
from data_extraction_api.extraction_util_functions.aqi_data_extraction import ExtractAQIData
import sys
from src.logger import logging
from src.exception import MyException

data_extraction_duration = 14
start_date = "2026-01-19"
# weather_extraction_obj = ExtractWeatherData(start_date,data_extraction_duration)
# weather_extraction_obj.extract_data()
aqi_extraction_obj = ExtractAQIData(start_date,data_extraction_duration)
aqi_extraction_obj.extract_data()
