#!/usr/bin/env python

"""
DuckDuckGo search implementation
"""

import asyncio
from typing import List
from loguru import logger
from src.engines.base import SearchEngine, SearchResult


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search implementation"""
    
    def __init__(self):
        super().__init__()
        self.priority = 2.0  # Lower priority than Google and Jina
        self.rate_limit_cooldown = 60  # 60 second cooldown
        
        logger.info("DuckDuckGo search engine initialized successfully")
    
    def is_available(self) -> bool:
        """DuckDuckGo search is always available"""
        return not self.is_in_cooldown()
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute search using DuckDuckGo"""
        if not self.is_available():
            return []
            
        try:
            logger.info(f"Sending DuckDuckGo search request: {query}")
            
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
            
            self.record_success()
            logger.info(f"DuckDuckGo search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            # Check if this is a rate limiting error
            if "rate" in error_str or "limit" in error_str or "429" in error_str:
                self.record_error(is_rate_limit=True)
                logger.error(f"DuckDuckGo search rate limit error: {str(e)}")
            else:
                self.record_error()
                logger.error(f"DuckDuckGo search failed: {str(e)}")
            return []