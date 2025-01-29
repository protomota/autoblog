import os
import sys
import re
import subprocess
import logging
import datetime
import shutil
from pathlib import Path
from typing import Optional, Tuple

# Add the parent directory of the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT.parent))

from blogi.core.config import (
    PROJECT_ROOT,
    HUMAN_BLOG_SITE_STATIC_IMAGES_PATH,
    OBSIDIAN_HUMAN_IMAGES_PATH,
    HUMAN_BLOG_URL,
    HUMAN_BLOG_SITE_PATH,
    OBSIDIAN_HUMAN_POSTS_PATH,
    HUMAN_POSTS_PATH
)

# Debug mode flag - set to True to enable DEBUG logging
DEBUG_MODE = False
BASE_LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'

def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=BASE_LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class DeploymentManager:
    def __init__(self, blog_type="human"):
        self.logger = logger
        self.changes_made = False
        
        # Set paths based on blog type
        if blog_type == "human":
            self.dest_path = HUMAN_POSTS_PATH
            self.post_file_path = OBSIDIAN_HUMAN_POSTS_PATH
            self.blog_url_base = HUMAN_BLOG_URL
            self.blog_site_path = HUMAN_BLOG_SITE_PATH
            self.images_source = OBSIDIAN_HUMAN_IMAGES_PATH
            self.images_dest = HUMAN_BLOG_SITE_STATIC_IMAGES_PATH
        else:
            raise ValueError(f"Unsupported blog type: {blog_type}")

    def run_command(self, command: list[str], cwd: str = None) -> Tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            process = subprocess.run(
                command,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True
            )
            return True, process.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def sync_images(self) -> bool:
        """Verify all images are properly synced."""
        try:
            self.logger.info("Verifying image sync:")
            self.logger.info(f"  Source: {self.images_source}")
            self.logger.info(f"  Destination: {self.images_dest}")

            # Validate directories
            for directory in [self.dest_path, self.images_source, self.images_dest]:
                if not directory.exists():
                    self.logger.error(f"  Directory not found: {directory}")
                    raise FileNotFoundError(f"Directory not found: {directory}")
                self.logger.debug(f"  ✓ Validated: {directory}")

            # Verify markdown files
            md_files = list(self.dest_path.glob('*.md'))
            self.logger.info(f"Verifying {len(md_files)} markdown files:")

            for filepath in md_files:
                self.logger.info(f"  File: {filepath.name}")
                with open(filepath, "r") as file:
                    content = file.read()
                
                # Check for unconverted links
                obsidian_links = re.findall(r'\[\[([^]]*\.png)\]\]', content)
                if obsidian_links:
                    self.logger.warning(f"    Found {len(obsidian_links)} unconverted image links!")
                
                # Verify markdown images
                markdown_links = re.findall(r'!\[.*?\]\(/images/([^)]+)\)', content)
                if markdown_links:
                    self.logger.info(f"    Found {len(markdown_links)} image references:")
                    for image in markdown_links:
                        image_path = self.images_dest / image
                        if image_path.exists():
                            self.logger.info(f"      ✓ {image_path}")
                        else:
                            self.logger.warning(f"      ✗ Missing: {image_path}")
                            self.changes_made = True
                else:
                    self.logger.info("    No images found")

            return True
            
        except Exception as e:
            self.logger.error(f"Image verification failed: {e}")
            self.logger.exception("Detailed error trace:")
            return False

    def sync_content(self) -> bool:
        """Sync content from Obsidian to Hugo."""
        try:
            self.dest_path.mkdir(parents=True, exist_ok=True)
            
            source_files = [f for f in self.post_file_path.glob('*.md')]
            self.logger.info(f"Checking {len(source_files)} files for changes:")
            
            files_processed = 0
            for source_file in source_files:
                self.logger.info(f"Checking file: {source_file.name}")
                
                dest_file = self.dest_path / source_file.name

                with open(source_file, "r") as file:
                    content = file.read()
                
                content = self._process_images(content, source_file)
                
                with open(source_file, "w") as file:
                    file.write(content)
                with open(dest_file, "w") as file:
                    file.write(content)
                
                files_processed += 1
                
            if files_processed > 0:
                self.changes_made = True
                self.logger.info(f"Content sync completed successfully ({files_processed} files updated)")
            else:
                self.logger.info("No files needed updating")
            return True
            
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            self.logger.exception("Detailed error trace:")
            return False

    def _process_images(self, content: str, source_file: Path) -> str:
        """Process images in content and return updated content."""
        images = re.findall(r'\[\[([^]]*\.png)\]\]', content)
        
        for image in images:
            self.logger.info(f"    Processing image: {image}")
            new_image_name = image.replace(' ', '_')
            
            obsidian_image = self.images_source / image
            new_obsidian_image = self.images_source / new_image_name
            if obsidian_image.exists() and obsidian_image != new_obsidian_image:
                obsidian_image.rename(new_obsidian_image)
                self.logger.info(f"    ✓ Renamed Obsidian image: {image} -> {new_image_name}")
                self.changes_made = True
            
            markdown_image = f"![Image](/images/{new_image_name})"
            content = content.replace(f"[[{image}]]", markdown_image)
            
        return content

    def build_hugo(self, site_path: Path) -> bool:
        """Build Hugo site."""
        success, output = self.run_command(['hugo'], cwd=site_path)
        if not success:
            self.logger.error(f"Hugo build failed: {output}")
        return success

    def git_operations(self, site_path: Path) -> bool:
        """Handle all git operations."""
        try:
            self.run_command(['git', 'add', '.'], cwd=site_path)
            
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                 cwd=site_path, 
                                 capture_output=True)
            
            if result.returncode == 1:  # Changes exist
                commit_message = f"New Blog Post on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.run_command(['git', 'commit', '-m', commit_message], cwd=site_path)
                self.run_command(['git', 'push', 'origin', 'main'], cwd=site_path)
                self.handle_branch_deployment(site_path)
                
            return True
        except Exception as e:
            self.logger.error(f"Git operations failed: {e}")
            return False

    def handle_branch_deployment(self, site_path: Path) -> bool:
        """Handle branch deployment."""
        try:
            subprocess.run(['git', 'branch', '-D', 'deploy'], 
                         cwd=site_path,
                         stderr=subprocess.DEVNULL)
            
            self.run_command(['git', 'subtree', 'split', '--prefix', 'public', '-b', 'deploy'],
                           cwd=site_path)
            self.run_command(['git', 'push', 'origin', 'deploy:deploy', '--force'],
                           cwd=site_path)
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

def main():
    """Main entry point for deployment process."""
    deploy_manager = DeploymentManager(blog_type="human")
    
    if not all([
        deploy_manager.sync_content(),
        deploy_manager.sync_images()
    ]):
        return False

    if deploy_manager.changes_made:
        if all([
            deploy_manager.build_hugo(deploy_manager.blog_site_path),
            deploy_manager.git_operations(deploy_manager.blog_site_path)
        ]):
            deploy_manager.show_success_notification()
            return True
    else:
        deploy_manager.logger.info("No changes detected - skipping build and git operations")
        deploy_manager.show_success_notification(no_changes=True)
        return True
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 