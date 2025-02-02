import os
import sys
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import requests
import markdown
import frontmatter
import json
from datetime import datetime
import atexit
import signal

# Get the absolute path to the project root (protomota directory)
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])  # Go up 3 levels: admin -> blogi -> protomota

# Add project root to PYTHONPATH and sys.path
os.environ['PYTHONPATH'] = PROJECT_ROOT
sys.path.insert(0, PROJECT_ROOT)

# Now import Flask and other standard libraries
from flask import Flask, render_template, request, jsonify, url_for
import subprocess
import shlex

# Configuration
from blogi.core.config import (
    logger,
    BLOG_AGENT_TYPES, 
    BLOG_AGENT_NAMES,
    BLOG_RESEARCHER_AI_AGENT, 
    BLOG_ARTIST_AI_AGENT,
    chaos_percentage_manager,
    OBSIDIAN_AI_POSTS_PATH,
    ELEVENLABS_API_KEY
)
from blogi.core.agent import BlogAgent
from blogi.core.deployment import DeploymentManager

app = Flask(__name__, static_url_path='/static')

executor = ThreadPoolExecutor(max_workers=3)

# Add logging at application startup
logger.info("=== Application Initialization Started ===")
logger.info(f"Project root path: {PROJECT_ROOT}")
logger.info(f"Python path: {os.environ['PYTHONPATH']}")
logger.info("Loading Flask application and dependencies...")

# Add this near the top with other config imports

async def execute_generate_command(agent_type, agent_name, topic=None, image_prompt=None, webhook_url=None, chaos_percentage="0"):
    """Execute the command using the BlogAgent directly."""
    logger.info("\n=== New Generation Command Started ===")
    logger.info(f"Parameters received:")
    logger.info(f"  - Agent Type: {agent_type}")
    logger.info(f"  - Agent Name: {agent_name}")
    logger.info(f"  - Topic: {topic}")
    logger.info(f"  - Image Prompt: {image_prompt}")
    logger.info(f"  - Webhook URL: {webhook_url}")
    logger.info(f"  - Chaos Percentage: {chaos_percentage}")
    
    try:
        # Update the chaos percentage manager
        chaos_percentage_manager.update(chaos_percentage)
        
        # Explicitly catch the return values from BlogAgent.create
        try:
            success, message, filepath, filename = await BlogAgent.create(
                agent_type=agent_type,
                agent_name=agent_name,
                topic=topic,
                image_prompt=image_prompt,
                webhook_url=webhook_url
            )
        except Exception as e:
            # If BlogAgent.create fails to return proper tuple
            logger.error(f"Error in BlogAgent.create: {str(e)}")
            return False, str(e), None, None
        
        if not success:
            logger.error(f"Blog generation failed: {message}")
            return False, message, None, None
            
        # Extract filename from filepath if it exists
        filename = Path(filepath).name if filepath else None
            
        logger.info(f"execute_generate_command Command execution completed - Success: {success}, Output: {message}, Filename: {filename}, Filepath: {filepath}")
        return success, message, filepath, filename
            
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(f"Error in generate command: {error_message}")
        return False, error_message, None, None

@app.route('/')
def index():
    logger.info("Index page requested")
    return render_template('index.html', 
                         agent_types=BLOG_AGENT_TYPES,
                         agent_names=json.dumps(BLOG_AGENT_NAMES))

@app.route('/run-ngrok', methods=['POST'])
def run_ngrok():
    """Handle the NGROK server start request."""
    logger.info("Starting NGROK server")
    apple_script = '''
    tell application "Terminal"
        activate
        do script "ngrok http 9119"
    end tell
    '''
    
    try:
        subprocess.run(['osascript', '-e', apple_script])
        logger.info("NGROK server start command executed successfully")
        return "NGROK server started"
    except Exception as e:
        logger.error(f"Failed to start NGROK server: {str(e)}", exc_info=True)
        return f"Failed to start NGROK server: {str(e)}"

