import os
import logging
from flask import Flask, jsonify, request
from threading import Thread, Lock
import uuid
from core.config import DatabaseConfig
from core.db import DatabaseConnectionManager
from core.executor import SQLCommandExecutor
from core.history import CommandHistoryManager

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
            with self.jobs_lock:
                job = self.jobs.get(job_id)
            if not job:
                return jsonify({
                    "status": "error",
                    "message": f"Job ID {job_id} not found"
                }), 404
            return jsonify({
                "status": job["status"],
                "result": job["result"]
            }), 200

        @self.app.route('/clear', methods=['DELETE'])
        def clear_executed_commands():
            self.history_manager.clear()
            return jsonify({
                "status": "success",
                "message": "Command history cleared"
            }), 200

        @self.app.route('/', methods=['GET'])
        def health_check():
            return jsonify({
                "command_history": self.history_manager.get(),
                "running_commands": self.history_manager.get_running()
            }), 200

    def run(self):
        host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_RUN_PORT', 80))
        self.app.run(host=host, port=port)

if __name__ == "__main__":
    Application().run()
