import requests
import time
import logging

# Configure logging
from blogi.core.config import logger

class MidjourneyImageService:
    # Add API base URL as a class constant
    API_BASE_URL = "https://api.userapi.ai/midjourney/v2"

    def __init__(self, api_key, account_hash, prompt, webhook_url):
        self.api_key = api_key
        self.account_hash = account_hash
        self.prompt = prompt
        self.webhook_url = webhook_url

        if not webhook_url.endswith('/imagine/webhook'):
            self.webhook_url = webhook_url.rstrip('/') + '/imagine/webhook'

        logger.info(f"INIT MidjourneyImageService WITH WEBHOOK URL: {webhook_url}")
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _generate_quad_image(self):
        """Make the initial request to generate a QUAD image"""
        
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
            f"{self.API_BASE_URL}/imagine",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()

    def run(self):
        """
        Run the image generation service
        
        Returns:
            str: URL of the generated image
            
        Raises:
            RuntimeError: If image generation fails
        """
        # Initialize generation request
        response = self._generate_quad_image()

        logger.info(f"\n\n*********\n\n_generate_quad_image Response Body: {response}\n\n*********\n\n")

        if not response:
            raise RuntimeError("Failed to get response from image generation service")
        
        response_hash = response.get("hash")

        if not response_hash:
            raise RuntimeError("Failed to get response_hash from image generation response")
            
        logger.info(f"Image generation task initiated with hash: {response_hash}")

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
            f"{self.API_BASE_URL}/imagine",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()