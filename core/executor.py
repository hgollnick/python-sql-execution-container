import time
import logging
from typing import List
from .db import DatabaseConnectionManager
from .models import ExecutedCommand

logger = logging.getLogger(__name__)

class SQLCommandExecutor:
    def __init__(self, db_manager: DatabaseConnectionManager):
        self.db_manager = db_manager

    def execute(self, sql_commands: List[str]) -> List[ExecutedCommand]:
        results = []
        with self.db_manager.connect() as connection:
            for command in sql_commands:
                if not command.strip():
                    continue
                start = time.time()
                cursor = connection.cursor()
                try:
                    cursor.execute(command)
                    connection.commit()
                    duration = time.time() - start
                    results.append(ExecutedCommand(
                        command=command.strip(),
                        duration=duration,
                        status="success"
                    ))
                    logger.info(f"Executed command in {duration:.2f}s: {command[:100]}...")
                except Exception as e:
                    duration = time.time() - start
                    error_msg = f"Error executing command: {str(e)}"
                    logger.error(error_msg)
                    results.append(ExecutedCommand(
                        command=command.strip(),
                        duration=duration,
                        status="error",
                        error=error_msg
                    ))
        return results
