#!/usr/bin/env python

"""
Bing search API implementation
"""

import httpx
from typing import List
from loguru import logger
from src.engines.base import SearchEngine, SearchResult


class BingSearch(SearchEngine):
    """Bing search implementation"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.priority = 3.0  # Lower priority
        self.rate_limit_cooldown = 300  # 5 minute cooldown
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        
        logger.info("Bing search engine initialized successfully")
    
    def is_available(self) -> bool:
        """Check if Bing search is available"""
        return (bool(self.api_key) and 
                not self.is_in_cooldown())
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute search using Bing API"""
        if not self.is_available():
            return []
            
        try:
            logger.info(f"Sending Bing search request: {query}")
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Accept': 'application/json'
            }
            
            params = {
                'q': query,
                'count': min(num_results, 50),  # Bing API limit
                'offset': 0,
                'mkt': 'en-US',
                'safesearch': 'Moderate'
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
            
            results = []
            web_pages = data.get('webPages', {}).get('value', [])
            
            for item in web_pages:
                title = item.get('name', '')
                link = item.get('url', '')
                snippet = item.get('snippet', '')
                
                results.append(SearchResult(
                    title=title,
                    link=link,
                    snippet=snippet,
                    source="bing"
                ))
            
            self.record_success()
            logger.info(f"Bing search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "limit" in error_str or "429" in error_str or "quota" in error_str:
                self.record_error(is_rate_limit=True)
                logger.error(f"Bing search rate limit error: {str(e)}")
            else:
                self.record_error()
                logger.error(f"Bing search failed: {str(e)}")
            return []