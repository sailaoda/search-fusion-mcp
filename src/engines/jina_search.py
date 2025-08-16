#!/usr/bin/env python

"""
Jina AI Search Engine - Advanced search with AI-powered results
"""

from typing import List, Dict, Any
from loguru import logger
from .base import SearchEngine, SearchResult


class JinaSearch(SearchEngine):
    """Jina AI search implementation"""
    
    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key
        self.priority = 1.5  # High priority for AI-powered search
        self.rate_limit_cooldown = 60  # 1 minute cooldown
        
        # Jina search endpoints
        self.jina_search_api = "https://s.jina.ai/"
        self.jina_search_api_premium = "https://api.jina.ai/v1/search"
        self.timeout = 30
        
        logger.info("Jina AI search engine initialized successfully")
    
    def is_available(self) -> bool:
        """Jina search requires API key to work"""
        if not self.api_key:
            return False
        return not self.is_in_cooldown()
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute Jina AI search"""
        if not query or not query.strip():
            return []
            
        try:
            logger.info(f"Sending Jina search request: {query}")
            
            # Get raw search results
            raw_results = await self._jina_search(query, num_results)
            
            # Convert to SearchResult objects
            results = []
            for item in raw_results[:num_results]:
                title = item.get('title', 'No title')
                url = item.get('url', item.get('link', ''))
                description = item.get('description', item.get('snippet', ''))
                
                if url:  # Only add results with valid URLs
                    results.append(SearchResult(
                        title=title,
                        link=url,
                        snippet=description,
                        source="jina"
                    ))
            
            await self.record_success()
            logger.info(f"Jina search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "limit" in error_str or "429" in error_str or "quota" in error_str:
                await self.record_error(is_rate_limit=True)
                logger.error(f"Jina search rate limit error: {str(e)}")
            else:
                await self.record_error()
                logger.error(f"Jina search failed: {str(e)}")
            return []
    
    async def _jina_search(self, query: str, num_results: int = 10) -> List[dict]:
        """Execute Jina search using direct API calls"""
        # If have API key and requesting more than 10 results, use premium API
        if self.api_key and num_results > 10:
            return await self._jina_premium_search(query, num_results)
        else:
            return await self._jina_basic_search(query, num_results)
    
    async def _jina_basic_search(self, query: str, num_results: int = 10) -> List[dict]:
        """Basic Jina search (free version)"""
        from urllib.parse import quote
        
        encoded_query = quote(query)
        jina_url = f"{self.jina_search_api}{encoded_query}"
        
        headers = {
            "Accept": "application/json"
        }
        
        # Use shared HTTP client for better connection pooling
        response = await self.http_client.get(jina_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to unified format
        if isinstance(data, list):
            return data[:num_results]
        elif isinstance(data, dict) and 'results' in data:
            return data['results'][:num_results]
        else:
            return []
    
    async def _jina_premium_search(self, query: str, num_results: int = 30) -> List[dict]:
        """Premium Jina search with API key"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "num": min(num_results, 100)  # API limit
        }
        
        # Use shared HTTP client for better connection pooling
        response = await self.http_client.post(
            self.jina_search_api_premium, 
            headers=headers, 
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('results', [])
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Jina engine status with API key information"""
        status = await super().get_status()
        status["has_api_key"] = bool(self.api_key)
        status["features"] = "Premium" if self.api_key else "None (API key required)"
        return status