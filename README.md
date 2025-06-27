# Flask SQL Command Executor

This project is a Flask-based REST API that securely executes a list of SQL commands against a database (PostgreSQL or Microsoft SQL Server) in a thread-safe manner. Each command execution is logged, and a history of commands can be retrieved or cleared. The app is database-agnostic and can be run easily with Docker Compose.

**This application is intended for trusted environments only, especially for debugging purposes.**

## Features

* Accepts a list of SQL commands via API.
* Runs each command asynchronously in a separate thread.
* Tracks running commands and shows their elapsed time.
* Uses environment variables to configure DB access.
* Logs execution details and errors.
* Stores a history of executed commands.
* Includes endpoints to check service health and clear command history.


---

## Environment Variables

Before running the application, ensure the following environment variables are set (see `docker-compose.yml` for examples):

```bash
DB_TYPE=postgres                # 'postgres' or 'mssql'
DB_SERVER=db                    # Database host (use 'db' for docker-compose)
DB_DATABASE=testdb              # Database name
DB_USERNAME=testuser            # Database user
DB_PASSWORD=testpass            # Database password
FLASK_RUN_HOST=0.0.0.0          # Optional, default is 0.0.0.0
FLASK_RUN_PORT=80                # Optional, default is 80
```

---

## Installation (Local)

### Requirements

* Python 3.8+
* `psycopg2-binary` (PostgreSQL client for Python)
* `pymssql` (SQL Server client for Python)
* `Flask`

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running with Docker Compose

The easiest way to run the app and a test Postgres database is with Docker Compose:

```bash
cd example
# Build and start the app and database
docker-compose up --build
```

- The API will be available at [http://localhost:8080/](http://localhost:8080/)
- The database will be seeded with test data available in ```example\init-db.sql```.

---

## API Endpoints

### Health Check
```bash
GET /
```
Returns the command history and currently running commands (with elapsed time).

### Execute SQL Command(s)
```bash
POST /command
Content-Type: application/json
{
  "sql_commands": ["SELECT * FROM users;"]
}
```
Returns immediately with status. Use `/` to check command history and running commands.

### Clear Command History
```bash
DELETE /clear
```
Clears all command history and running command tracking.

---

## Example SQL for Testing

The included Postgres database is initialized with:
- A `users` table and sample data
- Views and functions for slow queries (10s and 60s delays)

You can test slow queries with:
```bash
curl -X POST http://localhost:8080/command \
  -H "Content-Type: application/json" \
  -d '{"sql_commands": ["SELECT * FROM users_with_10s_delay;"]}'
```

Or test error handling with:
```bash
curl -X POST http://localhost:8080/command \
  -H "Content-Type: application/json" \
  -d '{"sql_commands": ["SELECT * FROM does_not_exist;"]}'
```

---

## Notes
- The app is database-agnostic: set `DB_TYPE=postgres` or `DB_TYPE=mssql` and provide the correct driver and connection info.
