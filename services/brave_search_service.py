import os
import aiohttp
from typing import Optional, List, Dict, Any
import logging

# Configure logging
from blogi.core.config import logger

class BraveSearchClient:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Brave Search client with API key."""
        self.api_key = api_key or os.getenv('BRAVE_SEARCH_API_KEY')
        if not self.api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY not found in environment variables")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async def start(self):
        """Start an aiohttp session."""
        self.session = aiohttp.ClientSession(
            headers={
                'Accept': 'application/json',
                'X-Subscription-Token': self.api_key
            },
            timeout=self.timeout
        )

    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def search_topic(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Search for a topic using Brave Search API."""
        if not self.session:
            await self.start()
        try:
            params = {'q': query, 'count': count}
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('web', {}).get('results', [])
                return []
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []