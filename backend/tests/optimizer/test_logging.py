
import os
import pytest
from app.optimizer.runner import append_optimizer_log

def test_append_optimizer_log(tmp_path, monkeypatch):
    """Verify that append_optimizer_log writes correctly formatted logs."""
    # Mocking BACKEND_LOGS_DIR to a temp directory
    log_dir = tmp_path / "backend" / "logs" / "optimizer"
    log_dir.mkdir(parents=True)
    
    # We need to monkeypatch the file path logic in runner.py if it's hardcoded
    # For now, let's assume it uses a constant we can override or just check the output
    
    family_hash = "test_family_123"
    results = {
        "score": 4022.50,
        "best_generation": 412,
        "total_generations": 500,
        "lane_count": 12,
        "cost_breakdown": {
            "ATTRACTION": {"multiplier": 1.2, "sum": 1200.0},
            "BLOCKER": {"multiplier": 0.0, "sum": 0.0},
            "CUT_THROUGH": {"multiplier": 1, "sum": 10000.0},
            "Y_SHAPE": {"multiplier": 2, "sum": 300.0},
            "OVERLAP": {"multiplier": 0.5, "sum": 250000.0},
            "SPACING": {"multiplier": 0, "sum": -50.0}
        }
    }
    config = {
        "pop_size": 1000,
        "mutation_rate": 0.2,
        "patience": 500,
        "timeout_seconds": 3600,
        "mutation_strategies": {
            "SWAP": 0.2, "HEURISTIC": 0.2, "COMPACTION": 0.3, "EXPLORATION": 0.3
        }
    }
    
    # Override the log path in runner.py for this test
    # (Assuming we define LOG_DIR in runner.py)
    import app.optimizer.runner as runner
    monkeypatch.setattr(runner, "OPTIMIZER_LOGS_DIR", str(log_dir))
    
    append_optimizer_log(family_hash, results, config)
    
    log_file = log_dir / f"family_{family_hash}.log"
    assert log_file.exists()
    
    content = log_file.read_text()
    assert "OPTIMIZATION COMPLETE" in content
    assert "Score 4022.50" in content
    assert "Achieved at Gen 412 / 500" in content
    assert "Pop 1000" in content
    assert "SWAP: 0.2" in content
    assert "Attraction (Weight N/A): Multiplier (avg dist^2) 1.20 -> Sum 1200.00" in content
