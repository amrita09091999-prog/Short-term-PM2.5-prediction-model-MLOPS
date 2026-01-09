import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from src.exception import MyException
from src.logger import logging
from src.constants import (
    DATABASE_NAME,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USERNAME,
    POSTGRES_PASSWORD,
)

class PostgresClient:
    """
    PostgresClient is responsible for establishing a connection
    to the PostgreSQL database using SQLAlchemy.

    Attributes
    ----------
    engine : Engine
        Shared SQLAlchemy engine instance.
    session : Session
        SQLAlchemy session object.
    """

    engine: Engine = None

    def __init__(self, database_name: str = DATABASE_NAME):
        try:
            if PostgresClient.engine is None:
                connection_url = (
                    f"postgresql+psycopg2://"
                    f"{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}"
                    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{database_name}"
                )

                PostgresClient.engine = create_engine(
                    connection_url,
                    pool_pre_ping=True,   # checks stale connections
                    pool_size=5,
                    max_overflow=10
                )

                logging.info("PostgreSQL engine created successfully.")

            self.engine = PostgresClient.engine
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            logging.info(f"Connected to PostgreSQL database: {database_name}")

        except Exception as e:
            raise MyException(e, sys)

    def get_session(self):
        """
        Returns a new SQLAlchemy session.
        """
        try:
            return self.SessionLocal()
        except Exception as e:
            raise MyException(e, sys)
