import anthropic
from anthropic import HUMAN_PROMPT, AI_PROMPT
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
        """Send a prompt to the Anthropic API and get a response.
        Args:
            prompt (str): The prompt to send
        Returns:
            str: The response from the API
        """
        if self._is_closed:
            raise RuntimeError("Service has been closed")
            
        # Wrap user prompt so it starts with the correct token.
        anthropic_prompt = f"{HUMAN_PROMPT} {prompt.strip()} {AI_PROMPT}"
        
        try:
            response = await self.client.completions.create(
                model=self.model,
                prompt=anthropic_prompt,
                max_tokens_to_sample=300
            )
            return response.completion
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
