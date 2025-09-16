#!/usr/bin/env python

"""
Search Fusion MCP Server - Main server implementation
High-Availability Multi-Engine Search Aggregation MCP Server
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from mcp.server.fastmcp import FastMCP, Context
from loguru import logger
import httpx
import wikipedia

from src.config.config_manager import ConfigManager
from src.search_manager import SearchManager
from src.web_fetcher import WebFetcher


class SearchFusionServer:
    """Search Fusion MCP Server main class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Search Fusion MCP Server"""
        
        # Initialize configuration manager
        self.config_manager = ConfigManager(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.search_manager: Optional[SearchManager] = None
        
        # Initialize web fetcher (get API keys from configuration)
        jina_config = self.config_manager.get_engine_config('jina')
        serper_config = self.config_manager.get_engine_config('serper')
        self.web_fetcher = WebFetcher(
            jina_api_key=jina_config.api_key,
            serper_api_key=serper_config.api_key
        )
        
        self.last_init_attempt = 0
        self.init_cooldown = 30
        
        # Concurrency control
        self._init_lock = asyncio.Lock()
        self._search_semaphore = asyncio.Semaphore(30)  # Limit concurrent searches
        
        # Create MCP server
        self.mcp = FastMCP("Search-Fusion")
        self._register_tools()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        try:
            # Configure loguru
            logger.remove()  # Remove default handler
            
            # Console logging with colors
            logger.add(
                lambda msg: print(msg, end=""),
                level=self.config_manager.config.log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                colorize=True
            )
            
            # File logging
            if self.config_manager.config.log_file:
                logger.add(
                    self.config_manager.config.log_file,
                    level=self.config_manager.config.log_level,
                    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                    rotation=self.config_manager.config.log_rotation,
                    retention="7 days",
                    compression="zip",
                    encoding="utf-8"
                )
            
        except Exception as e:
            print(f"⚠️ Failed to setup logging: {e}")
    
    def _register_tools(self):
        """Register MCP tools"""
        logger.info("🔧 Registering MCP tools...")
        
        @self.mcp.tool()
        async def search(query: str, num_results: int = 10, engine: str = "auto") -> str:
            """Execute web search and return results
            
            Args:
                query: Search query terms
                num_results: Number of results to return, default 10
                engine: Search engine type, options:
                    - "auto": Automatically select best available search engine (default)
                    - "google": Prioritize Google search (requires API key)
                    - "serper": Prioritize Serper search (requires API key)
                    - "jina": Prioritize Jina AI search
                    - "duckduckgo": Prioritize DuckDuckGo search
                    - "exa": Prioritize Exa search (requires API key)
                    - "bing": Prioritize Bing search (requires API key)
                    - "baidu": Prioritize Baidu search (requires API key)
            """
            return await self._handle_search(query, num_results, engine)
        
        @self.mcp.tool()
        async def fetch_url(url: str, use_jina: bool = True, with_image_alt: bool = False, max_length: int = 50000, page_number: int = 1) -> str:
            """Fetch web content with intelligent pagination support
            
            Args:
                url: Web URL to fetch
                use_jina: Whether to prioritize Jina Reader for LLM-optimized content, default True
                with_image_alt: Whether to generate alt text descriptions for images, default False
                max_length: Maximum content length per page, auto-paginate if exceeded, default 50000 characters
                page_number: Specific page to retrieve (starting from 1), default 1
            """
            return await self._handle_fetch_url(url, use_jina, with_image_alt, max_length, page_number)
        
        @self.mcp.tool()
        async def get_available_engines() -> str:
            """Get list of currently available search engines and their status"""
            return await self._handle_get_engines()
        
        @self.mcp.tool()
        async def search_wikipedia(entity: str, first_sentences: int = 10) -> str:
            """Search Wikipedia page content
            
            Args:
                entity: Entity to search for (people, places, concepts, events, etc.)
                first_sentences: Number of first sentences to return (set to 0 for full content), default 10
            """
            return await self._handle_wikipedia_search(entity, first_sentences)
        
        @self.mcp.tool()
        async def search_archived_webpage(url: str, year: int = 0, month: int = 0, day: int = 0) -> str:
            """Search archived versions of websites using Wayback Machine
            
            Args:
                url: Website URL to search
                year: Target year (optional)
                month: Target month (optional)
                day: Target day (optional)
            """
            return await self._handle_wayback_search(url, year, month, day)

        logger.info("✅ All MCP tools registered successfully")
    
    async def _ensure_search_manager(self) -> bool:
        """Ensure search manager is initialized (thread-safe)"""
        # Quick check without lock for performance
        if self.search_manager is not None:
            return True
        
        # Use lock for initialization to prevent race conditions
        async with self._init_lock:
            # Double-check after acquiring lock
            if self.search_manager is not None:
                return True
            
            # Check cooldown
            current_time = time.time()
            if current_time - self.last_init_attempt < self.init_cooldown:
                logger.warning(f"⏳ Search manager initialization in cooldown, {self.init_cooldown - (current_time - self.last_init_attempt):.0f}s remaining")
                return False
            
            self.last_init_attempt = current_time
            
            try:
                logger.info("🔄 Initializing search manager...")
                self.search_manager = SearchManager()
                logger.success("✅ Search manager initialized successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Search manager initialization failed: {e}")
                self.search_manager = None
                return False
    
    async def _handle_search(self, query: str, num_results: int, engine: str) -> str:
        """Handle search requests with concurrency control"""
        # Use semaphore to limit concurrent searches
        async with self._search_semaphore:
            try:
                # Ensure search manager is available
                if not await self._ensure_search_manager():
                    return self._error_response("Search manager unavailable, please try again later", query, engine)
                
                # Execute search with timeout handling
                start_time = time.time()
                logger.info(f"🔍 Starting search: query='{query}', engine='{engine}', num_results={num_results}")
                
                try:
                    results = await asyncio.wait_for(
                        self.search_manager.search(query, num_results, engine),
                        timeout=60.0  # 60 second timeout
                    )
                except asyncio.TimeoutError:
                    elapsed_time = time.time() - start_time
                    logger.error(f"⏰ Search timeout after {elapsed_time:.1f}s: query='{query}', engine='{engine}'")
                    return self._error_response("Search operation timed out", query, engine)
                
                elapsed_time = time.time() - start_time
                
                # Format response
                response = {
                    "query": query,
                    "engine": engine,
                    "time_ms": int(elapsed_time * 1000),
                    "num_results": len(results),
                    "results": [
                        {
                            "title": result.title,
                            "link": result.link,
                            "snippet": result.snippet,
                            "source": result.source,
                            "metadata": result.metadata
                        }
                        for result in results
                    ],
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
                
                if results:
                    logger.success(f"🎯 Search successful: '{query}' ({len(results)} results, {elapsed_time*1000:.0f}ms)")
                else:
                    logger.warning(f"⚠️ Search returned no results: '{query}'")
                    response["message"] = "No results found, try different keywords or search engines"
                
                return json.dumps(response, ensure_ascii=False, indent=2)
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(f"❌ Search error after {elapsed_time:.1f}s: {e}")
                return self._error_response(f"Search failed: {str(e)}", query, engine)
     
    async def _handle_fetch_url(self, url: str, use_jina: bool, with_image_alt: bool, max_length: int, page_number: int) -> str:
        """Handle URL fetching requests with intelligent pagination support"""
        try:
            logger.info(f"🔍 Starting web fetch: {url} (page {page_number})")
            start_time = time.time()
            
            try:
                # Use web fetcher with timeout
                result = await asyncio.wait_for(
                    self.web_fetcher.fetch_url(
                        url=url,
                        use_jina=use_jina,
                        with_image_alt=with_image_alt,
                        max_length=max_length,
                        page_number=page_number
                    ),
                    timeout=90.0  # 90 second timeout for web fetching
                )
            except asyncio.TimeoutError:
                elapsed_time = time.time() - start_time
                logger.error(f"⏰ Web fetch timeout after {elapsed_time:.1f}s: {url}")
                return json.dumps({
                    "success": False,
                    "error": "Web fetch operation timed out",
                    "url": url,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False, indent=2)
            
            elapsed_time = time.time() - start_time
            result['time_ms'] = int(elapsed_time * 1000)
            result['timestamp'] = datetime.now().isoformat()
            
            if result.get('success'):
                if result.get('is_paginated'):
                    logger.success(f"✅ Web fetch successful (paginated): {url} - {result['page_info']}")
                else:
                    logger.success(f"✅ Web fetch successful: {url} ({result.get('total_length', 0)} characters)")
            else:
                logger.error(f"❌ Web fetch failed: {url} - {result.get('error', 'Unknown error')}")
            
            return json.dumps(result, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ URL fetch exception: {e}")
            return json.dumps({
                "success": False,
                "error": f"Fetch exception: {str(e)}",
                "url": url,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2)
    

    
    async def _handle_get_engines(self) -> str:
        """Handle get available engines requests"""
        try:
            if not await self._ensure_search_manager():
                return json.dumps({
                    "error": "Search manager unavailable",
                    "engines": [],
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False, indent=2)
            
            engines = await self.search_manager.get_available_engines()
            stats = self.search_manager.get_search_stats()
            
            response = {
                "engines": engines,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📊 Engine status retrieved: {len(engines)} engines")
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Get engines error: {e}")
            return json.dumps({
                "error": f"Failed to get engine list: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2)
    
    async def _handle_wikipedia_search(self, entity: str, first_sentences: int) -> str:
        """Handle Wikipedia search requests with async optimization"""
        try:
            logger.info(f"🔍 Starting Wikipedia search for: {entity}")
            # Use async wrapper for synchronous Wikipedia operations
            page = await asyncio.to_thread(self._get_wikipedia_page, entity)
            logger.info(f"📄 Successfully retrieved Wikipedia page: {page.title}")
            
            result_parts = [f"Page Title: {page.title}"]
            
            if first_sentences > 0:
                try:
                    # Get summary using async wrapper
                    summary = await asyncio.to_thread(
                        wikipedia.summary, 
                        entity, 
                        sentences=first_sentences, 
                        auto_suggest=False
                    )
                    result_parts.append(f"First {first_sentences} sentences summary: {summary}")
                except Exception:
                    # Fallback to content splitting
                    content_sentences = page.content.split(". ")[:first_sentences]
                    summary = ". ".join(content_sentences) + "." if content_sentences else page.content[:5000] + "..."
                    result_parts.append(f"First {first_sentences} sentences summary: {summary}")
            else:
                result_parts.append(f"Complete content: {page.content}")
            
            result_parts.append(f"URL: {page.url}")
            
            result = {
                "entity": entity,
                "title": page.title,
                "content": "\n\n".join(result_parts),
                "url": page.url,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            logger.success(f"✅ Wikipedia search successful: {entity}")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except wikipedia.exceptions.DisambiguationError as e:
            options_list = "\n".join([f"- {option}" for option in e.options[:10]])
            content = (
                f"Disambiguation error: '{entity}' has multiple pages.\n\n"
                f"Available options:\n{options_list}\n\n"
                f"Please use more specific search terms."
            )
            
            result = {
                "entity": entity,
                "error": "disambiguation",
                "content": content,
                "options": e.options[:10],
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except wikipedia.exceptions.PageError:
            try:
                # Use async wrapper for search with detailed error handling
                logger.info(f"🔍 Attempting Wikipedia search for suggestions: {entity}")
                search_results = await asyncio.to_thread(wikipedia.search, entity, results=5)
                logger.info(f"📝 Wikipedia search returned {len(search_results) if search_results else 0} suggestions")
                
                if search_results:
                    suggestion_list = "\n".join([f"- {result}" for result in search_results[:5]])
                    content = (
                        f"Page not found: '{entity}' has no corresponding Wikipedia page.\n\n"
                        f"Similar pages:\n{suggestion_list}\n\n"
                        f"Please try searching for one of these suggestions."
                    )
                    
                    result = {
                        "entity": entity,
                        "error": "page_not_found",
                        "content": content,
                        "suggestions": search_results[:5],
                        "timestamp": datetime.now().isoformat(),
                        "success": False
                    }
                else:
                    result = {
                        "entity": entity,
                        "error": "page_not_found",
                        "content": f"Page not found: '{entity}' has no corresponding Wikipedia page and no similar pages found.",
                        "timestamp": datetime.now().isoformat(),
                        "success": False
                    }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            except (json.JSONDecodeError, ValueError) as json_error:
                logger.error(f"❌ Wikipedia API returned invalid JSON response: {str(json_error)}")
                return self._error_response(
                    f"Wikipedia API returned invalid response format. This usually indicates a temporary service issue. Please try again later.", 
                    entity, 
                    "wikipedia"
                )
            except Exception as search_error:
                error_msg = str(search_error)
                logger.error(f"❌ Wikipedia search internal error: {type(search_error).__name__}: {error_msg}")
                
                # Check if it's a JSON parsing error
                if "Expecting value" in error_msg and "line 1 column 1" in error_msg:
                    return self._error_response(
                        "Wikipedia service returned an empty or invalid response. This is usually a temporary issue with Wikipedia's servers. Please try again in a few moments.",
                        entity,
                        "wikipedia"
                    )
                else:
                    return self._error_response(f"Wikipedia search failed: {error_msg}", entity, "wikipedia")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Wikipedia search error: {type(e).__name__}: {error_msg}")
            
            # Handle specific JSON parsing errors
            if "Expecting value" in error_msg and "line 1 column 1" in error_msg:
                return self._error_response(
                    "Wikipedia service is temporarily unavailable or returned an invalid response. Please try again in a few moments.",
                    entity,
                    "wikipedia"
                )
            elif "JSONDecodeError" in str(type(e)) or "json" in error_msg.lower():
                return self._error_response(
                    "Wikipedia API returned an invalid response format. This is usually a temporary service issue.",
                    entity,
                    "wikipedia"
                )
            else:
                return self._error_response(f"Wikipedia search failed: {error_msg}", entity, "wikipedia")
    
    def _get_wikipedia_page(self, entity: str):
        """Synchronous helper method for getting Wikipedia page with retry logic"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                return wikipedia.page(title=entity, auto_suggest=False)
            except Exception as e:
                error_msg = str(e)
                if attempt < max_retries and ("Expecting value" in error_msg or "json" in error_msg.lower()):
                    logger.warning(f"⚠️ Wikipedia page fetch attempt {attempt + 1} failed with JSON error, retrying...")
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    raise  # Re-raise the exception if max retries reached or not a JSON error
    
    async def _handle_wayback_search(self, url: str, year: int, month: int, day: int) -> str:
        """Handle Wayback Machine search requests"""
        try:
            # Process URL
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            
            base_url = "https://archive.org/wayback/available"
            date_param = ""
            
            # Build date parameter
            if year > 0 and month > 0 and day > 0:
                import calendar
                current_year = datetime.now().year
                
                # Adjust year range
                if year < 1995:
                    year = 1995
                elif year > current_year:
                    year = current_year
                
                # Adjust month range
                if month < 1:
                    month = 1
                elif month > 12:
                    month = 12
                
                # Adjust day range
                max_day = calendar.monthrange(year, month)[1]
                if day < 1:
                    day = 1
                elif day > max_day:
                    day = max_day
                
                date_param = f"{year:04d}{month:02d}{day:02d}"
            
            # Send request
            params = {"url": url}
            if date_param:
                params["timestamp"] = date_param
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()
                
                # Check if response has content before parsing JSON
                if not response.text or not response.text.strip():
                    raise ValueError("Archive.org returned empty response")
                
                try:
                    data = response.json()
                except (json.JSONDecodeError, ValueError) as json_error:
                    logger.error(f"❌ Archive.org returned invalid JSON: {str(json_error)}")
                    logger.debug(f"Response content: {response.text[:500]}...")
                    raise ValueError(f"Archive.org returned invalid JSON response: {str(json_error)}")
            
            if "archived_snapshots" in data and "closest" in data["archived_snapshots"]:
                closest = data["archived_snapshots"]["closest"]
                archived_url = closest["url"]
                archived_timestamp = closest["timestamp"]
                available = closest.get("available", True)
                
                if not available:
                    result = {
                        "original_url": url,
                        "status": "unavailable",
                        "content": "Snapshot exists but is not available",
                        "timestamp": datetime.now().isoformat(),
                        "success": False
                    }
                else:
                    # Format timestamp
                    try:
                        import datetime as dt
                        dt_obj = dt.datetime.strptime(archived_timestamp, "%Y%m%d%H%M%S")
                        formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except Exception:
                        formatted_time = archived_timestamp
                    
                    result = {
                        "original_url": url,
                        "archived_url": archived_url,
                        "archived_timestamp": formatted_time,
                        "status": "found",
                        "content": f"Found archived version",
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    }
                
                logger.success(f"✅ Wayback Machine search successful: {url}")
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                result = {
                    "original_url": url,
                    "status": "not_found",
                    "content": f"No archived versions found for '{url}'",
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Wayback Machine search error: {e}")
            return self._error_response(f"Web archive search failed: {str(e)}", url, "wayback")

    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Performing cleanup operations")
        # Add any resources that need cleanup here
    
    def _error_response(self, error_msg: str, query: str = "", engine: str = "") -> str:
        """Generate unified error response"""
        error_response = {
            "error": error_msg,
            "query": query,
            "engine": engine,
            "suggestion": "Please try again later, or try using other search engines",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "server_info": {
                "version": "1.0.0",
                "encoding": "utf-8",
                "ensure_ascii": False
            }
        }
        
        # Log the error for debugging
        logger.error(f"🚨 Error response generated: {error_msg} (query: '{query}', engine: '{engine}')")
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def run(self):
        """Start the server"""
        try:
            logger.info("🚀 Starting Search Fusion MCP Server...")
            self.mcp.run()
        except KeyboardInterrupt:
            logger.info("👋 Received interrupt signal, shutting down server...")
        except Exception as e:
            logger.error(f"❌ Server runtime error: {e}")
        finally:
            asyncio.run(self.cleanup())


def main():
    """Main entry function"""
    server = SearchFusionServer()
    server.run()


if __name__ == "__main__":
    main()
