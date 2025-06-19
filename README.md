# Flask SQL Command Executor

This project is a Flask-based REST API that securely executes a list of SQL commands against a Microsoft SQL Server (`pymssql`) in a thread-safe manner. Each command execution is logged, and a history of commands can be retrieved or cleared.

## Features

* ✅ Accepts a list of SQL commands via API
* 🧵 Runs each command asynchronously in a separate thread
* 🔐 Uses environment variables to configure DB access
* 📜 Logs execution details and errors
* 🧠 Stores a history of executed commands
* 🛠️ Includes endpoints to check service health and clear command history

---

## Environment Variables

Before running the application, ensure the following environment variables are set:

```bash
DB_SERVER=<your-sql-server-host>
DB_DATABASE=<your-database-name>
DB_USERNAME=<your-username>
DB_PASSWORD=<your-password>
FLASK_RUN_HOST=0.0.0.0        # Optional, default is 0.0.0.0
FLASK_RUN_PORT=5000           # Optional, default is 80
```

---

## Installation

### Requirements

* Python 3.8+
* `pymssql` (SQL Server client for Python)
* `Flask`

### Install Dependencies

```bash
pip install flask pymssql
```

---

## Running the Application

```bash
python app.py
```

The service will be available at `http://localhost:5000/` (or whichever port you configure).

---

## API Endpoints

### `POST /command`

Executes a list of SQL commands asynchronously.

**Request Body:**

```json
{
  "sql_commands": [
    "DELETE FROM users WHERE id = 123;",
    "UPDATE logs SET deleted = 1 WHERE user_id = 123;"
  ]
}
```

**Response:**

```json
{
  "status": "in_progress",
  "message": "Command started successfully"
}
```

### `GET /`

Health check + Command execution history.

**Response:**

```json
{
  "status": "healthy",
  "command_history": [
    {
      "command": "DELETE FROM users WHERE id = 123;",
      "duration": 0.04,
      "status": "success",
      "error": null,
      "timestamp": "2025-06-19T13:00:00"
    },
    ...
  ]
}
```

### `DELETE /clear`

Clears the stored command history.

**Response:**

```json
{
  "status": "success",
  "message": "Command history cleared"
}
```

---

## Logs

Command execution logs are stored in:

* `commands.log` (file)
* Console output

---

## Thread Safety

Command execution and history are protected by `threading.Lock()` to prevent race conditions.

---

## Security Notes

* Use only in trusted environments.
* Consider authentication and authorization for production.
* Commands are executed **as-is** — ensure validation/sanitization if exposed externally.

---

## License

MIT or your license of choice.

---
