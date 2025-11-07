import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class BatchJob:
    id: str
    total: int
    processed: int = 0
    filled_items: List[dict] = field(default_factory=list)
    meta_items: List[dict] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    @property
    def status(self) -> str:
        return "done" if self.finished_at is not None else "running"

JOBS: Dict[str, BatchJob] = {}
