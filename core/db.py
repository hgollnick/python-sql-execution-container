import os
from contextlib import contextmanager
from .config import DatabaseConfig
import logging

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_type = os.getenv('DB_TYPE', 'mssql').lower()  # 'postgres' or 'mssql'
        if self.db_type == 'postgres':
            import psycopg2
            self.driver = psycopg2
        elif self.db_type == 'mssql':
            import pymssql
            self.driver = pymssql
        else:
            raise ValueError(f"Unsupported DB_TYPE: {self.db_type}")

    @contextmanager
    def connect(self):
        connection = None
        try:
            if self.db_type == 'postgres':
                connection = self.driver.connect(
                    host=self.config.server,
                    user=self.config.username,
                    password=self.config.password,
                    dbname=self.config.database
                )
            elif self.db_type == 'mssql':
                connection = self.driver.connect(
                    server=self.config.server,
                    user=self.config.username,
                    password=self.config.password,
                    database=self.config.database
                )
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
