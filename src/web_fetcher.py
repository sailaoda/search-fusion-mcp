#!/usr/bin/env python

"""
Web Fetcher Module - Comprehensive web fetching with pagination support
Integrates Jina AI Reader, Serper scrape, and traditional HTTP fetching
All English implementation
"""

import httpx
import asyncio
import json
import re
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse, quote
from loguru import logger
from bs4 import BeautifulSoup


class WebFetcher:
    """Comprehensive web fetcher with multiple methods and pagination support"""
    
    def __init__(self, jina_api_key: Optional[str] = None, serper_api_key: Optional[str] = None):
        """Initialize web fetcher
        
        Args:
            jina_api_key: Jina API key (optional)
            serper_api_key: Serper API key (optional)
        """
        self.jina_api_key = jina_api_key
        self.serper_api_key = serper_api_key
        self.timeout = 30
        
        # Jina API endpoints
        self.jina_read_api = "https://r.jina.ai/"
        self.jina_search_api = "https://s.jina.ai/"
        self.jina_search_api_premium = "https://svip.jina.ai/"
        
        # Page content storage with TTL
        self.page_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 3600  # 1 hour TTL for page cache
    
    async def fetch_url(self, url: str, use_jina: bool = True, with_image_alt: bool = False, 
                       max_length: int = 50000, page_number: int = 1) -> Dict[str, Any]:
        """Fetch web content with intelligent pagination support
        
        Args:
            url: Target URL
            use_jina: Whether to prioritize Jina AI
            with_image_alt: Whether to include image alt text
            max_length: Maximum content length per page
            page_number: Specific page to retrieve (for paginated content)
            
        Returns:
            Dictionary containing content, pagination info, etc.
        """
        try:
            # If requesting specific page, check cache first
            if page_number > 1:
                return await self._get_cached_page(url, page_number)
            
            # Try different fetching methods in priority order
            if use_jina:
                result = await self._fetch_with_jina(url, with_image_alt)
                if result and result.get('success'):
                    return await self._process_content(url, result, max_length)
            
            # Fallback: Use Serper scrape
            if self.serper_api_key:
                result = await self._fetch_with_serper(url)
                if result and result.get('success'):
                    return await self._process_content(url, result, max_length)
            
            # Last fallback: Traditional HTTP fetching
            result = await self._fetch_with_httpx(url)
            if result and result.get('success'):
                return await self._process_content(url, result, max_length)
            
            return {
                'success': False,
                'error': 'All fetching methods failed',
                'url': url
            }
            
        except Exception as e:
            logger.error(f"❌ Web fetching failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    async def _fetch_with_jina(self, url: str, with_image_alt: bool = False) -> Dict[str, Any]:
        """Fetch using Jina AI Reader"""
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            
            if self.jina_api_key:
                headers['Authorization'] = f'Bearer {self.jina_api_key}'
            
            # Add optional headers
            extra_headers = {}
            if with_image_alt:
                extra_headers["X-With-Generated-Alt"] = "true"
            
            extra_headers["X-With-Links-Summary"] = "all"
            extra_headers["X-Retain-Images"] = "none"
            extra_headers["X-Respond-With"] = "markdown"
            
            headers.update(extra_headers)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.jina_read_api, 
                                           headers=headers, 
                                           json={"url": url})
                response.raise_for_status()
                
                content = response.text
                
                if content and content.strip():
                    return {
                        'success': True,
                        'content': content,
                        'method': 'jina',
                        'format': 'markdown'
                    }
                else:
                    return {'success': False, 'error': 'Jina returned empty content'}
                    
        except Exception as e:
            logger.error(f"Jina fetching failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _fetch_with_serper(self, url: str) -> Dict[str, Any]:
        """Fetch using Serper scrape"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-API-KEY': self.serper_api_key
            }
            
            payload = {
                'url': url,
                'includeMarkdown': True
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    'https://scrape.serper.dev',
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            content = data.get('markdown') or data.get('text', '')
            if content.strip():
                return {
                    'success': True,
                    'content': content,
                    'method': 'serper',
                    'format': 'markdown' if data.get('markdown') else 'text',
                    'metadata': data.get('metadata', {})
                }
            else:
                return {'success': False, 'error': 'Serper returned empty content'}
                
        except Exception as e:
            logger.error(f"Serper fetching failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _fetch_with_httpx(self, url: str) -> Dict[str, Any]:
        """Fetch using traditional HTTP and convert to Markdown"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '').lower()
                
                if 'text/html' in content_type:
                    # Parse HTML and convert to Markdown
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove scripts and styles
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Extract main content
                    content = self._html_to_markdown(soup)
                    
                    return {
                        'success': True,
                        'content': content,
                        'method': 'httpx',
                        'format': 'markdown',
                        'title': soup.find('title').get_text() if soup.find('title') else ''
                    }
                else:
                    # Return text content directly
                    return {
                        'success': True,
                        'content': response.text,
                        'method': 'httpx',
                        'format': 'text'
                    }
                    
        except Exception as e:
            logger.error(f"HTTP fetching failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _html_to_markdown(self, soup: BeautifulSoup) -> str:
        """Convert HTML to simple Markdown format"""
        content_parts = []
        
        # Extract title
        title = soup.find('title')
        if title:
            content_parts.append(f"# {title.get_text().strip()}\n")
        
        # Extract main content area
        main_content = (soup.find('main') or 
                       soup.find('article') or 
                       soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
                       soup.find('body'))
        
        if main_content:
            # Process headings
            for i, heading in enumerate(main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
                level = int(heading.name[1])
                text = heading.get_text().strip()
                if text:
                    content_parts.append(f"{'#' * level} {text}\n")
            
            # Process paragraphs
            for p in main_content.find_all('p'):
                text = p.get_text().strip()
                if text:
                    content_parts.append(f"{text}\n")
            
            # Process lists
            for ul in main_content.find_all('ul'):
                for li in ul.find_all('li'):
                    text = li.get_text().strip()
                    if text:
                        content_parts.append(f"- {text}\n")
            
            # Process links
            for a in main_content.find_all('a', href=True):
                text = a.get_text().strip()
                href = a.get('href')
                if text and href:
                    content_parts.append(f"[{text}]({href})\n")
        
        return '\n'.join(content_parts) if content_parts else soup.get_text()
    
    async def _process_content(self, url: str, result: Dict[str, Any], max_length: int) -> Dict[str, Any]:
        """Process fetching result with pagination functionality"""
        content = result.get('content', '')
        
        if len(content) <= max_length:
            # Content doesn't need pagination
            processed_result = {
                'url': url,
                'method': result.get('method', 'unknown'),
                'format': result.get('format', 'text'),
                'success': True,
                'content': content,
                'total_length': len(content),
                'is_paginated': False,
                'pages': 1,
                'current_page': 1,
                'page_info': f"Complete content ({len(content)} characters)"
            }
        else:
            # Needs pagination
            pages = self._split_content_into_pages(content, max_length)
            # Create unique page ID for this session
            session_id = str(uuid.uuid4())[:8]
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            page_id = f"{session_id}_{content_hash}_{len(pages)}"
            self.page_cache[page_id] = {
                'pages': pages,
                'metadata': result,
                'url': url,
                'created_at': asyncio.get_event_loop().time()
            }
            
            processed_result = {
                'url': url,
                'method': result.get('method', 'unknown'),
                'format': result.get('format', 'text'),
                'success': True,
                'content': pages[0],  # Return first page
                'total_length': len(content),
                'is_paginated': True,
                'pages': len(pages),
                'current_page': 1,
                'page_id': page_id,
                'page_info': f"Page 1 of {len(pages)} (total {len(content)} characters)",
                'next_page_hint': f"To get next page, use: fetch_url(url='{url}', page_number=2) or get other pages by changing page_number parameter"
            }
        
        # Add metadata
        if 'metadata' in result:
            processed_result['metadata'] = result['metadata']
        if 'title' in result:
            processed_result['title'] = result['title']
        
        return processed_result
    
    async def _get_cached_page(self, url: str, page_number: int) -> Dict[str, Any]:
        """Get cached page content"""
        # Clean expired cache entries first
        self._cleanup_expired_cache()
        
        # Find matching cache entry for this URL
        for page_id, cached_data in self.page_cache.items():
            if cached_data.get('url') == url:
                pages = cached_data['pages']
                
                if page_number < 1 or page_number > len(pages):
                    return {
                        'success': False,
                        'error': f'Invalid page number, should be between 1-{len(pages)}',
                        'url': url
                    }
                
                page_content = pages[page_number - 1]
                
                return {
                    'success': True,
                    'url': url,
                    'content': page_content,
                    'current_page': page_number,
                    'total_pages': len(pages),
                    'page_info': f"Page {page_number} of {len(pages)}",
                    'is_paginated': True,
                    'page_id': page_id,
                    'metadata': cached_data.get('metadata', {})
                }
        
        # If no cache found, need to re-fetch
        return {
            'success': False,
            'error': f'Page cache not found for URL: {url}. Please fetch the URL first.',
            'url': url
        }
    
    def _split_content_into_pages(self, content: str, max_length: int) -> List[str]:
        """Intelligently split content into pages, preferring paragraph boundaries"""
        if len(content) <= max_length:
            return [content]
        
        pages = []
        current_page = ""
        
        # Split by paragraphs
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            # If current paragraph is too long, need to force split
            if len(paragraph) > max_length:
                # Save current page first
                if current_page:
                    pages.append(current_page.strip())
                    current_page = ""
                
                # Force split long paragraph
                for i in range(0, len(paragraph), max_length):
                    chunk = paragraph[i:i + max_length]
                    pages.append(chunk)
                continue
            
            # Check if adding current paragraph exceeds limit
            if len(current_page) + len(paragraph) + 2 > max_length:  # +2 for \n\n
                if current_page:
                    pages.append(current_page.strip())
                current_page = paragraph
            else:
                if current_page:
                    current_page += '\n\n' + paragraph
                else:
                    current_page = paragraph
        
        # Add last page
        if current_page:
            pages.append(current_page.strip())
        
        return pages
    
    def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        current_time = asyncio.get_event_loop().time()
        expired_keys = []
        
        for page_id, cached_data in self.page_cache.items():
            if current_time - cached_data.get('created_at', 0) > self.cache_ttl:
                expired_keys.append(page_id)
        
        for key in expired_keys:
            del self.page_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def clear_cache(self):
        """Clear page cache"""
        self.page_cache.clear()
        logger.info("Page cache cleared")
    
    async def search_jina(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search using Jina AI"""
        try:
            # If have API key and requesting more than 10 results, use premium API
            if self.jina_api_key and num_results > 10:
                return await self._jina_premium_search(query, num_results)
            else:
                return await self._jina_basic_search(query, num_results)
                
        except Exception as e:
            error_msg = f"Jina search failed: {str(e)}"
            logger.error(error_msg)
            return []
    
    async def _jina_basic_search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Basic Jina search (free version)"""
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
    
    async def _jina_premium_search(self, query: str, num_results: int = 30) -> List[Dict[str, Any]]:
        """Premium Jina search (requires API key)"""
        if not self.jina_api_key:
            raise Exception("Premium search requires Jina API key")
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.jina_api_key}'
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
