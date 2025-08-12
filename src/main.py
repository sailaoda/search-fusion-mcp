#!/usr/bin/env python

"""
Search Fusion MCP Server - Main entry point
Maintains backward compatibility while using new server architecture
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import SearchFusionServer


def main():
    """Main entry point - start Search Fusion MCP Server"""
    server = SearchFusionServer()
    server.run()


if __name__ == "__main__":
    main()
