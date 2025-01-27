from flask import Flask, render_template, request, jsonify, url_for
import subprocess
import json
import shlex
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT'))

# Configure logging
from ai_agents.core.config import logger

# Now we can import from ai_agents
from ai_agents.core.config import BLOG_AGENT_TYPES, BLOG_AGENT_NAMES, PROJECT_ROOT, BLOG_RESEARCHER_AI_AGENT, BLOG_ARTIST_AI_AGENT  

app = Flask(__name__, static_url_path='/static')

def execute_generate_command(agent_type, agent_name, topic=None, image_prompt=None, webhook_url=None):
    """Execute the command using the Python deployment manager."""
    try:
        from deployment.deploy_manager import DeployManager, main as deploy_main
        
        # Get kwargs for main function
        kwargs = {
            'agent_type': agent_type,
            'agent_name': agent_name,
            'topic': topic,
            'image_prompt': image_prompt,
            'webhook_url': webhook_url
        }
        
        # Remove None values
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        # Run deployment process
        try:
            success, error_message = deploy_main(**kwargs)  # Assuming deploy_main now returns a tuple (success, error_message)
            if not success:
                return False, f"Deployment failed: {error_message}", None
        except Exception as deploy_error:
            return False, f"Deployment failed: Error during deployment process: {str(deploy_error)}", None
            
        # Get blog URL if successful
        if success:
            try:
                deploy_manager = DeployManager()
                success, blog_url, error = deploy_manager.get_latest_file()
                if success and blog_url:
                    return True, "Deployment completed successfully", blog_url
                return False, f"Deployment completed but couldn't get URL: {error}", None
            except Exception as url_error:
                return False, f"Deployment completed but failed to get blog URL: {str(url_error)}", None
            
        return False, "Deployment failed: Unknown error occurred during deployment", None
        
    except Exception as e:
        return False, f"Deployment system error: {str(e)}\nCheck if all required dependencies are installed and servers are running.", None

@app.route('/')
def index():
    return render_template('index.html', 
                         agent_types=BLOG_AGENT_TYPES,
                         agent_names=json.dumps(BLOG_AGENT_NAMES))

@app.route('/run-ngrok', methods=['POST'])
def run_ngrok():
    """Handle the NGROK server start request."""
    apple_script = '''
    tell application "Terminal"
        activate
        do script "ngrok http 9119"
    end tell
    '''
    
    subprocess.run(['osascript', '-e', apple_script])
    return "NGROK server started" 

@app.route('/run-midjourney', methods=['POST'])
def run_midjourney():
    """Handle the midjourney server start request."""
    
    apple_script = f'''
    tell application "Terminal"
        activate
        do script "cd {PROJECT_ROOT} && python blogi/ai_agents/utils/midjourney_webhook_server.py"
    end tell
    '''
    
    subprocess.run(['osascript', '-e', apple_script])
    return "Midjourney webhook server started" 

@app.route('/start_server', methods=['POST'])
def start_server():
    try:
        data = request.json
        command = data.get('command')
        if not command:
            return jsonify({'success': False, 'message': 'No command provided'})

        # Split the command safely
        args = shlex.split(command)

        # Start the process in the background
        subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        return jsonify({'success': True, 'message': f'Started {command}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        agent_type = data.get('agent_type')
        agent_name = data.get('agent_name')
        
        if agent_type == BLOG_RESEARCHER_AI_AGENT:
            topic = data.get('topic')
            if not topic:
                return jsonify({'success': False, 'message': 'Topic is required for researcher agent'})
            success, output, blog_url = execute_generate_command(agent_type, agent_name, topic=topic)
        elif agent_type == BLOG_ARTIST_AI_AGENT:
            webhook_url = data.get('webhook_url')
            if not webhook_url:
                return jsonify({'success': False, 'message': 'Webhook URL is required for artist agent'})
            
            image_prompt = data.get('image_prompt', None)
            success, output, blog_url = execute_generate_command(
                agent_type, 
                agent_name, 
                image_prompt=image_prompt,
                webhook_url=webhook_url
            )

        return jsonify({
            'success': success,
            'message': output,
            'blog_url': blog_url
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'blog_url': None
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9229, debug=True)