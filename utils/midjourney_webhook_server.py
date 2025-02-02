from flask import Flask, request, jsonify
import hmac
import hashlib
import os
import requests
from pathlib import Path
import sys
from datetime import datetime

from PIL import Image

# Add the parent directory of the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT.parent))

# Configuration
from blogi.core.config import (
    setup_logging, 
    logger, 
    BLOG_SITE_STATIC_IMAGES_PATH, 
    OBSIDIAN_AI_IMAGES
)

app = Flask(__name__)
logger = setup_logging()

class MidjourneyWebhookHandler:
    def __init__(self):
        self.processed_urls = set()  # Add cache for processed URLs

    def verify_signature(self, payload, signature, secret):
        """Verify the webhook signature"""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    def slice_and_save_images(self, dated_ai_image_path):
        """Slices an image into four equal-sized quadrants and creates thumbnails."""
        try:
            logger.info(f"Slicing and saving images for dated_ai_image_path: {dated_ai_image_path}")

            img = Image.open(dated_ai_image_path)
            width, height = img.size
            
            # Calculate dimensions for each quadrant
            quad_width = width // 2
            quad_height = height // 2
            
            coordinates = [
                (0, 0, quad_width, quad_height),                    # Top-left
                (quad_width, 0, width, quad_height),                # Top-right
                (0, quad_height, quad_width, height),               # Bottom-left
                (quad_width, quad_height, width, height)            # Bottom-right
            ]
            
            base_name = Path(dated_ai_image_path).stem
            positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
            
            for coords, position in zip(coordinates, positions):
                quadrant = img.crop(coords)
                
                # Save full-size quadrant
                filename = f"{base_name}_{position}.png"
                obsidian_output_path = OBSIDIAN_AI_IMAGES / filename
                try:
                    quadrant.save(obsidian_output_path)
                    logger.info(f"Saved full-size: {obsidian_output_path}")
                    
                    # Create and save thumbnail (25% size)
                    thumb_size = (quadrant.width // 4, quadrant.height // 4)
                    thumbnail = quadrant.resize(thumb_size, Image.Resampling.LANCZOS)
                    thumb_filename = f"{base_name}_{position}_thumb.png"
                    thumb_path = OBSIDIAN_AI_IMAGES / thumb_filename
                    thumbnail.save(thumb_path)
                    logger.info(f"Saved thumbnail: {thumb_path}")
                        
                except Exception as e:
                    logger.error(f"Error saving {obsidian_output_path}: {e}")
            
            # Close the image before deleting
            img.close()
            # Delete the original image
            Path(dated_ai_image_path).unlink()
            logger.info(f"Deleted original image: {dated_ai_image_path}")
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

    def save_image_and_prompt(self, image_url, prompt, image_timestamp):
        """Process and save the image and prompt."""
        try:
            logger.info(f"Saving image and prompt for timestamp: {image_timestamp}")
            # Create directories if they don't exist
            BLOG_SITE_STATIC_IMAGES_PATH.mkdir(parents=True, exist_ok=True)
            if OBSIDIAN_AI_IMAGES:
                OBSIDIAN_AI_IMAGES.mkdir(parents=True, exist_ok=True)
            
            # Setup paths and save files
            dated_obsidian_paths = {
                'image': OBSIDIAN_AI_IMAGES / f"midjourney_{image_timestamp}.png",
                'prompt': OBSIDIAN_AI_IMAGES / f"midjourney_{image_timestamp}.md"
            }

            self.save_prompt_to_file(prompt, dated_obsidian_paths['prompt'])
            self.download_image(image_url, dated_obsidian_paths['image'])
            
            # Slice the image into quadrants
            self.slice_and_save_images(dated_obsidian_paths['image'])
            
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
        data = request.json
        logger.info(f"Received webhook data: {data}")
        
        if 'status' in data:
            if data['status'] == 'done':
                image_url = data.get('result', {}).get('url')
                prompt = data.get('prompt') or data.get('result', {}).get('prompt') or "No prompt available"
                # Get timestamp from URL query parameter instead of payload
                image_timestamp = request.args.get('image_timestamp') or "0000000000"

                if image_url:
                    # Check if we've already processed this URL
                    if webhook_handler.has_been_processed(image_url):
                        logger.info(f"Skipping already processed image: {image_url}")
                        return jsonify({'status': 'success', 'message': 'Already processed'}), 200
                    
                    logger.info(f"QUAD Image generation completed. URL: {image_url}")
                    logger.info(f"Using image timestamp: {image_timestamp}")
                    webhook_handler.save_image_and_prompt(image_url, prompt, image_timestamp)
                    webhook_handler.mark_as_processed(image_url)
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