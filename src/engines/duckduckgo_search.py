#!/usr/bin/env python

"""
DuckDuckGo Search Engine - Free search without API key requirement
"""

from typing import List
import asyncio
from loguru import logger

from .base import SearchEngine, SearchResult


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search engine implementation"""
    
    def __init__(self):
        super().__init__()
        self.priority = 2.0  # Lower priority since it's free but may be less reliable
        
        logger.info("DuckDuckGo search engine initialized successfully")
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute DuckDuckGo search using async HTTP client"""
        if not query or not query.strip():
            return []
            
        try:
            logger.info(f"Sending DuckDuckGo search request: {query}")
            
            # Use async HTTP client for true concurrency
            results = await self._async_search(query, num_results)
            
            await self.record_success()
            logger.info(f"DuckDuckGo search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            # Check if this is a rate limiting error
            if "rate" in error_str or "limit" in error_str or "429" in error_str:
                await self.record_error(is_rate_limit=True)
                logger.error(f"DuckDuckGo search rate limit error: {str(e)}")
            else:
                await self.record_error()
                logger.error(f"DuckDuckGo search error: {str(e)}")
            
            return []
    
    async def _async_search(self, query: str, num_results: int) -> List[SearchResult]:
        """Perform async search using HTTP client"""
        try:
            # Use DuckDuckGo instant answer API or HTML scraping
            # For now, fall back to sync DDGS but with proper async wrapper
            return await asyncio.to_thread(self._sync_search, query, num_results)
            
        except Exception as e:
            logger.error(f"Async DuckDuckGo search failed: {e}")
            return []
    
    def _sync_search(self, query: str, num_results: int) -> List[SearchResult]:
        """Synchronous search wrapped for async execution"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                search_results = list(ddgs.text(
                    keywords=query,
                    region="us-en",
                    max_results=num_results,
                    safesearch='moderate'
                ))
                
                for item in search_results:
                    title = item.get('title', '')
                    link = item.get('href', '')
                    snippet = item.get('body', '')
                    
                    results.append(SearchResult(
                        title=title,
                        link=link,
                        snippet=snippet,
                        source="duckduckgo"
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Sync DuckDuckGo search failed: {e}")
            return []