import sys
import pandas as pd
import numpy as np

from src.configuration.postgres_connection import PostgresClient
from src.constants import DATABASE_NAME,WEATHER_TABLE_NAME,AQI_TABLE_NAME
from src.exception import MyException

class RawData:
    """
    Handles data extraction from PostgreSQL and returns pandas DataFrames.
    """

    def __init__(self) -> None:
        try:
            self.pg_client = PostgresClient(database_name=DATABASE_NAME)
            self.engine = self.pg_client.engine
        except Exception as e:
            raise MyException(e, sys)
    def  check_table_existance(self,table_name):
        try:
            if self.pg_client.inspector.has_table(table_name):
                return True
            else:
                return False
        except Exception as e:
            raise MyException(e, sys)

    def export_table_as_dataframe(self, table_name: str) -> pd.DataFrame:
        """
        Exports a PostgreSQL table as a pandas DataFrame.

        Parameters
        ----------
        table_name : str
            Name of the table to export.

        Returns
        -------
        pd.DataFrame
        """
        try:
            query = f"SELECT * FROM {table_name}"
            print("Fetching data from PostgreSQL")

            df = pd.read_sql(query, self.pg_client.engine)

            print(f"Data fetched with rows: {len(df)}")

            df.replace({"na": np.nan}, inplace=True)
            return df

        except Exception as e:
            raise MyException(e, sys)
