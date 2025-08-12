#!/usr/bin/env python

"""
Google Custom Search API implementation
"""

import httpx
import asyncio
from typing import List, Optional
from loguru import logger
from src.engines.base import SearchEngine, SearchResult


class GoogleSearch(SearchEngine):
    """Google Custom Search API implementation"""
    
    def __init__(self, api_key: str, cse_id: str):
        super().__init__()
        self.api_key = api_key
        self.cse_id = cse_id
        self.priority = 1.0  # Highest priority
        self.rate_limit_cooldown = 300  # 5 minute cooldown
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        logger.info("Google search engine initialized successfully")
    
    def is_available(self) -> bool:
        """Check if Google search is available"""
        return (bool(self.api_key) and 
                bool(self.cse_id) and 
                not self.is_in_cooldown())
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute Google search using Custom Search API"""
        if not self.is_available():
            return []
            
        try:
            logger.info(f"Sending Google search request: {query}")
            
            params = {
                'key': self.api_key,
                'cx': self.cse_id,
                'q': query,
                'num': min(num_results, 10),  # Google API limit
                'safe': 'active',
                'fields': 'items(title,link,snippet,displayLink)'
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            logger.info(f"Google API response keys: {list(data.keys())}")
            
            results = []
            items = data.get('items', [])
            logger.info(f"Google API returned {len(items)} items")
            
            for item in items:
                title = item.get('title', '')
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                display_link = item.get('displayLink', '')
                
                result = SearchResult(
                    title=title,
                    link=link,
                    snippet=snippet,
                    source="google",
                    metadata={'display_link': display_link}
                )
                results.append(result)
                logger.info(f"Added result: {title}")
            
            self.record_success()
            logger.info(f"Google search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limiting errors
            if "quota" in error_str or "rate" in error_str or "limit" in error_str or "429" in error_str:
                self.record_error(is_rate_limit=True)
                logger.error(f"Google search rate limit error: {str(e)}")
            else:
                self.record_error()
                logger.error(f"Google search failed: {str(e)}")
            return []
