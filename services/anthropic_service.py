import anthropic
from anthropic import AI_PROMPT, HUMAN_PROMPT
import aiohttp
from typing import Optional
import logging
import os
from blogi.core.config import logger

class AnthropicService:
    def __init__(self, model: str):
        """Initialize the Anthropic service.
        Args:
            model (str): The model to use for completions
        """
        self.model = model
        self.client = anthropic.AsyncAnthropic()
        self.session = None
        self._is_closed = False

    async def ask(self, prompt: str) -> str:
        """Send a prompt to the Anthropic API using the Messages API."""
        if self._is_closed:
            raise RuntimeError("Service has been closed")

        try:
            response = await self.client.messages.create(
                model=self.model,
                system="You are a helpful assistant.",
                messages=[
                    {"role": "user", "content": prompt.strip()},
                ],
                max_tokens=300
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
