"""Server-Sent Events (SSE) Manager for real-time scraper monitoring."""
import asyncio
from typing import Dict


class SSEManager:
    """Manages SSE event subscriptions and emissions for scraper runs.
    
    Maintains in-memory queues for each subscribed run_id, allowing multiple
    clients to receive real-time updates about scraper progress, logs, and decisions.
    """
    
    def __init__(self) -> None:
        """Initialize the SSE manager with empty subscribers dictionary."""
        self._subscribers: Dict[str, asyncio.Queue] = {}
    
    def subscribe(self, run_id: str) -> asyncio.Queue:
        """Subscribe to events for a specific scraper run.
        
        If a subscription already exists for this run_id, returns the existing queue.
        This allows multiple calls to subscribe() without losing queued events.
        
        Args:
            run_id: Unique identifier for the scraper run
            
        Returns:
            asyncio.Queue that will receive events for this run_id
        """
        if run_id not in self._subscribers:
            self._subscribers[run_id] = asyncio.Queue()
        return self._subscribers[run_id]
    
    async def emit(self, run_id: str, event_type: str, data: dict) -> None:
        """Emit an event to all subscribers of a specific run.
        
        Args:
            run_id: Unique identifier for the scraper run
            event_type: Type of event (e.g., 'progress', 'log', 'decision')
            data: Event payload as a dictionary
        """
        if run_id in self._subscribers:
            await self._subscribers[run_id].put({
                "event": event_type,
                "data": data
            })
    
    def unsubscribe(self, run_id: str) -> None:
        """Remove a subscription and clean up its queue.
        
        Args:
            run_id: Unique identifier for the scraper run
        """
        if run_id in self._subscribers:
            del self._subscribers[run_id]


# Module-level singleton instance
sse_manager = SSEManager()