@app.route('/run-midjourney', methods=['POST'])
def run_midjourney():
    """Handle the midjourney server start request."""
    logger.info("Starting Midjourney webhook server")
    
    apple_script = f'''
    tell application "Terminal"
        activate
        do script "source {PROJECT_ROOT}/venv/bin/activate && python {PROJECT_ROOT}/blogi/utils/midjourney_webhook_server.py"
    end tell
    '''
    
    try:
        subprocess.run(['osascript', '-e', apple_script])
        logger.info("Midjourney webhook server start command executed successfully")
        return "Midjourney webhook server started"
    except Exception as e:
        logger.error(f"Failed to start Midjourney webhook server: {str(e)}", exc_info=True)
        return f"Failed to start Midjourney webhook server: {str(e)}"

@app.route('/start_server', methods=['POST'])
def start_server():
    logger.info("Start server endpoint called")
    try:
        data = request.json
        command = data.get('command')
        logger.info(f"Received command: {command}")
        
        if not command:
            logger.error("No command provided")
            return jsonify({'success': False, 'message': 'No command provided'})

        # Split the command safely
        args = shlex.split(command)
        logger.info(f"Executing command with args: {args}")

        # Start the process in the background
        subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        logger.info(f"Successfully started process: {command}")
        return jsonify({'success': True, 'message': f'Started {command}'})
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)})

@app.route('/generate', methods=['POST'])
async def generate():
    try:
        logger.info("Generate endpoint called")
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        agent_type = data.get('agent_type')
        agent_name = data.get('agent_name')
        logger.info(f"Agent type: {agent_type}, Agent name: {agent_name}")
        
        if agent_type == BLOG_RESEARCHER_AI_AGENT:
            topic = data.get('topic')
            if not topic:
                logger.error("Topic is required for researcher agent but was not provided")
                return jsonify({'success': False, 'message': 'Topic is required for researcher agent'})
            logger.info(f"Executing researcher command with topic: {topic}")
            success, output, filepath, filename = await execute_generate_command(agent_type, agent_name, topic=topic)
        elif agent_type == BLOG_ARTIST_AI_AGENT:
            webhook_url = data.get('webhook_url')
            if not webhook_url:
                logger.error("Webhook URL is required for artist agent but was not provided")
                return jsonify({'success': False, 'message': 'Webhook URL is required for artist agent'})
            
            image_prompt = data.get('image_prompt', None)
            chaos_percentage = data.get('chaos_percentage', "0")
            
            # Update the global chaos percentage
            chaos_percentage_manager.update(chaos_percentage)
            
            logger.info(f"Executing artist command with prompt: {image_prompt}, webhook: {webhook_url}, chaos: {chaos_percentage}")
            success, output, filepath, filename = await execute_generate_command(
                agent_type, 
                agent_name, 
                image_prompt=image_prompt,
                webhook_url=webhook_url,
                chaos_percentage=chaos_percentage
            )

        logger.info(f"generate Command execution completed - Success: {success}, Output: {output}, Filename: {filename}, Filepath: {filepath}")
        return jsonify({
            'success': success,
            'message': output,
            'filepath': filepath,
            'filename': filename
        })
    except Exception as e:
        logger.error(f"Error in generate endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'filepath': None,
            'filename': None
        })

@app.route('/deploy', methods=['POST'])
async def deploy():
    """Handle blog deployment."""
    logger.info("Deploy endpoint called")
    try:
        deploy_manager = DeploymentManager()
        
        # Run deployment process
        if not all([
            deploy_manager.sync_content(),
            deploy_manager.sync_images()
        ]):
            return jsonify({
                'success': False,
                'message': 'Failed to sync content and images'
            })

        if deploy_manager.changes_made:
            if all([
                deploy_manager.build_hugo(deploy_manager.blog_site_path),
                deploy_manager.git_operations(deploy_manager.blog_site_path)
            ]):
                return jsonify({
                    'success': True,
                    'message': 'Deployment completed successfully!'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to build and deploy'
                })
        else:
            return jsonify({
                'success': True,
                'message': 'No changes detected - skipping deployment'
            })
            
    except Exception as e:
        logger.error(f"Error in deploy endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Deployment error: {str(e)}'
        })

