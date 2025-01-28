import os
import sys
import subprocess
import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple
from blogi.core.config import PROJECT_ROOT, AI_BLOG_URL
from .base_deployment_manager import BaseDeployManager

class AIDeployManager(BaseDeployManager):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIDeployManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        super().__init__()
        self.project_root = PROJECT_ROOT
        self.ai_blog_site_path = PROJECT_ROOT / "ai_blog"
        self.source_path = self.ai_blog_site_path / 'content' / 'posts'
        self.post_file_path = None
        self.blog_url_base = AI_BLOG_URL
        self._initialized = True

def main(agent_type: str, agent_name: str, **kwargs):
    """Main entry point for deployment process."""
    deploy_manager = AIDeployManager()
    
    # Run the AI agent
    python_script = deploy_manager.project_root / 'agent' / 'main.py'
    cmd = [sys.executable, str(python_script), '--agent_type', agent_type, '--agent_name', agent_name]
    
    # Add additional arguments based on agent type
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend([f'--{key}', value])
    
    success, output = deploy_manager.run_command(cmd)
    if not success:
        error_msg = f"AI agent execution failed: {output}"
        deploy_manager.logger.error(error_msg)
        return False, error_msg
    
    # Extract file path from AI agent output
    for line in output.split('\n'):
        if line.startswith('POST_FILE_PATH='):
            deploy_manager.post_file_path = line.split('=', 1)[1].strip()
            break
    
    if not deploy_manager.post_file_path:
        error_msg = "Failed to get file path from AI agent output"
        deploy_manager.logger.error(error_msg)
        return False, error_msg
    

    # Run deployment steps
    if not deploy_manager.build_hugo(deploy_manager.ai_blog_site_path):
        return False, "Hugo build failed"
        
    if not deploy_manager.git_operations(deploy_manager.ai_blog_site_path):
        return False, "Git operations failed"
    
    deploy_manager.show_success_notification()
    return True, "Deployment completed successfully"

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent_type', required=True)
    parser.add_argument('--agent_name', required=True)
    parser.add_argument('--topic', required=False)
    parser.add_argument('--image_prompt', required=False)
    parser.add_argument('--webhook_url', required=False)
    
    args = parser.parse_args()
    main(**vars(args)) 