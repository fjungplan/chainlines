from pathlib import Path
import json
from rapidfuzz import fuzz

class GTRelevanceIndex:
    SIMILARITY_THRESHOLD = 80
    
    def __init__(self, index_path: Path = Path("./cache/gt_relevance_index.json")):
        self._path = index_path
        self._index: dict[str, list[str]] = {}
        self._load()
    
    def _load(self):
        if self._path.exists():
            try:
                self._index = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                self._index = {}
    
    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._index, indent=2), encoding="utf-8")
    
    def add_year(self, year: int, teams: list[str]):
        self._index[str(year)] = teams
    
    def is_relevant(self, team_name: str, year: int) -> bool:
        year_teams = self._index.get(str(year), [])
        for gt_team in year_teams:
            if fuzz.ratio(team_name.lower(), gt_team.lower()) >= self.SIMILARITY_THRESHOLD:
                return True
        return False
