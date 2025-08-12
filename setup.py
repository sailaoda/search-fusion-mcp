#!/usr/bin/env python

"""
Search Fusion MCP Server - 设置文件
高可用多引擎搜索聚合MCP服务器
"""

from setuptools import setup, find_packages
import os
import sys

# 确保使用UTF-8编码
if sys.version_info < (3, 8):
    sys.exit("Python 3.8+ is required")

# 读取README文件
def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

# 读取requirements
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="search-fusion-mcp",
    version="1.0.0",
    author="sailaoda",
    author_email="wuyesai@gmail.com",
    description="🔍 High-Availability Multi-Engine Search Aggregation MCP Server",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/sailaoda/search-fusion-mcp",
    project_urls={
        "Bug Tracker": "https://github.com/sailaoda/search-fusion-mcp/issues",
        "Documentation": "https://github.com/sailaoda/search-fusion-mcp/blob/main/README.md",
        "Source Code": "https://github.com/sailaoda/search-fusion-mcp",
    },
    packages=find_packages(),
    package_dir={},
    include_package_data=True,
    package_data={
        "": [
            "*.md",
            "requirements.txt",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Indexing",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "search-fusion-mcp=src.main:main",
        ],
    },
    keywords=[
        "mcp", "search", "aggregation", "ai", "llm", "jina", "google", "serper",
        "duckduckgo", "bing", "baidu", "exa", "wikipedia", "web-scraping",
        "high-availability", "failover", "multi-engine"
    ],
    zip_safe=False,
)