"""Test checkpoint system."""
import pytest
import json
from pathlib import Path
import tempfile

def test_checkpoint_schema_validates():
    """CheckpointData should validate correctly."""
    from app.scraper.checkpoint import CheckpointData
    
    cp = CheckpointData(
        phase=1,
        current_position="https://example.com/team/1",
        completed_urls=["https://example.com/team/2"],
        sponsor_names={"Visma", "Jumbo"}
    )
    
    assert cp.phase == 1
    assert len(cp.completed_urls) == 1
    assert "Visma" in cp.sponsor_names

def test_checkpoint_manager_save_and_load():
    """CheckpointManager should save and load checkpoints."""
    from app.scraper.checkpoint import CheckpointManager, CheckpointData
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "checkpoint.json"
        manager = CheckpointManager(path)
        
        # Save
        data = CheckpointData(phase=2, current_position="test-url")
        manager.save(data)
        
        # Load
        loaded = manager.load()
        assert loaded is not None
        assert loaded.phase == 2
        assert loaded.current_position == "test-url"

def test_checkpoint_manager_returns_none_if_no_file():
    """CheckpointManager.load should return None if no checkpoint exists."""
    from app.scraper.checkpoint import CheckpointManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nonexistent.json"
        manager = CheckpointManager(path)
        
        assert manager.load() is None

def test_checkpoint_manager_clear():
    """CheckpointManager.clear should delete checkpoint file."""
    from app.scraper.checkpoint import CheckpointManager, CheckpointData
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "checkpoint.json"
        manager = CheckpointManager(path)
        
        manager.save(CheckpointData())
        assert path.exists()
        
        manager.clear()
        assert not path.exists()
