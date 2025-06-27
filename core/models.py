from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ExecutedCommand:
    command: str
    duration: float
    status: str
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
