from flask import Flask, jsonify, request
import os
import pymssql
import logging
from datetime import datetime
from threading import Thread, Lock
from typing import List, Dict, Union, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('commands.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    server: str
    database: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create database configuration from environment variables."""
        required_vars = {
            'DB_SERVER': os.getenv('DB_SERVER'),
            'DB_DATABASE': os.getenv('DB_DATABASE'),
            'DB_USERNAME': os.getenv('DB_USERNAME'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD')
        }
        
        missing_vars = [key for key, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        return cls(
            server=required_vars['DB_SERVER'],
            database=required_vars['DB_DATABASE'],
            username=required_vars['DB_USERNAME'],
            password=required_vars['DB_PASSWORD']
        )

@dataclass
class ExecutedCommand:
    command: str
    duration: float
    status: str
    error: Optional[str] = None
    timestamp: datetime = datetime.now()

class CommandManager:
    def __init__(self):
        self.executed_commands: List[ExecutedCommand] = []
        self.lock = Lock()
        self.db_config = DatabaseConfig.from_env()
        
    @contextmanager
    def database_connection(self):
        """Context manager for database connections."""
        connection = None
        try:
            connection = pymssql.connect(
                server=self.db_config.server,
                user=self.db_config.username,
                password=self.db_config.password,
                database=self.db_config.database
            )
            yield connection
        except pymssql.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def execute_single_command(self, connection, command: str) -> ExecutedCommand:
        """Execute a single SQL command and return its execution details."""
        command_start = time.time()
        cursor = connection.cursor()
        
        try:
            cursor.execute(command)
            connection.commit()  # Commit after each successful command
            duration = time.time() - command_start
            
            return ExecutedCommand(
                command=command.strip(),
                duration=duration,
                status="success"
            )
            
        except pymssql.Error as e:
            duration = time.time() - command_start
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg)
            
            return ExecutedCommand(
                command=command.strip(),
                duration=duration,
                status="error",
                error=error_msg
            )

    def execute_sql_commands(self, sql_commands: List[str]) -> Dict:
        """Execute a list of SQL commands and return execution details."""
        start_time = datetime.now()
        logger.info(f"Starting commands at {start_time}")
        
        success_count = 0
        error_count = 0

        try:
            with self.database_connection() as connection:
                for command in sql_commands:
                    if not command.strip():
                        continue
                    
                    result = self.execute_single_command(connection, command)
                    
                    with self.lock:
                        self.executed_commands.append(result)
                    
                    if result.status == "success":
                        success_count += 1
                        logger.info(f"Successfully executed command in {result.duration:.2f}s: {command[:100]}...")
                    else:
                        error_count += 1
                        logger.warning(f"Command failed but continuing with next command. Error: {result.error}")

        except pymssql.Error as e:
            logger.error(f"Fatal database error: {str(e)}")
            return {
                "status": "error",
                "message": f"Fatal database error: {str(e)}",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "success_count": success_count,
                "error_count": error_count
            }

        end_time = datetime.now()
        return {
            "status": "completed",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration": str(end_time - start_time),
            "success_count": success_count,
            "error_count": error_count,
            "executed_commands": [
                {
                    "command": cmd.command,
                    "duration": cmd.duration,
                    "status": cmd.status,
                    "error": cmd.error,
                    "timestamp": cmd.timestamp.isoformat()
                }
                for cmd in self.executed_commands
            ]
        }

    def clear_history(self):
        """Clear the execution history."""
        with self.lock:
            self.executed_commands.clear()

    def get_history(self) -> List[Dict]:
        """Get the execution history."""
        with self.lock:
            return [
                {
                    "command": cmd.command,
                    "duration": cmd.duration,
                    "status": cmd.status,
                    "error": cmd.error,
                    "timestamp": cmd.timestamp.isoformat()
                }
                for cmd in self.executed_commands
            ]

# Initialize Flask app and command manager
app = Flask(__name__)
command_manager = CommandManager()

@app.route('/command', methods=['POST'])
def command():
    """Endpoint to start a new command."""
    try:
        data = request.get_json()
        if not data or 'sql_commands' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'sql_commands' in request body"
            }), 400

        if not isinstance(data['sql_commands'], list):
            return jsonify({
                "status": "error",
                "message": "'sql_commands' must be a list"
            }), 400

        def run_command():
            try:
                result = command_manager.execute_sql_commands(data['sql_commands'])
                logger.info(
                    "Command completed. Successful: %d, Failed: %d", 
                    result.get('success_count', 0),
                    result.get('error_count', 0)
                )
            except Exception as e:
                logger.error("Command failed: %s", str(e), exc_info=True)

        command_thread = Thread(target=run_command)
        command_thread.start()

        return jsonify({
            "status": "in_progress",
            "message": "Command started successfully"
        }), 202

    except Exception as e:
        logger.error("Error processing command request", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/clear', methods=['DELETE'])
def clear_executed_commands():
    """Clear the command history."""
    command_manager.clear_history()
    return jsonify({
        "status": "success",
        "message": "Command history cleared"
    }), 200

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint that returns command history."""
    return jsonify({
        "status": "healthy",
        "command_history": command_manager.get_history()
    }), 200

if __name__ == "__main__":
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 80))
    app.run(host=host, port=port)
