"""Checkpoint system for scraper resume capability."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class CheckpointData(BaseModel):
    """Data stored in a checkpoint."""
    phase: int = 1
    current_position: Optional[str] = None
    completed_urls: list[str] = Field(default_factory=list)
    sponsor_names: set[str] = Field(default_factory=set)
    team_queue: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CheckpointManager:
    """Manages checkpoint persistence."""
    
    def __init__(self, path: Path):
        self._path = path
    
    def save(self, data: CheckpointData) -> None:
        """Save checkpoint to file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert for JSON serialization
        json_data = data.model_dump()
        json_data['sponsor_names'] = list(json_data['sponsor_names'])
        json_data['last_updated'] = data.last_updated.isoformat()
        
        self._path.write_text(json.dumps(json_data, indent=2))
    
    def load(self) -> Optional[CheckpointData]:
        """Load checkpoint from file, or None if not exists."""
        if not self._path.exists():
            return None
        
        json_data = json.loads(self._path.read_text())
        json_data['sponsor_names'] = set(json_data['sponsor_names'])
        json_data['last_updated'] = datetime.fromisoformat(json_data['last_updated'])
        
        return CheckpointData(**json_data)
    
    def clear(self) -> None:
        """Delete checkpoint file."""
        if self._path.exists():
            self._path.unlink()
