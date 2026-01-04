"""Concurrent worker pool for scraping."""
import asyncio
import logging
from typing import TypeVar, Callable, Awaitable, List, Any, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
T = TypeVar('T')
R = TypeVar('R')

class WorkerPool:
    """Pool of concurrent workers with limited parallelism."""
    
    def __init__(self, max_workers: int = 3):
        self._max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)
    
    async def run(
        self,
        items: List[T],
        task: Callable[[T], Awaitable[R]]
    ) -> List[R]:
        """Run task on all items with limited concurrency."""
        
        async def bounded_task(item: T) -> R:
            async with self._semaphore:
                return await task(item)
        
        tasks = [bounded_task(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)

@dataclass
class SourceWorker:
    """Worker configuration for a specific source."""
    fetch_fn: Callable[[str], Awaitable[Any]]
    max_workers: int
    queue: List[str] = field(default_factory=list)

class MultiSourceCoordinator:
    """Coordinates workers across multiple sources."""
    
    def __init__(self):
        self._sources: Dict[str, SourceWorker] = {}
    
    def add_source(
        self,
        name: str,
        fetch_fn: Callable[[str], Awaitable[Any]],
        max_workers: int = 2
    ) -> None:
        """Register a source with its worker config."""
        self._sources[name] = SourceWorker(
            fetch_fn=fetch_fn,
            max_workers=max_workers
        )
    
    async def enqueue(self, source: str, url: str) -> None:
        """Add URL to source's queue."""
        if source in self._sources:
            self._sources[source].queue.append(url)
    
    async def run_all(self) -> None:
        """Run all source workers in parallel."""
        tasks = []
        
        for name, worker in self._sources.items():
            pool = WorkerPool(max_workers=worker.max_workers)
            task = pool.run(worker.queue, worker.fetch_fn)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
