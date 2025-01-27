import anthropic
from typing import Optional
import logging
import os
import aiohttp

# Configure logging
from blogi.core.config import logger

class AnthropicService:
    def __init__(self, model: str):
        self.model = model
        self.client = anthropic.Anthropic()
        self.session = None
        self._is_closed = False

    async def ask(self, prompt: str) -> Optional[str]:
        """Send a prompt to Claude and get a response."""
        if self._is_closed:
            raise RuntimeError("Service has been closed")
            
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            if message and message.content:
                return message.content[0].text
            return None
        except Exception as e:
            logger.error(f"Error in AnthropicService.ask: {str(e)}")
            return None

    async def cleanup(self):
        """Cleanup any resources."""
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
