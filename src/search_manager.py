#!/usr/bin/env python

"""
Search Manager - Manages multiple search engines with priority-based failover
"""

from typing import List, Optional, Dict, Any
import time
from loguru import logger
from datetime import datetime

from src.config.config_manager import ConfigManager
from src.engines import (
    SearchEngine, 
    SearchResult,
    GoogleSearch,
    SerperSearch,
    DuckDuckGoSearch,
    BingSearch,
    BaiduSearch,
    ExaSearch,
    JinaSearch
)


class SearchManager:
    """Search manager responsible for managing multiple search engines with priority-based polling"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.engines: List[SearchEngine] = []
        self.last_used_engine: Optional[SearchEngine] = None
        self.last_search_time = 0

        self.config_manager = ConfigManager(config_path)
        self.cooldown_period = self.config_manager.config.default_cooldown

        self._initialize_engines()
        
        # Sort engines by priority (lower number = higher priority)
        self.engines.sort(key=lambda x: x.priority)
        
        logger.info(f"🔍 Search manager initialized with {len(self.engines)} engines")
        self._log_engine_summary()
    
    def _initialize_engines(self):
        """Initialize search engines"""
        
        # 1. Google search engine (highest priority)
        if self.config_manager.is_engine_enabled('google'):
            google_config = self.config_manager.get_engine_config('google')
            if google_config.api_key and google_config.cse_id:
                try:
                    self.engines.append(GoogleSearch(
                        api_key=google_config.api_key, 
                        cse_id=google_config.cse_id
                    ))
                    logger.info("✓ Google search engine initialized successfully")
                except Exception as e:
                    logger.error(f"✗ Google search engine initialization failed: {e}")
            else:
                logger.warning("⚠ Google search configuration incomplete (missing CSE_ID), skipping initialization")
        
        # 2. Serper search engine (same priority as Google)
        if self.config_manager.is_engine_enabled('serper'):
            serper_config = self.config_manager.get_engine_config('serper')
            try:
                self.engines.append(SerperSearch(api_key=serper_config.api_key))
                logger.info("✓ Serper search engine initialized successfully")
            except Exception as e:
                logger.error(f"✗ Serper search engine initialization failed: {e}")
        
        # 3. Jina AI search engine (second priority)
        jina_config = self.config_manager.get_engine_config('jina')
        try:
            self.engines.append(JinaSearch(api_key=jina_config.api_key))
            if jina_config.api_key:
                logger.info("✓ Jina AI search engine initialized successfully (advanced features available)")
            else:
                logger.info("✓ Jina AI search engine initialized successfully (basic features)")
        except Exception as e:
            logger.error(f"✗ Jina AI search engine initialization failed: {e}")
        
        # 4. DuckDuckGo search (free, always available)
        try:
            self.engines.append(DuckDuckGoSearch())
            logger.info("✓ DuckDuckGo search engine initialized successfully")
        except Exception as e:
            logger.error(f"✗ DuckDuckGo search engine initialization failed: {e}")
        
        # 5. Exa search engine
        if self.config_manager.is_engine_enabled('exa'):
            exa_config = self.config_manager.get_engine_config('exa')
            try:
                self.engines.append(ExaSearch(api_key=exa_config.api_key))
                logger.info("✓ Exa search engine initialized successfully")
            except Exception as e:
                logger.error(f"✗ Exa search engine initialization failed: {e}")
        
        # 6. Bing search engine
        if self.config_manager.is_engine_enabled('bing'):
            bing_config = self.config_manager.get_engine_config('bing')
            try:
                self.engines.append(BingSearch(api_key=bing_config.api_key))
                logger.info("✓ Bing search engine initialized successfully")
            except Exception as e:
                logger.error(f"✗ Bing search engine initialization failed: {e}")
        
        # 7. Baidu search engine
        if self.config_manager.is_engine_enabled('baidu'):
            baidu_config = self.config_manager.get_engine_config('baidu')
            if baidu_config.api_key and baidu_config.secret_key:
                try:
                    self.engines.append(BaiduSearch(
                        api_key=baidu_config.api_key,
                        secret_key=baidu_config.secret_key
                    ))
                    logger.info("✓ Baidu search engine initialized successfully")
                except Exception as e:
                    logger.error(f"✗ Baidu search engine initialization failed: {e}")
            else:
                logger.warning("⚠ Baidu search configuration incomplete (missing SECRET_KEY), skipping initialization")
    
    def _log_engine_summary(self):
        """Log search engine summary"""
        if not self.engines:
            logger.warning("⚠️ No search engines available")
            return
        
        engine_info = []
        for engine in self.engines:
            status = "✓" if engine.is_available() else "✗"
            engine_info.append(f"{status} {engine.__class__.__name__} (Priority: {engine.priority})")
        
        logger.info("📊 Available search engines:")
        for info in engine_info:
            logger.info(f"  {info}")
    
    async def search(self, query: str, num_results: int = 10, preferred_engine: str = "auto") -> List[SearchResult]:
        """Execute search with automatic engine selection and failover"""
        
        if not self.engines:
            logger.error("❌ No search engines available")
            return []
        
        # Update search statistics
        self.last_search_time = time.time()
        
        # Engine selection logic
        if preferred_engine.lower() != "auto":
            # Try to use preferred engine first
            target_engine = self._find_engine_by_name(preferred_engine)
            if target_engine and target_engine.is_available():
                logger.info(f"🎯 Using preferred engine: {preferred_engine}")
                results = await target_engine.search(query, num_results)
                if results:
                    self.last_used_engine = target_engine
                    return results
                else:
                    logger.warning(f"⚠️ Preferred engine {preferred_engine} returned no results, trying failover")
        
        # Auto selection: try engines in priority order
        for engine in self.engines:
            if not engine.is_available():
                continue
                
            logger.info(f"🔍 Trying {engine.__class__.__name__}...")
            
            try:
                results = await engine.search(query, num_results)
                
                if results:
                    self.last_used_engine = engine
                    logger.success(f"✅ Search successful with {engine.__class__.__name__}: {len(results)} results")
                    return results
                else:
                    logger.warning(f"⚠️ {engine.__class__.__name__} returned no results")
                    
            except Exception as e:
                logger.error(f"❌ {engine.__class__.__name__} failed: {str(e)}")
                continue
        
        logger.error("❌ All search engines failed or returned no results")
        return []
    
    def _find_engine_by_name(self, engine_name: str) -> Optional[SearchEngine]:
        """Find engine by name"""
        engine_name_lower = engine_name.lower()
        
        for engine in self.engines:
            class_name = engine.__class__.__name__.lower()
            if (engine_name_lower in class_name or 
                class_name.startswith(engine_name_lower) or
                engine_name_lower == class_name.replace('search', '')):
                return engine
        
        return None
    
    def get_available_engines(self) -> List[Dict[str, Any]]:
        """Get list of available engines with their status"""
        engine_list = []
        
        for engine in self.engines:
            engine_info = engine.get_status()
            engine_list.append(engine_info)
        
        return engine_list
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search manager statistics"""
        total_requests = sum(engine.total_requests for engine in self.engines)
        successful_requests = sum(engine.successful_requests for engine in self.engines)
        
        return {
            "total_engines": len(self.engines),
            "available_engines": len([e for e in self.engines if e.is_available()]),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": f"{(successful_requests / total_requests * 100) if total_requests > 0 else 0:.1f}%",
            "last_search_time": self.last_search_time,
            "last_used_engine": self.last_used_engine.__class__.__name__ if self.last_used_engine else None
        }
