#!/usr/bin/env python

"""
Base search engine classes and common functionality
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import time
from loguru import logger
from dataclasses import dataclass


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
    
    def record_success(self):
        """Record a successful search"""
        self.last_success_time = time.time()
        self.successful_requests += 1
        self.total_requests += 1
        # Reset error count on success
        if self.error_count > 0:
            logger.info(f"✅ {self.__class__.__name__} recovered from errors")
            self.error_count = 0
    
    def record_error(self, is_rate_limit: bool = False):
        """Record a search error
        
        Args:
            is_rate_limit: Whether this is a rate limiting error
        """
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
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status information"""
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
