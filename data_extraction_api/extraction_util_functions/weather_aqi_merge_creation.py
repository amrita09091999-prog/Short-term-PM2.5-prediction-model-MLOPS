import sys
from src.logger import logging
from src.exception import MyException
from src.data_access.project_raw_data import RawData
# first get the raw tables from sql_alchemy
# perform merge 
# perform data transformation
# validate transformation
# save it in sql engine as the final data