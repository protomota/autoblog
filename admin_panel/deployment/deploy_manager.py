import os
import sys
import subprocess
import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple

class DeployManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeployManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.project_root = Path(os.getenv('PROTOBLOG_PROJECT_ROOT'))
        self.source_path = self.project_root / 'content' / 'posts'
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
            result = subprocess.run(
                cmd,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Command failed: {e.stderr}"
        except Exception as e:
            return False, f"Error: {str(e)}"

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
        success, output = self.run_command(['hugo'], cwd=self.project_root)
        if not success:
            self.logger.error(f"Hugo build failed: {output}")
        return success

    def git_operations(self) -> bool:
        """Handle all git operations."""
        try:
            # Add all changes
            self.run_command(['git', 'add', '.'], cwd=self.project_root)
            
            # Check for changes
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                 cwd=self.project_root, 
                                 capture_output=True)
            
            if result.returncode == 1:  # Changes exist
                commit_message = f"New Blog Post on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.run_command(['git', 'commit', '-m', commit_message], cwd=self.project_root)
                
                # Push to main
                self.run_command(['git', 'push', 'origin', 'main'], cwd=self.project_root)
                
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
                         cwd=self.project_root,
                         stderr=subprocess.DEVNULL)
            
            # Create new hostinger-deploy branch
            self.run_command(['git', 'subtree', 'split', '--prefix', 'public', '-b', 'hostinger-deploy'],
                           cwd=self.project_root)
            
            # Force push to hostinger
            self.run_command(['git', 'push', 'origin', 'hostinger-deploy:hostinger-protoblog', '--force'],
                           cwd=self.project_root)
            
            # Cleanup
            self.run_command(['git', 'branch', '-D', 'hostinger-deploy'],
                           cwd=self.project_root)
            
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
    deploy_manager = DeployManager()
    
    # Run the AI agent
    python_script = deploy_manager.project_root / 'ai_agents' / 'main.py'
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