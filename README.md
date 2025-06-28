# Flask SQL Command Executor

A Flask-based REST API to securely execute SQL commands (PostgreSQL or SQL Server) in a thread-safe, auditable way. Supports async and sync execution, job tracking, and history. Easily run locally or with Docker Compose.

**Intended for trusted environments only (e.g., debugging, internal tools).**

---

## Quick Start

### With Docker Compose

```bash
cd example
# Build and start the app and database
docker-compose up --build
```
- API: [http://localhost:8080/](http://localhost:8080/)
- Swagger UI: [http://localhost:8080/apidocs/](http://localhost:8080/apidocs/)
- Test database auto-seeded from `example/init-db.sql`.

### Local (Python)

Requirements:
- Python 3.8+
- `psycopg2-binary` (PostgreSQL)
- `pymssql` (SQL Server)
- `Flask`, `flasgger`

```bash
pip install -r requirements.txt
python app.py
```

---

## Environment Variables

Set these (see `example/docker-compose.yml`):

```bash
DB_TYPE=postgres                # 'postgres' or 'mssql'
DB_SERVER=db                    # Database host (use 'db' for docker-compose)
DB_DATABASE=testdb              # Database name
DB_USERNAME=testuser            # Database user
DB_PASSWORD=testpass            # Database password
FLASK_RUN_HOST=0.0.0.0          # Optional, default is 0.0.0.0
FLASK_RUN_PORT=80               # Optional, default is 80
```

---

## API Endpoints

All endpoints return JSON. See live docs at `/apidocs/` (Swagger UI).

### Health & History
- `GET /` — Command history and running commands (paginated)
  - Query: `page`, `page_size`

### Execute SQL (Async)
- `POST /command`
  - Body: `{ "sql_commands": ["SELECT * FROM users;"] }`
  - Returns: `{ status, job_id, message }` (use `/job/<job_id>` to check result)

### Execute SQL (Sync)
- `POST /command_sync`
  - Body: `{ "sql_commands": ["SELECT * FROM users;"] }`
  - Returns: `{ status, job_id, results }` (waits for completion)

### Job Status
- `GET /job/<job_id>`
  - Returns: `{ status, result }` or error

### Clear History
- `DELETE /clear`
  - Clears all command history and running command tracking

---

## Example SQL for Testing

The included Postgres DB is initialized with:
- A `users` table and sample data
- Views/functions for slow queries (10s/60s delays)

Test slow query:
```bash
curl -X POST http://localhost:8080/command \
  -H "Content-Type: application/json" \
  -d '{"sql_commands": ["SELECT * FROM users_with_10s_delay;"]}'
```

Test error handling:
```bash
curl -X POST http://localhost:8080/command \
  -H "Content-Type: application/json" \
  -d '{"sql_commands": ["SELECT * FROM does_not_exist;"]}'
```

---

## Project Structure

```
app.py                # Main Flask app
core/
  config.py           # DB config from env
  db.py               # DB connection manager
  executor.py         # SQL execution logic
  history.py          # Command history & running tracking
  models.py           # Data models
example/
  docker-compose.yml  # Example stack
  init-db.sql         # DB init script
Dockerfile            # Container build
requirements.txt      # Python deps
```

---

## Security & Notes
- **Never expose to untrusted users.**
- Supports PostgreSQL and SQL Server (set `DB_TYPE`).
- All SQL is executed as provided—no sanitization.
- Logs to `commands.log` and stdout.
- API docs: `/apidocs/` (Swagger UI via Flasgger)

---

## License
MIT License. See `LICENSE.txt`.

## Contributions
PRs and issues welcome!
