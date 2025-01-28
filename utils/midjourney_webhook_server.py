from flask import Flask, request, jsonify
import logging
import hmac
import hashlib
import json
import os
import requests
import subprocess
from pathlib import Path
import sys
import datetime

from PIL import Image

# Add the parent directory of the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT.parent))

from blogi.core.config import setup_logging, logger, AI_BLOG_SITE_PATH, OBSIDIAN_NOTES_PATH
from blogi.deployment.ai_deployment_manager import AIDeployManager

app = Flask(__name__)
logger = setup_logging()

class MidjourneyWebhookHandler:
    def __init__(self):
        self.deploy_manager = AIDeployManager()
        self.processed_urls = set()  # Add cache for processed URLs

    def verify_signature(self, payload, signature, secret):
        """Verify the webhook signature"""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    def slice_and_save_images(self,
                              dated_ai_image_path,
                              ai_blog_site_images_path,
                              obsidian_ai_images_path,
                              image_timestamp):
        
        """Slices a 2048x2048 image into four 1024x1024 images and saves them."""
        try:
            img = Image.open(dated_ai_image_path)
            
            if img.size != (2048, 2048):
                logger.error(f"Image must be 2048x2048 pixels. Current size: {img.size}")
                return
            
            coordinates = [
                (0, 0, 1024, 1024),       # Top-left
                (1024, 0, 2048, 1024),    # Top-right
                (0, 1024, 1024, 2048),    # Bottom-left
                (1024, 1024, 2048, 2048)  # Bottom-right
            ]
            
            base_name = Path(dated_ai_image_path).stem
            positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
            
            for coords, position in zip(coordinates, positions):
                quadrant = img.crop(coords)
                
                # Save both dated and normal versions
                for filename in [
                    f"{base_name}_{image_timestamp}_{position}.png",
                    f"{base_name}_{position}.png"
                ]:
                    ai_output_path = Path(ai_blog_site_images_path) / filename
                    obsidian_output_path = Path(obsidian_ai_images_path) / filename
                    try:
                        quadrant.save(ai_output_path)
                        quadrant.save(obsidian_output_path)
                        logger.info(f"Saved: {ai_output_path}")
                        logger.info(f"Saved: {obsidian_output_path}")
                    except Exception as e:
                        logger.error(f"Error saving {ai_output_path}: {e}")
                        logger.error(f"Error saving {obsidian_output_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing image: {e}")

    def save_prompt_to_file(self, prompt, prompt_file_path):
        """Save the prompt to a file."""
        try:
            logger.info(f"Saving prompt to file: {prompt_file_path}")
            prompt_str = str(prompt) if prompt is not None else "No prompt available"
            Path(prompt_file_path).write_text(prompt_str)
        except Exception as e:
            logger.error(f"Error saving prompt to file: {e}")

    def download_image(self, image_url, download_path):
        """Download an image from a URL."""
        try:
            logger.info(f"Downloading image from: {image_url}")
            response = requests.get(image_url)
            response.raise_for_status()
            Path(download_path).write_bytes(response.content)
            logger.info("Image downloaded successfully")
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            raise

    def save_image_and_prompt(self, image_url, prompt):
        """Process and save the image and prompt."""
        try:

            image_timestamp = os.getenv('IMAGE_TIMESTAMP')
            ai_blog_site_images_path = AI_BLOG_SITE_PATH / 'static' / 'images'
            # Create directory if it doesn't exist
            ai_blog_site_images_path.mkdir(parents=True, exist_ok=True)

            obsidian_ai_images_path = OBSIDIAN_NOTES_PATH / 'ai_blog' / 'images'
            
            # Create paths for image and prompt
            dated_ai_image_path = ai_blog_site_images_path / f"{image_timestamp}.png"
            dated_ai_prompt_path = ai_blog_site_images_path / f"{image_timestamp}.md"
            dated_obsidian_image_path = obsidian_ai_images_path / f"{image_timestamp}.png"
            dated_obsidian_prompt_path = obsidian_ai_images_path / f"{image_timestamp}.md"
            
            # Save prompt and download image
            self.save_prompt_to_file(prompt, dated_ai_prompt_path)
            self.save_prompt_to_file(prompt, dated_obsidian_prompt_path)
            self.download_image(image_url, dated_ai_image_path)
            self.download_image(image_url, dated_obsidian_image_path)
            # Slice the image into quadrants
            self.slice_and_save_images(dated_ai_image_path,
                                       ai_blog_site_images_path,
                                       obsidian_ai_images_path,
                                       image_timestamp)
            # Run deployment process
            self.deploy_manager.build_hugo()
            self.deploy_manager.git_operations()
            
        except Exception as e:
            logger.error(f"Error in save_image_and_prompt: {e}")
            raise

    def has_been_processed(self, image_url):
        """Check if the image URL has already been processed"""
        return image_url in self.processed_urls

    def mark_as_processed(self, image_url):
        """Mark an image URL as processed"""
        self.processed_urls.add(image_url)

webhook_handler = MidjourneyWebhookHandler()

@app.route('/imagine/webhook', methods=['POST'])
def webhook_handler_route():
    try:
        payload = request.get_data().decode('utf-8')
        data = request.json
        logger.info(f"Received webhook data: {data}")
        
        if 'status' in data:
            if data['status'] == 'done':
                image_url = data.get('result', {}).get('url')
                prompt = data.get('prompt') or data.get('result', {}).get('prompt') or "No prompt available"
                
                if image_url:
                    # Check if we've already processed this URL
                    if webhook_handler.has_been_processed(image_url):
                        logger.info(f"Skipping already processed image: {image_url}")
                        return jsonify({'status': 'success', 'message': 'Already processed'}), 200

                    logger.info(f"QUAD Image generation completed. URL: {image_url}")
                    webhook_handler.save_image_and_prompt(image_url, prompt)
                    webhook_handler.mark_as_processed(image_url)  # Mark as processed after successful save
                    return jsonify({'status': 'success', 'image_url': image_url}), 200
                else:
                    logger.error("Image URL not found in response")
                    return jsonify({'status': 'error', 'message': 'Image URL not found'}), 400
                    
            elif data['status'] == 'failed':
                error = data.get('status_reason') or 'Unknown error'
                logger.error(f"Image generation failed: {error}")
                return jsonify({'status': 'error', 'message': error}), 400
        
        return jsonify({'status': 'received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9119)