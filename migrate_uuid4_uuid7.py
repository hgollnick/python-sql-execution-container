import os
import pymssql
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the SQL commands
sql_commands = """
EXEC dbo.MigrateUUID4ToUUID7 @TableName = 'ErrorCause', @UUID4ColumnName = 'erca_id';
EXEC dbo.MigrateUUID4ToUUID7 @TableName = 'ErrorProtocol', @UUID4ColumnName = 'executionId';
EXEC dbo.MigrateUUID4ToUUID7 @TableName = 'ErrorProtocolDetail', @UUID4ColumnName = 'executionId';
"""

# Database connection configuration
server =  os.getenv('your_server_name')  # Update with your server name
database =  os.getenv('your_database_name')  # Update with your database name
username =  os.getenv('your_username')  # Update with your username
password =  os.getenv('your_password')  # Update with your password

def execute_sql_commands():
    start_time = datetime.now()
    logging.info(f"Execution started at {start_time}.")

    try:
        # Establish a connection to the database
        connection = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database
        )
        
        # Create a cursor object
        cursor = connection.cursor()

        # Execute each SQL command
        for command in sql_commands.strip().split(';'):
            if command.strip():
                cursor.execute(command)

        # Commit the transactions
        connection.commit()

    except pymssql.Error as e:
        logging.error("Error while executing SQL commands:", exc_info=True)

    finally:
        # Close the connection
        if 'connection' in locals() and connection:
            connection.close()

        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"Execution ended at {end_time}.")
        logging.info(f"Total duration: {duration}.")

if __name__ == "__main__":
    execute_sql_commands()
