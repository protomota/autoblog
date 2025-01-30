import os
import aiohttp
from typing import Optional, List, Dict, Any
from blogi.core.config import logger

class BraveSearchClient:
    def __init__(self):
        """Initialize the Brave Search client."""
        self.api_key = os.getenv('BRAVE_API_KEY')
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY not found in environment variables")
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a search using Brave Search API.
        Args:
            query (str): The search query
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            }
            params = {
                "q": query,
                "count": 10
            }

            async with self.session.get(self.base_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('web', {}).get('results', [])
                else:
                    logger.error(f"Brave Search API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error in Brave search: {str(e)}")
            return []

    async def cleanup(self):
        """Cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()