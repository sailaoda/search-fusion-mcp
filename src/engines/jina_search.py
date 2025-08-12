#!/usr/bin/env python

"""
Jina AI search implementation
"""

from typing import List, Optional
from loguru import logger
from src.engines.base import SearchEngine, SearchResult


class JinaSearch(SearchEngine):
    """Jina AI search implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.priority = 1.5  # Between Google and DuckDuckGo
        self.rate_limit_cooldown = 60  # 60 second cooldown
        
        # Initialize basic Jina client configuration
        self.timeout = 30
        self.jina_search_api = "https://s.jina.ai/"
        self.jina_search_api_premium = "https://svip.jina.ai/"
        
        logger.info("Jina search engine initialized successfully")
    
    def is_available(self) -> bool:
        """Jina search is always available (basic features work with or without API key)"""
        return not self.is_in_cooldown()
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute search using Jina AI"""
        if not self.is_available():
            return []
            
        try:
            logger.info(f"Sending Jina search request: {query}")
            
            # Use Jina search API directly
            search_results = await self._jina_search(query, num_results)
            
            results = []
            for item in search_results:
                # Handle different result formats
                if isinstance(item, dict):
                    title = item.get("title", "") or item.get("name", "")
                    url = item.get("url", "") or item.get("link", "") or item.get("href", "")
                    content = item.get("content", "") or item.get("snippet", "") or item.get("body", "")
                    
                    # Limit snippet length
                    snippet = content[:300] + "..." if len(content) > 300 else content
                    
                    results.append(SearchResult(
                        title=title,
                        link=url,
                        snippet=snippet,
                        source="jina"
                    ))
            
            self.record_success()
            logger.info(f"Jina search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "limit" in error_str or "429" in error_str or "quota" in error_str:
                self.record_error(is_rate_limit=True)
                logger.error(f"Jina search rate limit error: {str(e)}")
            else:
                self.record_error()
                logger.error(f"Jina search failed: {str(e)}")
            return []
    
    async def _jina_search(self, query: str, num_results: int = 10) -> List[dict]:
        """Execute Jina search using direct API calls"""
        import httpx
        from urllib.parse import quote
        
        # If have API key and requesting more than 10 results, use premium API
        if self.api_key and num_results > 10:
            return await self._jina_premium_search(query, num_results)
        else:
            return await self._jina_basic_search(query, num_results)
    
    async def _jina_basic_search(self, query: str, num_results: int = 10) -> List[dict]:
        """Basic Jina search (free version)"""
        import httpx
        from urllib.parse import quote
        
        encoded_query = quote(query)
        jina_url = f"{self.jina_search_api}{encoded_query}"
        
        headers = {
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(jina_url, headers=headers)
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
        """Premium Jina search (requires API key)"""
        import httpx
        
        if not self.api_key:
            raise Exception("Premium search requires Jina API key")
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            "q": query,
            "num": min(num_results, 100)  # API limit
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.jina_search_api_premium, 
                                       headers=headers, 
                                       json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])