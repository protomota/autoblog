from anthropic import AsyncAnthropic
from typing import Optional
import logging
import os
import aiohttp

# Configure logging
from blogi.core.config import logger

class AnthropicService:
    def __init__(self, model: str):
        """Initialize the Anthropic service.
        Args:
            model (str): The model to use for completions
        """
        self.model = model
        # Initialize AsyncAnthropic without proxies
        self.client = AsyncAnthropic()
        self.session = None
        self._is_closed = False

    async def ask(self, prompt: str) -> str:
        """Send a prompt to the Anthropic API and get a response.
        Args:
            prompt (str): The prompt to send
        Returns:
            str: The response from the API
        """
        if self._is_closed:
            raise RuntimeError("Service has been closed")
            
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error in Anthropic API call: {str(e)}")
            return ""

    async def cleanup(self):
        """Cleanup resources."""
        if self._is_closed:
            return
            
        try:
            if self.session and not self.session.closed:
                await self.session.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            self._is_closed = True
            self.session = None
            self.client = None