@app.route('/generate-voice', methods=['POST'])
async def generate_voice():
    """Handle voice over generation."""
    logger.info("\n=== Voice Over Generation Started ===")
    try:
        # Get the filename from the request
        data = request.get_json()
        original_filename = data.get('filename', '')
        logger.info(f"Original blog post filename: {original_filename}")
        
        # Load content from config file
        config_path = Path('tmp/config.json')
        logger.info(f"Looking for config file at: {config_path} (absolute: {config_path.absolute()})")
        
        if not config_path.exists():
            logger.error(f"Config file not found at: {config_path}")
            return jsonify({
                'success': False,
                'message': 'Config file not found. Please generate a blog post first.'
            })

        # Read the config file
        try:
            logger.info("Reading config file...")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            text = config_data.get('blog_content')
            if not text:
                logger.error("No blog content found in config file")
                return jsonify({
                    'success': False,
                    'message': 'No blog content found in config file'
                })
            
            logger.info(f"Successfully loaded blog content (length: {len(text)} characters)")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Failed to parse config file'
            })
        
        # Clean up the text
        logger.info("Processing text for voice generation...")
        text = ' '.join(text.split())  # Clean up whitespace
        logger.info(f"Processed text length: {len(text)} characters")
        
        # Call ElevenLabs API
        logger.info("Preparing ElevenLabs API call...")
        url = "https://api.elevenlabs.io/v1/text-to-speech/qNkzaJoHLLdpvgh5tISm"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        logger.info("Making request to ElevenLabs API...")
        response = requests.post(url, json=data, headers=headers)
        logger.info(f"ElevenLabs API response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"ElevenLabs API error response: {response.text}")
            return jsonify({
                'success': False,
                'message': f'ElevenLabs API error: {response.text}'
            })

        # Ensure the output directory exists
        output_dir = Path(OBSIDIAN_AI_POSTS_PATH)
        logger.info(f"Creating output directory if needed: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename based on original blog post name
        audio_filename = original_filename.replace('.md', '_voice.mp3')
        output_path = output_dir / audio_filename
        logger.info(f"Saving audio file to: {output_path}")
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Audio file saved successfully. Size: {len(response.content)} bytes")
        logger.info("=== Voice Over Generation Completed Successfully ===")
            
        return jsonify({
            'success': True,
            'message': f'Voice over generated successfully: {audio_filename}',
            'audio_path': str(output_path)
        })
            
    except Exception as e:
        logger.error("=== Voice Over Generation Failed ===")
        logger.error(f"Error in generate-voice endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Voice generation error: {str(e)}'
        })

async def cleanup():
    """Cleanup function to properly close async resources."""
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Get the current event loop
    loop = asyncio.get_event_loop()
    
    # Close the loop
    if not loop.is_closed():
        loop.stop()

def signal_handler(signame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signame}")
    # Run cleanup
    loop = asyncio.get_event_loop()
    if not loop.is_closed():
        loop.run_until_complete(cleanup())

if __name__ == '__main__':
    logger.info("\n=== Starting Application Server ===")
    logger.info("Importing Hypercorn dependencies...")
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: signal_handler(s))

    # Register cleanup on exit
    atexit.register(lambda: asyncio.get_event_loop().run_until_complete(cleanup()))

    logger.info("Configuring Hypercorn...")
    config = Config()
    config.bind = ["0.0.0.0:9229"]
    config.use_reloader = True
    
    logger.info(f"Server configuration:")
    logger.info(f"  - Bind address: {config.bind}")
    logger.info(f"  - Reloader enabled: {config.use_reloader}")
    logger.info("Starting server...")
    
    try:
        asyncio.run(serve(app, config))
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
    finally:
        # Ensure cleanup runs
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.run_until_complete(cleanup())