import os
from dataclasses import dataclass

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
