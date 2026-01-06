import hashlib
from pathlib import Path
from typing import Optional

class CacheManager:
    """Manages file-based caching for scraper responses and LLM results."""
    
    def __init__(self, cache_dir: Path = Path("./cache")):
        """
        Initialize the CacheManager.
        
        Args:
            cache_dir: The directory where cache files will be stored.
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _hash_key(self, key: str) -> str:
        """
        Create a filesystem-safe SHA256 hash of the key.
        
        Args:
            key: The key to hash (e.g., a URL or prompt).
            
        Returns:
            A 64-character hexadecimal hash string.
        """
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
    
    def _get_path(self, key: str, domain: str = "default") -> Path:
        """
        Get the cache file path for a given key and domain.
        
        Args:
            key: The cache key.
            domain: The domain subdirectory.
            
        Returns:
            A Path object pointing to the cache file.
        """
        hash_str = self._hash_key(key)
        
        # We'll determine the extension based on whether it already exists or content
        # But for path lookup, we check for both .html and .txt
        html_path = self.cache_dir / domain / f"{hash_str}.html"
        if html_path.exists():
            return html_path
            
        return self.cache_dir / domain / f"{hash_str}.txt"
    
    def get(self, key: str, domain: str = "default", force_refresh: bool = False) -> Optional[str]:
        """
        Retrieve cached content if it exists.
        
        Args:
            key: The cache key.
            domain: The domain subdirectory.
            force_refresh: If True, bypass the cache and return None.
            
        Returns:
            The cached content as a string, or None if not found or refresh is forced.
        """
        if force_refresh:
            return None
            
        path = self._get_path(key, domain)
        if path.exists():
            return path.read_text(encoding="utf-8")
            
        return None
    
    def set(self, key: str, content: str, domain: str = "default") -> None:
        """
        Store content in the cache.
        
        Args:
            key: The cache key.
            content: The content to cache.
            domain: The domain subdirectory.
        """
        hash_str = self._hash_key(key)
        
        # Determine extension based on content
        extension = ".html" if "<html>" in content.lower() or "<!doctype html>" in content.lower() else ".txt"
        
        domain_dir = self.cache_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        path = domain_dir / f"{hash_str}{extension}"
        path.write_text(content, encoding="utf-8")
