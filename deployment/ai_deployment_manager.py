import os
import sys
import subprocess
import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple
from blogi.core.config import PROJECT_ROOT

class AIDeployManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIDeployManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.project_root = PROJECT_ROOT
        self.ai_blog_site_path = PROJECT_ROOT / "ai_blog"
        self.source_path = self.ai_blog_site_path / 'content' / 'posts'
        self.file_path = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        self._initialized = True

    def run_command(self, cmd: list, cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            self.logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                check=True,
                env=os.environ.copy()  # Ensure environment variables are passed
            )
            if result.stderr:
                self.logger.warning(f"Command stderr: {result.stderr}")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with exit code {e.returncode}:\nstdout: {e.stdout}\nstderr: {e.stderr}"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_latest_file(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Get the file and generate blog URL."""
        try:
            post_path = Path(self.file_path)
            if not post_path.exists():
                return False, None, f"Post file not found at {post_path}"
            
            file_name = post_path.stem.lower()
            blog_url = f"https://protoblog.protomota.com/posts/{file_name}/"
            
            self.logger.info("-" * 40)
            self.logger.info(f"BLOG_URL={blog_url}")
            self.logger.info("-" * 40)
            
            return True, blog_url, None
        except Exception as e:
            self.logger.error(f"Failed to process file: {e}")
            return False, None, str(e)

    def build_hugo(self) -> bool:
        """Build Hugo site."""
        success, output = self.run_command(['hugo'], cwd=self.ai_blog_site_path)
        if not success:
            self.logger.error(f"Hugo build failed: {output}")
        return success

    def git_operations(self) -> bool:
        """Handle all git operations."""
        try:
            # Add all changes
            self.run_command(['git', 'add', '.'], cwd=self.ai_blog_site_path)
            
            # Check for changes
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                 cwd=self.ai_blog_site_path, 
                                 capture_output=True)
            
            if result.returncode == 1:  # Changes exist
                commit_message = f"New Blog Post on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.run_command(['git', 'commit', '-m', commit_message], cwd=self.ai_blog_site_path)
                
                # Push to main
                self.run_command(['git', 'push', 'origin', 'main'], cwd=self.ai_blog_site_path)
                
                # Handle hostinger branch
                self.handle_hostinger_deployment()
                
            return True
        except Exception as e:
            self.logger.error(f"Git operations failed: {e}")
            return False

    def handle_hostinger_deployment(self) -> bool:
        """Handle hostinger branch deployment."""
        try:
            # Remove existing hostinger-deploy branch if it exists
            subprocess.run(['git', 'branch', '-D', 'hostinger-deploy'], 
                         cwd=self.ai_blog_site_path,
                         stderr=subprocess.DEVNULL)
            
            # Create new hostinger-deploy branch
            self.run_command(['git', 'subtree', 'split', '--prefix', 'public', '-b', 'hostinger-deploy'],
                           cwd=self.ai_blog_site_path)
            
            # Force push to hostinger
            self.run_command(['git', 'push', 'origin', 'hostinger-deploy:hostinger-protoblog', '--force'],
                           cwd=self.ai_blog_site_path)
            
            # Cleanup
            self.run_command(['git', 'branch', '-D', 'hostinger-deploy'],
                           cwd=self.ai_blog_site_path)
            
            return True
        except Exception as e:
            self.logger.error(f"Hostinger deployment failed: {e}")
            return False

    def show_success_notification(self):
        """Show success notification on macOS."""
        try:
            subprocess.run(['osascript', '-e', 'display dialog "Deployment completed successfully!"'])
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")

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
    # Assuming the AI agent outputs the file path in a format like "FILE_PATH=<path>"

    for line in output.split('\n'):
        if line.startswith('FILE_PATH='):
            deploy_manager.file_path = line.split('=', 1)[1].strip()
            break
    
    if not deploy_manager.file_path:
        error_msg = "Failed to get file path from AI agent output"
        deploy_manager.logger.error(error_msg)
        return False, error_msg
    
    # Get blog URL using the file path
    success, blog_url, error = deploy_manager.get_latest_file()
    if not success:
        error_msg = f"Failed to process file: {error}"
        deploy_manager.logger.error(error_msg)
        return False, error_msg
    
    # TODO: Remove this
    # Disable GIT operations
    return True, "Deployment completed successfully"

    # Run deployment steps
    if not deploy_manager.build_hugo():
        return False, "Hugo build failed"
        
    if not deploy_manager.git_operations():
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