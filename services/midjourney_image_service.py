import requests
import time
import logging

# Configure logging
from blogi.core.config import logger, USERAPI_AI_API_BASE_URL

class MidjourneyImageService:
    # Add API base URL as a class constant

    def __init__(self, api_key, account_hash, prompt, webhook_url):
        self.api_key = api_key
        self.account_hash = account_hash
        self.prompt = prompt
        # Ensure webhook URL ends with /imagine/webhook
        self.webhook_url = webhook_url.rstrip('/') + '/imagine/webhook'
        logger.info(f"INIT MidjourneyImageService WITH WEBHOOK URL: {self.webhook_url}")
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def run_async(self):
        """
        Run the image generation service asynchronously
        
        Returns:
            str: URL of the generated image
            
        Raises:
            RuntimeError: If image generation fails
        """

        # Initialize generation request
        response = await self._generate_quad_image_async()

        logger.info(f"\n\n*********\n\n_generate_quad_image_async Response Body: {response}\n\n*********\n\n")

        if not response:
            raise RuntimeError("Failed to get response from image generation service")
        
        response_hash = response.get("hash")

        if not response_hash:
            raise RuntimeError("Failed to get response_hash from image generation response")
            
        logger.info(f"Image generation task initiated with hash: {response_hash}")

    async def _generate_quad_image_async(self):
        """Make the initial request to generate a QUAD image asynchronously"""
        
        logger.info(f"Make the initial request to generate a QUAD image WITH WEBHOOK URL: {self.webhook_url}")

        payload = {
            "prompt": self.prompt,
            "webhook_url": self.webhook_url,
            "webhook_type": "progress",
            "account_hash": self.account_hash,
            "is_disable_prefilter": True
        }
        logger.info(f"\n\n++++++++++++\n\npayload: {payload}\n\n++++++++++++\n\n")
        
        response = requests.post(
            f"{USERAPI_AI_API_BASE_URL}/imagine",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        logger.info(f"\n\n++++++++++++\n\nresponse: {response}\n\n++++++++++++\n\n")
        
        
        response.raise_for_status()
        return response.json()