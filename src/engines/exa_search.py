#!/usr/bin/env python

"""
Exa AI Search Engine - Advanced AI-powered search
"""

import asyncio
from typing import List
from loguru import logger
from .base import SearchEngine, SearchResult


class ExaSearch(SearchEngine):
    """Exa AI search implementation"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.priority = 1.8  # High priority for AI search
        self.rate_limit_cooldown = 120  # 2 minute cooldown
        
        # Initialize Exa client
        try:
            from exa_py import Exa
            self.exa = Exa(api_key=api_key)
            logger.info("Exa search engine initialized successfully")
        except ImportError:
            logger.error("Exa package not installed. Run: pip install exa-py")
            self.exa = None
        except Exception as e:
            logger.error(f"Exa initialization failed: {e}")
            self.exa = None
    
    def is_available(self) -> bool:
        """Check if Exa search is available"""
        return (self.exa is not None and 
                bool(self.api_key) and 
                not self.is_in_cooldown())
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute search using Exa AI with async wrapper"""
        if not self.is_available():
            return []
            
        try:
            logger.info(f"Sending Exa search request: {query}")
            
            # Use async wrapper for the synchronous Exa search
            results = await self._async_exa_search(query, num_results)
            
            await self.record_success()
            logger.info(f"Exa search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "limit" in error_str or "429" in error_str or "quota" in error_str:
                await self.record_error(is_rate_limit=True)
                logger.error(f"Exa search rate limit error: {str(e)}")
            else:
                await self.record_error()
                logger.error(f"Exa search failed: {str(e)}")
            return []
    
    async def _async_exa_search(self, query: str, num_results: int) -> List[SearchResult]:
        """Perform async Exa search using thread wrapper"""
        try:
            # Use asyncio.to_thread to run sync Exa search in thread pool
            search_results = await asyncio.to_thread(
                self._sync_exa_search, query, num_results
            )
            return search_results
            
        except Exception as e:
            logger.error(f"Async Exa search failed: {e}")
            return []
    
    def _sync_exa_search(self, query: str, num_results: int) -> List[SearchResult]:
        """Synchronous Exa search wrapped for async execution"""
        try:
            search_results = self.exa.search(
                query=query,
                num_results=min(num_results, 20),  # Exa API limit
                include_domains=None,
                exclude_domains=None,
                use_autoprompt=True
            )
            
            results = []
            for item in search_results.results:
                results.append(SearchResult(
                    title=item.title or "No title",
                    link=item.url,
                    snippet=item.text[:300] + "..." if item.text and len(item.text) > 300 else item.text or "",
                    source="exa"
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Sync Exa search failed: {e}")
            return []