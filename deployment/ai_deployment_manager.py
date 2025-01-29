import os
import sys
import subprocess
import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple
from blogi.core.config import logger, PROJECT_ROOT, AI_BLOG_URL, AI_BLOG_SITE_PATH, AI_POSTS_PATH
from blogi.deployment.base_deployment_manager import BaseDeployManager

class AIDeployManager(BaseDeployManager):
    _instance = None
    
    def __new__(cls):
        logger.info(f"Creating new AIDeployManager instance (Singleton)")
        if cls._instance is None:
            cls._instance = super(AIDeployManager, cls).__new__(cls)
            cls._instance._initialized = False
            logger.info("New AIDeployManager instance created")
        else:
            logger.info("Returning existing AIDeployManager instance")
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            logger.debug("AIDeployManager already initialized, skipping initialization")
            return
            
        logger.info("Initializing AIDeployManager")
        super().__init__()
        self.project_root = PROJECT_ROOT
        self.ai_blog_site_path = AI_BLOG_SITE_PATH
        self.post_file_path = None
        self.blog_url_base = AI_BLOG_URL

        self.dest_path = AI_POSTS_PATH
        self.post_file_path = None
        self.blog_url_base = AI_BLOG_URL

        logger.info(f"AIDeployManager initialized with:")
        logger.info(f"  - Project root: {self.project_root}")
        logger.info(f"  - Blog site path: {self.ai_blog_site_path}")
        logger.info(f"  - Posts path: {self.dest_path}")
        logger.info(f"  - Blog URL base: {self.blog_url_base}")

        self._initialized = True
        logger.info("AIDeployManager initialization complete")

    def deploy(self, agent_type: str, agent_name: str, topic: str = None, image_prompt: str = None, webhook_url: str = None) -> tuple[bool, str]:
        """Deploy AI blog post."""
        logger.info("\n=== Starting Blog Post Deployment ===")
        logger.info(f"Deployment parameters:")
        logger.info(f"  - Agent type: {agent_type}")
        logger.info(f"  - Agent name: {agent_name}")
        logger.info(f"  - Topic: {topic}")
        logger.info(f"  - Image prompt: {image_prompt}")
        logger.info(f"  - Webhook URL: {webhook_url}")

        try:
            # Construct command with full path to script
            script_path = PROJECT_ROOT / "blogi" / "agent" / "main.py"
            logger.info(f"Using script path: {script_path}")
            
            command = [
                "python",
                str(script_path),
                "--agent_type", agent_type,
                "--agent_name", agent_name
            ]
            
            if topic:
                command.extend(["--topic", topic])
            if image_prompt:
                command.extend(["--image_prompt", image_prompt])
            if webhook_url:
                command.extend(["--webhook_url", webhook_url])

            logger.info(f"Executing command: {' '.join(command)}")
            success, output = self.run_command(command)
            
            if not success:
                logger.error(f"AI agent execution failed")
                logger.error(f"Output: {output}")
                return False, f"AI agent execution failed: {output}"

            # Extract file path from AI agent output
            logger.info("Parsing AI agent output for file path")
            for line in output.split('\n'):
                if line.startswith('POST_FILE_PATH='):
                    self.post_file_path = line.split('=', 1)[1].strip()
                    logger.info(f"Found post file path: {self.post_file_path}")
                    break
            
            if not self.post_file_path:
                logger.error("Failed to extract post file path from output")
                return False, "Failed to get file path from AI agent output"
            
            # Run deployment steps
            logger.info("Starting Hugo build process")
            if not self.build_hugo(self.ai_blog_site_path):
                logger.error("Hugo build failed")
                return False, "Hugo build failed"
            
            logger.info("Starting Git operations")
            if not self.git_operations(self.ai_blog_site_path):
                logger.error("Git operations failed")
                return False, "Git operations failed"
            
            logger.info("Deployment completed successfully")
            self.show_success_notification()
            return True, "Deployment completed successfully"

        except Exception as e:
            logger.error("=== Deployment Error ===")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}", exc_info=True)
            return False, f"An error occurred: {e}"

def main(agent_type: str, agent_name: str, **kwargs):
    """Main entry point for deployment process."""
    logger.info("\n=== Starting Deployment Main Process ===")
    logger.info(f"Parameters:")
    logger.info(f"  - Agent type: {agent_type}")
    logger.info(f"  - Agent name: {agent_name}")
    logger.info(f"  - Additional kwargs: {kwargs}")

    deploy_manager = AIDeployManager()
    
    # Fix: Use correct path to main.py
    python_script = PROJECT_ROOT / 'blogi' / 'agent' / 'main.py'
    logger.info(f"Using script path: {python_script}")

    cmd = [sys.executable, str(python_script), '--agent_type', agent_type, '--agent_name', agent_name]
    
    # Add additional arguments based on agent type
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend([f'--{key}', value])
    
    logger.info(f"Executing command: {' '.join(cmd)}")
    success, output = deploy_manager.run_command(cmd)
    
    if not success:
        error_msg = f"AI agent execution failed: {output}"
        logger.error(error_msg)
        return False, error_msg
    
    # Extract file path from AI agent output
    logger.info("Parsing output for post file path")
    for line in output.split('\n'):
        if line.startswith('POST_FILE_PATH='):
            deploy_manager.post_file_path = line.split('=', 1)[1].strip()
            logger.info(f"Found post file path: {deploy_manager.post_file_path}")
            break
    
    if not deploy_manager.post_file_path:
        error_msg = "Failed to get file path from AI agent output"
        logger.error(error_msg)
        return False, error_msg
    
    # Run deployment steps
    logger.info("Starting Hugo build")
    if not deploy_manager.build_hugo(deploy_manager.ai_blog_site_path):
        logger.error("Hugo build failed")
        return False, "Hugo build failed"
        
    logger.info("Starting Git operations")
    if not deploy_manager.git_operations(deploy_manager.ai_blog_site_path):
        logger.error("Git operations failed")
        return False, "Git operations failed"
    
    logger.info("Deployment process completed successfully")
    deploy_manager.show_success_notification()
    return True, "Deployment completed successfully"

if __name__ == "__main__":
    logger.info("=== Starting Command Line Deployment ===")
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent_type', required=True)
    parser.add_argument('--agent_name', required=True)
    parser.add_argument('--topic', required=False)
    parser.add_argument('--image_prompt', required=False)
    parser.add_argument('--webhook_url', required=False)
    
    args = parser.parse_args()
    logger.info(f"Command line arguments: {args}")
    main(**vars(args)) 