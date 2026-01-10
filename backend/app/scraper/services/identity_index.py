from pathlib import Path
import json
from typing import Set

class HistoricalIdentityIndex:
    """
    Persistent index of team identities that have been identified as relevant
    (Tier 1 or Tier 2) in any season.
    """
    
    def __init__(self, index_path: Path = Path("./cache/historical_identities.json")):
        self._path = index_path
        self._identities: Set[str] = set()
        self._load()
    
    def _load(self):
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._identities = set(data)
            except Exception:
                self._identities = set()
    
    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Convert set to sorted list for deterministic JSON
        data = sorted(list(self._identities))
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def add(self, identity: str):
        """Add a team identity ID to the index."""
        if identity and identity not in self._identities:
            self._identities.add(identity)
            self.save()  # Auto-save on new addition? Or manual? 
                        # Auto-save might be slow if we add many frequent items, 
                        # but discovery is slow anyway (HTTP requests).
                        # Let's save immediately to be safe against crashes.
    
    def add_many(self, identities: Set[str]):
        """Add multiple identities at once."""
        initial_count = len(self._identities)
        self._identities.update(identities)
        if len(self._identities) > initial_count:
            self.save()

    def is_known(self, identity: str) -> bool:
        """Check if an identity is in the historical index."""
        return identity in self._identities
    
    def get_all(self) -> Set[str]:
        return self._identities.copy()
