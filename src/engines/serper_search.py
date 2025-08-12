#!/usr/bin/env python

"""
Serper API Search implementation (Google search alternative)
"""

import httpx
from typing import List
from loguru import logger
from src.engines.base import SearchEngine, SearchResult


class SerperSearch(SearchEngine):
    """Serper API search implementation (Google search alternative)"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.priority = 1.0  # Same priority as Google
        self.rate_limit_cooldown = 60  # 1 minute cooldown
        self.base_url = "https://google.serper.dev/search"
        
        logger.info("Serper search engine initialized successfully")
    
    def is_available(self) -> bool:
        """Check if Serper search is available"""
        return bool(self.api_key) and not self.is_in_cooldown()
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Execute Google search using Serper API"""
        if not self.is_available():
            return []
            
        try:
            logger.info(f"Sending Serper search request: {query}")
            
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': min(num_results, 100),  # Serper API limit
                'autocorrect': False,
                'gl': 'us',  # Default US region
                'hl': 'en'   # Default English
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            results = []
            
            # Process knowledge graph results (highest priority)
            knowledge_graph = data.get('knowledgeGraph')
            if knowledge_graph:
                title = knowledge_graph.get('title', '')
                description = knowledge_graph.get('description', '')
                website = knowledge_graph.get('website', '')
                
                if title:
                    results.append(SearchResult(
                        title=f"📚 Knowledge Graph: {title}",
                        link=website,
                        snippet=description or f"Information about {title}",
                        source="serper"
                    ))
            
            # Process organic search results
            organic_results = data.get('organic', [])
            for item in organic_results:
                title = item.get('title', '')
                link = item.get('link', '')
                snippet = item.get('snippet', '')
                
                if title and link:
                    results.append(SearchResult(
                        title=title,
                        link=link,
                        snippet=snippet,
                        source="serper"
                    ))
            
            # Process "People Also Ask" results
            people_also_ask = data.get('peopleAlsoAsk', [])
            for item in people_also_ask[:2]:  # Only take first 2
                question = item.get('question', '')
                answer = item.get('snippet', '')
                link = item.get('link', '')
                
                if question:
                    results.append(SearchResult(
                        title=f"❓ {question}",
                        link=link,
                        snippet=answer or "Click to see detailed answer",
                        source="serper"
                    ))
            
            self.record_success()
            logger.info(f"Serper search successful: {query} ({len(results)} results)")
            
            return results[:num_results]
                
        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limiting errors
            if "rate" in error_str or "limit" in error_str or "429" in error_str or "quota" in error_str:
                self.record_error(is_rate_limit=True)
                logger.error(f"Serper search rate limit error: {str(e)}")
            else:
                self.record_error()
                logger.error(f"Serper search failed: {str(e)}")
            return []
