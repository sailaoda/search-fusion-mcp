#!/usr/bin/env python

"""
Configuration Manager
Handles all configuration from MCP environment variables
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from loguru import logger


@dataclass 
class SearchEngineConfig:
    """Search engine configuration"""
    api_key: Optional[str] = None
    secret_key: Optional[str] = None
    cse_id: Optional[str] = None
    enabled: bool = False


@dataclass
class ServerConfig:
    """Main server configuration"""
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "search_fusion.log"
    log_rotation: str = "100 MB"
    
    # Proxy configuration
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None
    
    # Rate limiting configuration
    default_cooldown: int = 300
    max_error_count: int = 3
    
    # Search engine configurations
    google: SearchEngineConfig = field(default_factory=SearchEngineConfig)
    serper: SearchEngineConfig = field(default_factory=SearchEngineConfig)  # Same priority as Google
    jina: SearchEngineConfig = field(default_factory=lambda: SearchEngineConfig(enabled=True))  # Always available
    bing: SearchEngineConfig = field(default_factory=SearchEngineConfig)
    baidu: SearchEngineConfig = field(default_factory=SearchEngineConfig)
    exa: SearchEngineConfig = field(default_factory=SearchEngineConfig)
    duckduckgo: SearchEngineConfig = field(default_factory=lambda: SearchEngineConfig(enabled=True))


class ConfigManager:
    """Configuration manager - handles all configuration sources"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_path: Legacy parameter, now deprecated, using pure MCP environment variable configuration
        """
        if config_path:
            logger.warning("⚠️ config_path parameter is deprecated, now using pure MCP environment variable configuration")
        
        self.config = ServerConfig()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from MCP environment variables only"""
        
        # Load from environment variables and MCP configuration only
        self._load_from_env()
        
        # Setup proxy environment variables
        self._setup_proxy()
        
        logger.info("✅ Configuration loaded successfully (MCP environment variable mode)")
        self._log_config_summary()
    
    def _load_from_env(self):
        """Load configuration from environment variables and MCP configuration"""
        
        # Basic configuration
        self.config.log_level = os.getenv('LOG_LEVEL', self.config.log_level)
        self.config.log_file = os.getenv('LOG_FILE', self.config.log_file)
        self.config.log_rotation = os.getenv('LOG_ROTATION', self.config.log_rotation)
        
        # Proxy configuration
        self.config.http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        self.config.https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
        self.config.no_proxy = os.getenv('NO_PROXY') or os.getenv('no_proxy', self.config.no_proxy)
        
        # MCP format API key configuration
        # Supports format: SEARCH_ENGINE_API_KEY, SEARCH_ENGINE_SECRET_KEY etc
        
        # Google configuration
        google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_SEARCH_API_KEY')
        google_cse_id = os.getenv('GOOGLE_CSE_ID') or os.getenv('GOOGLE_SEARCH_CSE_ID')
        if google_api_key:
            self.config.google = SearchEngineConfig(
                api_key=google_api_key,
                cse_id=google_cse_id,
                enabled=True
            )
        
        # Serper configuration
        serper_api_key = os.getenv('SERPER_API_KEY') or os.getenv('SERPER_SEARCH_API_KEY')
        if serper_api_key:
            self.config.serper = SearchEngineConfig(
                api_key=serper_api_key,
                enabled=True
            )
        
        # Bing configuration
        bing_api_key = os.getenv('BING_API_KEY') or os.getenv('BING_SEARCH_API_KEY')
        if bing_api_key:
            self.config.bing = SearchEngineConfig(
                api_key=bing_api_key,
                enabled=True
            )
        
        # Baidu configuration
        baidu_api_key = os.getenv('BAIDU_API_KEY') or os.getenv('BAIDU_SEARCH_API_KEY')
        baidu_secret_key = os.getenv('BAIDU_SECRET_KEY') or os.getenv('BAIDU_SEARCH_SECRET_KEY')
        if baidu_api_key and baidu_secret_key:
            self.config.baidu = SearchEngineConfig(
                api_key=baidu_api_key,
                secret_key=baidu_secret_key,
                enabled=True
            )
        
        # Jina configuration
        jina_api_key = os.getenv('JINA_API_KEY') or os.getenv('JINA_SEARCH_API_KEY')
        self.config.jina = SearchEngineConfig(
            api_key=jina_api_key,  # Can be empty
            enabled=True  # Jina is always enabled
        )
        
        # Exa configuration
        exa_api_key = os.getenv('EXA_API_KEY') or os.getenv('EXA_SEARCH_API_KEY')
        if exa_api_key:
            self.config.exa = SearchEngineConfig(
                api_key=exa_api_key,
                enabled=True
            )
    
    def _setup_proxy(self):
        """Setup proxy environment variables"""
        if self.config.http_proxy:
            os.environ['http_proxy'] = self.config.http_proxy
            os.environ['HTTP_PROXY'] = self.config.http_proxy
        
        if self.config.https_proxy:
            os.environ['https_proxy'] = self.config.https_proxy
            os.environ['HTTPS_PROXY'] = self.config.https_proxy
        
        if self.config.no_proxy:
            os.environ['no_proxy'] = self.config.no_proxy
            os.environ['NO_PROXY'] = self.config.no_proxy
    
    def _log_config_summary(self):
        """Log configuration summary"""
        enabled_engines = []
        for engine_name in ['google', 'serper', 'jina', 'duckduckgo', 'exa', 'bing', 'baidu']:
            if self.is_engine_enabled(engine_name):
                config = self.get_engine_config(engine_name)
                if config.api_key:
                    enabled_engines.append(f"{engine_name.title()} (with API key)")
                else:
                    enabled_engines.append(f"{engine_name.title()} (free)")
        
        logger.info(f"📊 Enabled search engines: {', '.join(enabled_engines) if enabled_engines else 'None'}")
        
        if self.config.http_proxy or self.config.https_proxy:
            logger.info(f"🌐 Proxy configuration: HTTP={self.config.http_proxy}, HTTPS={self.config.https_proxy}")
        
        logger.info(f"📝 Logging: Level={self.config.log_level}, File={self.config.log_file}")
    
    def get_engine_config(self, engine_name: str) -> SearchEngineConfig:
        """Get configuration for specified search engine"""
        return getattr(self.config, engine_name.lower(), SearchEngineConfig(enabled=False))
    
    def is_engine_enabled(self, engine_name: str) -> bool:
        """Check if search engine is enabled and has valid configuration"""
        engine_config = self.get_engine_config(engine_name)
        
        # DuckDuckGo and Jina don't require API keys
        if engine_name.lower() in ['duckduckgo', 'jina']:
            return True
        
        # Other engines require API keys
        return engine_config.enabled and bool(engine_config.api_key)
    
    def get_proxy_config(self) -> Dict[str, Optional[str]]:
        """Get proxy configuration"""
        return {
            "http://": self.config.http_proxy,
            "https://": self.config.https_proxy,
        } if self.config.http_proxy or self.config.https_proxy else None
