import os
import logging
from flask import Flask, jsonify, request
from threading import Thread, Lock
import uuid
from core.config import DatabaseConfig
from core.db import DatabaseConnectionManager
from core.executor import SQLCommandExecutor
from core.history import CommandHistoryManager
from flasgger import Swagger

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('commands.log')
    ]
)
logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        self.app = Flask(__name__)
        self.swagger = Swagger(self.app)
        self.jobs = {}  # job_id -> {status, result}
        self.jobs_lock = Lock()
        try:
            self.db_config = DatabaseConfig.from_env()
            self.db_manager = DatabaseConnectionManager(self.db_config)
            self.command_executor = SQLCommandExecutor(self.db_manager)
            self.history_manager = CommandHistoryManager()
        except Exception as e:
            logger.critical(f"Failed to initialize application: {e}")
            raise
        self._register_routes()

    def _register_routes(self):
        @self.app.route('/command', methods=['POST'])
        def command():
            """
            Submit SQL commands for asynchronous execution
            ---
            tags:
              - Commands
            parameters:
              - in: body
                name: body
                required: true
                schema:
                  type: object
                  properties:
                    sql_commands:
                      type: array
                      items:
                        type: string
            responses:
              202:
                description: Command started successfully
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                    job_id:
                      type: string
                    message:
                      type: string
              400:
                description: Bad request
              500:
                description: Internal server error
            """
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

                job_id = str(uuid.uuid4())
                with self.jobs_lock:
                    self.jobs[job_id] = {"status": "in_progress", "result": None}

                running_entries = [self.history_manager.add_running(cmd) for cmd in data['sql_commands']]

                def run_commands():
                    try:
                        results = self.command_executor.execute(data['sql_commands'])
                        self.history_manager.add(results)
                        for cmd in data['sql_commands']:
                            self.history_manager.finish_running(cmd)
                        success_count = sum(1 for r in results if r.status == "success")
                        error_count = sum(1 for r in results if r.status == "error")
                        logger.info(f"Command completed. Successful: {success_count}, Failed: {error_count}")
                        with self.jobs_lock:
                            self.jobs[job_id] = {"status": "completed", "result": [r.__dict__ for r in results]}
                    except Exception as e:
                        logger.error(f"Command failed: {str(e)}", exc_info=True)
                        for cmd in data['sql_commands']:
                            self.history_manager.finish_running(cmd)
                        with self.jobs_lock:
                            self.jobs[job_id] = {"status": "error", "result": str(e)}

                Thread(target=run_commands).start()
                return jsonify({
                    "status": "in_progress",
                    "job_id": job_id,
                    "message": "Command started successfully"
                }), 202
            except Exception as e:
                logger.error("Error processing command request", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": f"Internal server error: {str(e)}"
                }), 500

        @self.app.route('/command_sync', methods=['POST'])
        def command_sync():
            """
            Submit SQL commands for synchronous execution
            ---
            tags:
              - Commands
            parameters:
              - in: body
                name: body
                required: true
                schema:
                  type: object
                  properties:
                    sql_commands:
                      type: array
                      items:
                        type: string
            responses:
              200:
                description: Command executed successfully
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                    job_id:
                      type: string
                    results:
                      type: array
                      items:
                        type: object
              400:
                description: Bad request
              500:
                description: Internal server error
            """
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

                job_id = str(uuid.uuid4())
                results = self.command_executor.execute_with_results(data['sql_commands'])
                with self.jobs_lock:
                    self.jobs[job_id] = {"status": "completed", "result": results}
                return jsonify({
                    "status": "completed",
                    "job_id": job_id,
                    "results": results
                }), 200
            except Exception as e:
                logger.error("Error processing command_sync request", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": f"Internal server error: {str(e)}"
                }), 500

        @self.app.route('/job/<job_id>', methods=['GET'])
        def get_job_status(job_id):
            """
            Get the status and result of a submitted job
            ---
            tags:
              - Jobs
            parameters:
              - in: path
                name: job_id
                type: string
                required: true
                description: The job ID
            responses:
              200:
                description: Job status and result
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                    result:
                      type: object
              404:
                description: Job not found
            """
            with self.jobs_lock:
                job = self.jobs.get(job_id)
            if not job:
                return jsonify({
                    "status": "error",
                    "message": f"Job ID {job_id} not found"
                }), 404
            # If job failed, include error details in response
            if job["status"] == "error":
                return jsonify({
                    "status": "error",
                    "error": job["result"]
                }), 200
            return jsonify({
                "status": job["status"],
                "result": job["result"]
            }), 200

        @self.app.route('/clear', methods=['DELETE'])
        def clear_executed_commands():
            """
            Clear the command execution history
            ---
            tags:
              - History
            responses:
              200:
                description: Command history cleared
                schema:
                  type: object
                  properties:
                    status:
                      type: string
                    message:
                      type: string
            """
            self.history_manager.clear()
            return jsonify({
                "status": "success",
                "message": "Command history cleared"
            }), 200

        @self.app.route('/', methods=['GET'])
        def health_check():
            """
            Get command history and running commands (with pagination)
            ---
            tags:
              - History
            parameters:
              - in: query
                name: page
                type: integer
                required: false
                default: 1
              - in: query
                name: page_size
                type: integer
                required: false
                default: 20
            responses:
              200:
                description: Command history and running commands
                schema:
                  type: object
                  properties:
                    command_history:
                      type: array
                      items:
                        type: object
                    running_commands:
                      type: array
                      items:
                        type: string
                    pagination:
                      type: object
                      properties:
                        page:
                          type: integer
                        page_size:
                          type: integer
                        total:
                          type: integer
                        total_pages:
                          type: integer
              400:
                description: Invalid pagination parameters
            """
            try:
                page = int(request.args.get('page', 1))
                page_size = int(request.args.get('page_size', 20))
                if page < 1 or page_size < 1:
                    raise ValueError
            except Exception:
                return jsonify({
                    "status": "error",
                    "message": "Invalid pagination parameters. 'page' and 'page_size' must be positive integers."
                }), 400

            history = self.history_manager.get()
            total = len(history)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_history = history[start:end]

            return jsonify({
                "command_history": paginated_history,
                "running_commands": self.history_manager.get_running(),
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }), 200

    def run(self):
        host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_RUN_PORT', 80))
        self.app.run(host=host, port=port)

if __name__ == "__main__":
    Application().run()
