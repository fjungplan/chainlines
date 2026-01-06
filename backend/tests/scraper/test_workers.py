import pytest
from pydantic import ValidationError
from app.scraper.orchestration.workers import SourceWorker, SourceData

def test_source_data_model_validates():
    """SourceData model accepts valid data."""
    data = SourceData(
        source="test",
        raw_content="<html></html>",
        founded_year=1990,
        dissolved_year=2000,
        history_text="Some history.",
        extra={"meta": "data"}
    )
    assert data.source == "test"
    assert data.founded_year == 1990
    assert data.extra["meta"] == "data"

def test_source_worker_is_abstract():
    """Cannot instantiate SourceWorker directly."""
    with pytest.raises(TypeError):
        SourceWorker()
