import requests
import json
import argparse

def test_webhook(webhook_url, image_url):
    # Ensure the webhook URL ends with '/imagine/webhook'
    if not webhook_url.endswith('/imagine/webhook'):
        webhook_url = webhook_url.rstrip('/') + '/imagine/webhook'
    
    # Simulate a successful completion webhook
    test_payload = {
        "status": "done",
        "result": {
            "url": image_url,
            "prompt": "test prompt for midjourney image"
        },
        "prompt": "test prompt for midjourney image"
    }
    
    # Send POST request
    try:
        response = requests.post(webhook_url, json=test_payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    DEFAULT_WEBHOOK_URL = 'http://localhost:9119/imagine/webhook'
    DEFAULT_IMAGE_URL = 'https://placehold.co/2048x2048/png'

    parser = argparse.ArgumentParser(description='Test webhook with custom URL')
    parser.add_argument('--webhook_url', 
                       default=DEFAULT_WEBHOOK_URL,
                       help=f'Webhook URL to send test request (default: {DEFAULT_WEBHOOK_URL})')
    parser.add_argument('--image_url', 
                       default=DEFAULT_IMAGE_URL,
                       help=f'Image URL to send test request (default: {DEFAULT_IMAGE_URL})')
    args = parser.parse_args()
    test_webhook(args.webhook_url, args.image_url)