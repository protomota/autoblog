from datetime import datetime
from typing import Optional
import os
import logging
from pathlib import Path

from services.midjourney_image_service import MidjourneyImageService

# Configure logging
from ai_agents.core.config import logger

class ProcessImageService:

    def __init__(self, agent_name: str, image_prompt: str, webhook_url: str):
            try:
                self.webhook_url = webhook_url
                current_dir = os.path.dirname(os.path.abspath(__file__))

                parent_dir = os.path.dirname(current_dir)

                # AI Agent prompts and templates
                self.agent_prompt_path = os.path.join(parent_dir, f"prompts/{agent_name}/", "agent_prompt.txt")
                self.enhanced_prompt_path = os.path.join(parent_dir, f"prompts/{agent_name}/", "enhanced_prompt.txt")
                self.disclaimer_path = os.path.join(parent_dir, f"prompts/{agent_name}/", "disclaimer.txt")
                
                self.image_prompt = image_prompt

                # Verify paths exist
                for path in [self.agent_prompt_path, self.enhanced_prompt_path, self.disclaimer_path]:
                    if not os.path.exists(path):
                        raise FileNotFoundError(f"Required prompt file not found: {path}")

                self._get_image_and_description()
            except Exception as e:
                logger.error(f"ProcessImageService initialization error: {str(e)}")
                raise

    def generate_images(self, prompt: str) -> dict:
        current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return {
            'top_left': f"/images/openmid/openmid_{current_timestamp}_top_left.png",
            'top_right': f"/images/openmid/openmid_{current_timestamp}_top_right.png",
            'bottom_left': f"/images/openmid/openmid_{current_timestamp}_bottom_left.png",
            'bottom_right': f"/images/openmid/openmid_{current_timestamp}_bottom_right.png"
        }

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