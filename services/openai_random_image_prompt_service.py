#!/bin/python3

import os
import logging
from openai import AsyncOpenAI
from typing import Optional

# Configure logging
from blogi.core.config import logger, OPENAI_MODEL, MIDJOURNEY_ASPECT_RATIO

class OpenAIRandomImagePromptService:

    def __init__(self):
        # Use AsyncOpenAI instead of OpenAI
        self.client = AsyncOpenAI()  # No proxies argument

    async def generate_random_prompt(self) -> Optional[str]:
        """Generate a random image prompt using OpenAI.
        Returns:
            Optional[str]: The generated prompt or None if generation fails
        """
        try:
            key_words_response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{
                    "role": "system",
                    "content": "You are a creative image prompt generator."
                }, {
                    "role": "user",
                    "content": "Generate a creative and detailed image prompt for Midjourney."
                }]
            )

            key_words = key_words_response.choices[0].message.content

            payload = [
                {"role": "system", "content": "You are a helpful assistant. Help me generate an AI image prompt!"},
                {"role": "user", "content": f"create a detailed prompt of less than 30 words for these key words {key_words} returning only the prompt and no other text or quotation marks"}
            ]

            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=payload
            )

            random_prompt = response.choices[0].message.content

            # Add the aspect ratio to the random prompt
            random_prompt = f"{random_prompt} --ar {MIDJOURNEY_ASPECT_RATIO}"

            if random_prompt:
                return random_prompt
            return None
        except Exception as e:
            logger.error(f"Error generating random prompt: {str(e)}")
            return None
