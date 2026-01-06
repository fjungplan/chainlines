from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel

class SourceData(BaseModel):
    """Data returned by a source worker."""
    source: str
    raw_content: Optional[str] = None
    founded_year: Optional[int] = None
    dissolved_year: Optional[int] = None
    history_text: Optional[str] = None
    extra: Dict[str, Any] = {}

class SourceWorker(ABC):
    """Abstract base for source-specific workers."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this source."""
        pass
    
    @abstractmethod
    async def fetch(self, url: str) -> Optional[SourceData]:
        """Fetch and parse data from this source."""
        pass
