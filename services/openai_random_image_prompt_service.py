#!/bin/python3

import os
import logging
from openai import OpenAI
from typing import Optional

# Configure logging
from blogi.core.config import logger

class OpenAIRandomImagePromptService:

    def __init__(self):
        # Initialize OpenAI client without proxies
        self.client = OpenAI()  # This will use OPENAI_API_KEY from environment

    async def generate_random_prompt(self) -> Optional[str]:
        """Generate a random image prompt using OpenAI.
        Returns:
            Optional[str]: The generated prompt or None if generation fails
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are a creative image prompt generator."
                }, {
                    "role": "user",
                    "content": "Generate a creative and detailed image prompt for Midjourney."
                }]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating random prompt: {str(e)}")
            return None
