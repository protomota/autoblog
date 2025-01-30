from datetime import datetime
from typing import Optional
import os
from pathlib import Path
import aiohttp

from blogi.services.midjourney_image_service import MidjourneyImageService

# Configuration
from blogi.core.config import logger, PROMPTS_DIR

class ProcessImageService:

    def __init__(self, agent_name: str, image_prompt: str, webhook_url: str):
            try:
                self.webhook_url = webhook_url

                # AI Agent prompts and templates
                self.agent_prompt_path = PROMPTS_DIR / agent_name / "agent_prompt.txt"
                self.enhanced_prompt_path = PROMPTS_DIR / agent_name / "enhanced_prompt.txt"
                self.disclaimer_path = PROMPTS_DIR / agent_name / "disclaimer.txt"
                
                self.image_prompt = image_prompt

                # Verify paths exist
                for path in [self.agent_prompt_path, self.enhanced_prompt_path, self.disclaimer_path]:
                    if not os.path.exists(path):
                        raise FileNotFoundError(f"Required prompt file not found: {path}")

                self._get_image_and_description()
            except Exception as e:
                logger.error(f"ProcessImageService initialization error: {str(e)}")
                raise

    def _get_image_and_description(self):
        try:
            logger.info("Initializing OpenAIRandomImagePromptService")

            # Get environment variables
            api_key = os.environ.get("USERAPI_AI_API_KEY")
            account_hash = os.environ.get("USERAPI_AI_ACCOUNT_HASH")

            if not api_key or not account_hash:
                raise ValueError("Missing required environment variables for image service")

            # Run the service
            midjourney_service = MidjourneyImageService(api_key=api_key, account_hash=account_hash, prompt=self.image_prompt, webhook_url=self.webhook_url)
            midjourney_service.run()
        except Exception as e:
            logger.error(f"Error in _get_image_and_description: {str(e)}")
            raise

    def __init__(self):
        """Initialize the image processing service."""
        self.session: Optional[aiohttp.ClientSession] = None

    async def setup(self):
        """Set up the service session."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def process_image(self, image_url: str) -> Optional[str]:
        """Process an image from the given URL.
        Args:
            image_url (str): The URL of the image to process
        Returns:
            Optional[str]: The processed image data or None if processing fails
        """
        if not self.session:
            await self.setup()

        try:
            async with self.session.get(image_url) as response:
                if response.status == 200:
                    return await response.text()
                logger.error(f"HTTP error {response.status} for image URL: {image_url}")
                return None
        except Exception as e:
            logger.error(f"Error processing image from {image_url}: {str(e)}")
            return None

    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()