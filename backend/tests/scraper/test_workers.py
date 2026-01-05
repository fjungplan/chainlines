"""Test concurrent source workers."""
import pytest
import asyncio
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_worker_pool_runs_parallel():
    """WorkerPool should run tasks in parallel."""
    from app.scraper.workers import WorkerPool
    
    results = []
    
    async def task(item):
        await asyncio.sleep(0.01)
        results.append(item)
        return item
    
    pool = WorkerPool(max_workers=3)
    items = [1, 2, 3, 4, 5]
    
    await pool.run(items, task)
    
    assert len(results) == 5
    assert set(results) == {1, 2, 3, 4, 5}

@pytest.mark.asyncio
async def test_worker_pool_limits_concurrency():
    """WorkerPool should respect max_workers limit."""
    from app.scraper.workers import WorkerPool
    
    active = []
    max_active = 0
    
    async def task(item):
        nonlocal max_active
        active.append(item)
        max_active = max(max_active, len(active))
        await asyncio.sleep(0.05)
        active.remove(item)
        return item
    
    pool = WorkerPool(max_workers=2)
    await pool.run([1, 2, 3, 4], task)
    
    assert max_active <= 2

@pytest.mark.asyncio
async def test_multi_source_coordinator():
    """MultiSourceCoordinator should run workers per source."""
    from app.scraper.workers import MultiSourceCoordinator
    
    results = {"source_a": [], "source_b": []}
    
    async def fetch_a(url):
        results["source_a"].append(url)
    
    async def fetch_b(url):
        results["source_b"].append(url)
    
    coordinator = MultiSourceCoordinator()
    coordinator.add_source("source_a", fetch_a, max_workers=2)
    coordinator.add_source("source_b", fetch_b, max_workers=1)
    
    await coordinator.enqueue("source_a", "url1")
    await coordinator.enqueue("source_a", "url2")
    await coordinator.enqueue("source_b", "url3")
    
    await coordinator.run_all()
    
    assert len(results["source_a"]) == 2
    assert len(results["source_b"]) == 1
