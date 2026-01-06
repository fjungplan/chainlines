import pytest
from pathlib import Path
from app.scraper.utils.cache import CacheManager

@pytest.fixture
def cache_dir(tmp_path):
    return tmp_path / "cache"

@pytest.fixture
def cache_manager(cache_dir):
    return CacheManager(cache_dir=cache_dir)

def test_cache_miss_returns_none(cache_manager):
    """When key doesn't exist, get() returns None"""
    assert cache_manager.get("non_existent_key") is None

def test_cache_set_and_get(cache_manager):
    """After set(key, data), get(key) returns the data"""
    key = "test_url"
    data = "<html>content</html>"
    cache_manager.set(key, data)
    assert cache_manager.get(key) == data

def test_cache_uses_hash_for_filename(cache_manager, cache_dir):
    """Verify long URLs are hashed to safe filenames"""
    key = "https://www.cyclingflash.com/team/ineos-grenadiers/2024"
    cache_manager.set(key, "data")
    
    # Check that a file exists and it's not named with the URL literally
    files = list(cache_dir.glob("**/*"))
    # Filter for files only
    files = [f for f in files if f.is_file()]
    assert len(files) == 1
    filename = files[0].name
    assert len(filename) == 64 + 4  # SHA256 (64 chars) + .txt or .html extension
    assert "cyclingflash.com" not in filename

def test_cache_respects_domain_subdirectory(cache_manager, cache_dir):
    """URLs from different domains go to different subdirs"""
    key1 = "https://domain1.com/page1"
    key2 = "https://domain2.com/page2"
    
    cache_manager.set(key1, "data1", domain="domain1.com")
    cache_manager.set(key2, "data2", domain="domain2.com")
    
    assert (cache_dir / "domain1.com").is_dir()
    assert (cache_dir / "domain2.com").is_dir()
    
    # Verify we can still get them
    assert cache_manager.get(key1, domain="domain1.com") == "data1"
    assert cache_manager.get(key2, domain="domain2.com") == "data2"

def test_force_refresh_bypasses_cache(cache_manager):
    """When force_refresh=True, cache is ignored"""
    key = "refresh_test"
    cache_manager.set(key, "old_data")
    
    # Normal get returns cached data
    assert cache_manager.get(key) == "old_data"
    
    # Get with force_refresh returns None
    assert cache_manager.get(key, force_refresh=True) is None
