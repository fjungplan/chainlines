"""Test CLI interface."""
import pytest
from unittest.mock import patch, AsyncMock

def test_cli_parses_phase():
    """CLI should parse --phase argument."""
    from app.scraper.cli import parse_args
    
    args = parse_args(["--phase", "1"])
    assert args.phase == 1

def test_cli_parses_tier():
    """CLI should parse --tier argument."""
    from app.scraper.cli import parse_args
    
    args = parse_args(["--tier", "1"])
    assert args.tier == "1"

def test_cli_parses_resume():
    """CLI should parse --resume flag."""
    from app.scraper.cli import parse_args
    
    args = parse_args(["--resume"])
    assert args.resume is True

def test_cli_parses_dry_run():
    """CLI should parse --dry-run flag."""
    from app.scraper.cli import parse_args
    
    args = parse_args(["--dry-run"])
    assert args.dry_run is True

@pytest.mark.asyncio
async def test_cli_runner_executes_phase1():
    """CLI runner should execute Phase 1."""
    from app.scraper.cli import run_scraper
    
    with patch('app.scraper.orchestration.phase1.DiscoveryService') as mock_discovery:
        mock_instance = AsyncMock()
        mock_instance.discover_teams = AsyncMock(return_value=AsyncMock(team_urls=[], sponsor_names=[]))
        mock_discovery.return_value = mock_instance
        
        await run_scraper(phase=1, tier="1", resume=False, dry_run=True)
        
        mock_instance.discover_teams.assert_called_once_with(
            start_year=2025,
            end_year=1990,
            tier_level=1
        )
