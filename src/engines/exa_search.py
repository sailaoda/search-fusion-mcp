#!/usr/bin/env python

"""
Exa AI search implementation
"""

from typing import List
from loguru import logger
from src.engines.base import SearchEngine, SearchResult


class ExaSearch(SearchEngine):
    """Exa AI search implementation"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.priority = 2.0  # Same priority as DuckDuckGo
        self.rate_limit_cooldown = 60  # 60 second cooldown
        
        try:
            from exa_py import Exa
            self.exa = Exa(api_key=api_key)
            logger.info("Exa search engine initialized successfully")
        except ImportError:
            logger.warning("exa-py library not found, ExaSearch will not be available")
            self.exa = None
        except Exception as e:
            logger.error(f"Exa search engine initialization failed: {str(e)}")
            self.exa = None
    
    def is_available(self) -> bool:
        """Check if Exa search is available"""
        return (self.exa is not None and 
                bool(self.api_key) and 
                not self.is_in_cooldown())
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute search using Exa AI"""
        if not self.is_available():
            return []
            
        try:
            logger.info(f"Sending Exa search request: {query}")
            
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
            
            self.record_success()
            logger.info(f"Exa search successful: {query} ({len(results)} results)")
            
            return results
                
        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "limit" in error_str or "429" in error_str or "quota" in error_str:
                self.record_error(is_rate_limit=True)
                logger.error(f"Exa search rate limit error: {str(e)}")
            else:
                self.record_error()
                logger.error(f"Exa search failed: {str(e)}")
            return []