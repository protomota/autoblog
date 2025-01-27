#!/bin/python3

import openai
import os
import logging

# Configure logging
from ai_agents.core.config import logger

class OpenAIRandomImagePromptService:

    def generate_random_image_prompt(self) -> str:
        MODEL = "gpt-4"
        api_key = os.environ.get("OPENAI_API_KEY")
        openai.api_key = api_key

        key_words_response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Help me generate 5 random words"},
                {"role": "user", "content": "list the words in a comma delimited list"}
            ]
        )

        key_words = key_words_response.choices[0].message.content

        payload = [
            {"role": "system", "content": "You are a helpful assistant. Help me generate an AI image prompt!"},
            {"role": "user", "content": f"create a detailed prompt of less than 30 words for these key words {key_words} returning only the prompt and no other text or quotation marks"}
        ]

        response = openai.chat.completions.create(
            model=MODEL,
            messages=payload
        )

        # Clean the response string by removing any surrounding quotes and extra whitespace
        prompt = response.choices[0].message.content
        prompt = prompt.strip()  # Remove leading/trailing whitespace
        prompt = prompt.strip('"\'')  # Remove any surrounding single or double quotes

        return prompt
