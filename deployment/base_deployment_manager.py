import os
import sys
import subprocess
import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple
from blogi.core.config import PROJECT_ROOT

class BaseDeployManager:
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        self.changes_made = False
        self.blog_url_base = None
        self.post_file_path = None

    def run_command(self, command: list) -> tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            self.logger.info(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True
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

    def build_hugo(self, site_path: Path) -> bool:
        """Build Hugo site."""
        success, output = self.run_command(['hugo'], cwd=site_path)
        if not success:
            self.logger.error(f"Hugo build failed: {output}")
        return success

    def git_operations(self, site_path: Path) -> bool:
        """Handle all git operations."""
        try:
            # Add all changes
            self.run_command(['git', 'add', '.'], cwd=site_path)
            
            # Check for changes
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                 cwd=site_path, 
                                 capture_output=True)
            
            if result.returncode == 1:  # Changes exist
                commit_message = f"New Blog Post on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.run_command(['git', 'commit', '-m', commit_message], cwd=site_path)
                
                # Push to main
                self.run_command(['git', 'push', 'origin', 'main'], cwd=site_path)
                
                # Handle deployment branch
                self.handle_branch_deployment(site_path)
                
            return True
        except Exception as e:
            self.logger.error(f"Git operations failed: {e}")
            return False

    def handle_branch_deployment(self, site_path: Path) -> bool:
        """Handle branch deployment."""
        try:
            # Remove existing deploy branch if it exists
            subprocess.run(['git', 'branch', '-D', 'deploy'], 
                         cwd=site_path,
                         stderr=subprocess.DEVNULL)
            
            # Create new deploy branch
            self.run_command(['git', 'subtree', 'split', '--prefix', 'public', '-b', 'deploy'],
                           cwd=site_path)
            
            # Force push to deploy
            self.run_command(['git', 'push', 'origin', 'deploy:deploy', '--force'],
                           cwd=site_path)
            
            # Cleanup
            self.run_command(['git', 'branch', '-D', 'deploy'],
                           cwd=site_path)
            
            return True
        except Exception as e:
            self.logger.error(f"Branch deployment failed: {e}")
            return False

    def show_success_notification(self, no_changes=False):
        """Show success notification on macOS."""
        try:
            message = "No changes detected!" if no_changes else "Deployment completed successfully!"
            subprocess.run(['osascript', '-e', f'display dialog "{message}"'])
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")

    def get_latest_file(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Get the file and generate blog URL."""
        try:
            if not self.blog_url_base:
                return False, None, "Blog URL base not set"

            post_path = Path(self.post_file_path)
            if not post_path.exists():
                return False, None, f"Post file not found at {post_path}"
            
            file_name = post_path.stem.lower()
            blog_url = f"{self.blog_url_base}/{file_name}/"
            
            self.logger.info("-" * 40)
            self.logger.info(f"BLOG_URL={blog_url}")
            self.logger.info("-" * 40)
            
            return True, blog_url, None
        except Exception as e:
            self.logger.error(f"Failed to process file: {e}")
            return False, None, str(e) 