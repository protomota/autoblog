import aiohttp
import logging
import re
from typing import Optional
from bs4 import BeautifulSoup

# Configure logging
from ai_agents.core.config import logger

class WebService:
    def __init__(self):
        self.session = None

    async def fetch_webpage_content(self, url: str) -> Optional[str]:
        """Fetch and extract main content from a webpage."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Clean up the HTML
                    for element in soup(["script", "style", "nav", "header", "footer"]):
                        element.decompose()
                    
                    # Extract main content
                    main_content = (
                        soup.find('main') or 
                        soup.find('article') or 
                        soup.find('div', class_=re.compile(r'content|article|post'))
                    )
                    
                    text = (main_content or soup).get_text(separator=' ', strip=True)
                    return re.sub(r'\s+', ' ', text)[:10000]
        except Exception as e:
            logger.error(f"Error fetching webpage {url}: {str(e)}")
            return None 