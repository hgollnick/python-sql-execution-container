from threading import Lock
from typing import List, Dict, Optional
from .models import ExecutedCommand
from datetime import datetime

class CommandHistoryManager:
    def __init__(self):
        self._history: List[ExecutedCommand] = []
        self._running: List[Dict] = []  # Each dict: {command, start_time, status}
        self._lock = Lock()

    def add_running(self, command: str):
        with self._lock:
            entry = {
                "command": command,
                "start_time": datetime.now(),
                "status": "in_progress"
            }
            self._running.append(entry)
            return entry

    def finish_running(self, command: str):
        with self._lock:
            for i, entry in enumerate(self._running):
                if entry["command"] == command and entry["status"] == "in_progress":
                    return self._running.pop(i)
            return None

    def add(self, commands: List[ExecutedCommand]):
        with self._lock:
            self._history.extend(commands)

    def clear(self):
        with self._lock:
            self._history.clear()
            self._running.clear()

    def get(self) -> List[Dict]:
        with self._lock:
            # Sort by timestamp descending
            sorted_cmds = sorted(self._history, key=lambda cmd: cmd.timestamp, reverse=True)
            return [
                {
                    "command": cmd.command,
                    "duration": cmd.duration,
                    "status": cmd.status,
                    "error": cmd.error,
                    "timestamp": cmd.timestamp.isoformat()
                }
                for cmd in sorted_cmds
            ]

    def get_running(self) -> List[Dict]:
        with self._lock:
            now = datetime.now()
            return [
                {
                    "command": entry["command"],
                    "status": entry["status"],
                    "delta": (now - entry["start_time"]).total_seconds(),
                    "start_time": entry["start_time"].isoformat()
                }
                for entry in self._running
            ]
