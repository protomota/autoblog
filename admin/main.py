import os
import sys
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# Get the absolute path to the project root (protomota directory)
PROJECT_ROOT = str(Path(__file__).resolve().parents[2])  # Go up 3 levels: admin -> blogi -> protomota

# Add project root to PYTHONPATH and sys.path
os.environ['PYTHONPATH'] = PROJECT_ROOT
sys.path.insert(0, PROJECT_ROOT)

# Now import Flask and other standard libraries
from flask import Flask, render_template, request, jsonify, url_for
import subprocess
import json
import shlex

# Configuration
from blogi.core.config import (
    logger,
    BLOG_AGENT_TYPES, 
    BLOG_AGENT_NAMES,
    BLOG_RESEARCHER_AI_AGENT, 
    BLOG_ARTIST_AI_AGENT,
    chaos_percentage_manager
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
                # Remove chaos_percentage from here since we're using the manager
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
    """Handle deployment request."""
    logger.info("\n=== Starting Deployment Process ===")
    
    try:
        deploy_manager = DeploymentManager()
        logger.info("Initialized DeploymentManager")
        
        # Sync content and images
        if not deploy_manager.sync_content():
            logger.error("Content sync failed")
            return jsonify({
                'success': False,
                'message': 'Content synchronization failed',
                'details': 'Check server logs for more information'
            })
            
        if not deploy_manager.sync_images():
            logger.error("Image sync failed")
            return jsonify({
                'success': False,
                'message': 'Image synchronization failed',
                'details': 'Check server logs for more information'
            })
            
        # If changes were made, build and deploy
        if deploy_manager.changes_made:
            logger.info("Changes detected, proceeding with build and deployment")
            
            if not deploy_manager.build_hugo(deploy_manager.blog_site_path):
                logger.error("Hugo build failed")
                return jsonify({
                    'success': False,
                    'message': 'Hugo build failed',
                    'details': 'Failed to build the static site'
                })
                
            if not deploy_manager.git_operations(deploy_manager.blog_site_path):
                logger.error("Git operations failed")
                return jsonify({
                    'success': False,
                    'message': 'Git operations failed',
                    'details': 'Failed to commit and push changes'
                })
                
            logger.info("Deployment completed successfully")
            return jsonify({
                'success': True,
                'message': 'Deployment completed successfully',
                'details': 'All changes have been published to the blog'
            })
        else:
            logger.info("No changes detected")
            return jsonify({
                'success': True,
                'message': 'No changes to deploy',
                'details': 'All content is already up to date'
            })
            
    except Exception as e:
        logger.error(f"Deployment failed with error: {str(e)}")
        logger.exception("Detailed error trace:")
        return jsonify({
            'success': False,
            'message': f'Deployment failed: {str(e)}',
            'details': 'An unexpected error occurred during deployment'
        })

if __name__ == '__main__':
    logger.info("\n=== Starting Application Server ===")
    logger.info("Importing Hypercorn dependencies...")
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    logger.info("Configuring Hypercorn...")
    config = Config()
    config.bind = ["0.0.0.0:9229"]
    config.use_reloader = True
    
    logger.info(f"Server configuration:")
    logger.info(f"  - Bind address: {config.bind}")
    logger.info(f"  - Reloader enabled: {config.use_reloader}")
    logger.info("Starting server...")
    
    asyncio.run(serve(app, config))