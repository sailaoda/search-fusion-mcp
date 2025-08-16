#!/usr/bin/env python

"""
Base search engine classes and common functionality
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import time
import asyncio
import httpx
from loguru import logger
from dataclasses import dataclass


class HTTPClientManager:
    """Shared HTTP client manager for connection pooling"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get shared HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            # Configure connection limits for better concurrency
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
            
            # Configure timeouts
            timeout = httpx.Timeout(
                connect=10.0,
                read=30.0,
                write=10.0,
                pool=5.0
            )
            
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                follow_redirects=True,
                verify=True
            )
        
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


@dataclass
class SearchResult:
    """Represents a single search result"""
    title: str
    link: str
    snippet: str
    source: str
    metadata: Optional[Dict[str, Any]] = None


class SearchEngine(ABC):
    """Abstract base class for all search engines"""
    
    def __init__(self):
        self.priority = 10  # Lower number = higher priority
        self.error_count = 0
        self.last_error_time = 0
        self.rate_limit_cooldown = 300  # 5 minutes default cooldown
        self.max_error_count = 3
        self.last_success_time = 0
        self.total_requests = 0
        self.successful_requests = 0
        
        # Thread safety for concurrent access
        self._stats_lock = asyncio.Lock()
        
        # Shared HTTP client for connection pooling
        self._http_manager = HTTPClientManager()
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get shared HTTP client for this engine"""
        return self._http_manager.client
        
    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute a search query
        
        Args:
            query: Search query string
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    def is_available(self) -> bool:
        """Check if this search engine is currently available"""
        return not self.is_in_cooldown()
    
    async def record_success(self):
        """Record a successful search (thread-safe)"""
        async with self._stats_lock:
            self.last_success_time = time.time()
            self.successful_requests += 1
            self.total_requests += 1
            # Reset error count on success
            if self.error_count > 0:
                logger.info(f"✅ {self.__class__.__name__} recovered from errors")
                self.error_count = 0
    
    async def record_error(self, is_rate_limit: bool = False):
        """Record a search error (thread-safe)
        
        Args:
            is_rate_limit: Whether this is a rate limiting error
        """
        async with self._stats_lock:
            self.error_count += 1
            self.last_error_time = time.time()
            self.total_requests += 1
            
            if is_rate_limit:
                logger.warning(f"⚠️ {self.__class__.__name__} hit rate limit, cooling down for {self.rate_limit_cooldown}s")
            elif self.error_count >= self.max_error_count:
                logger.error(f"❌ {self.__class__.__name__} disabled due to excessive errors ({self.error_count})")
    
    def is_in_cooldown(self) -> bool:
        """Check if engine is in cooldown period"""
        if self.error_count >= self.max_error_count:
            time_since_error = time.time() - self.last_error_time
            return time_since_error < self.rate_limit_cooldown
        return False
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    async def get_status(self) -> Dict[str, Any]:
        """Get engine status information (thread-safe)"""
        async with self._stats_lock:
            return {
                "name": self.__class__.__name__,
                "priority": self.priority,
                "available": self.is_available(),
                "in_cooldown": self.is_in_cooldown(),
                "error_count": self.error_count,
                "success_rate": f"{self.get_success_rate():.1f}%",
                "total_requests": self.total_requests,
                "last_success": self.last_success_time,
                "last_error": self.last_error_time
            }
