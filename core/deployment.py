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

# Configuration
from blogi.core.config import (
    PROJECT_ROOT,
    BLOG_SITE_STATIC_IMAGES_PATH,
    OBSIDIAN_IMAGES_PATH,
    BLOG_URL,
    BLOG_SITE_PATH,
    BLOG_SITE_POSTS_PATH,
    OBSIDIAN_POSTS_PATH,
    BLOG_SITE_STATIC_AI_IMAGES_PATH,
    OBSIDIAN_AI_IMAGES
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
    def __init__(self):
        self.logger = logger
        self.changes_made = False

        self.dest_path = BLOG_SITE_POSTS_PATH
        self.origin_path = OBSIDIAN_POSTS_PATH
        self.blog_url_base = BLOG_URL
        self.blog_site_path = BLOG_SITE_PATH
        self.images_source = OBSIDIAN_IMAGES_PATH
        self.images_dest = BLOG_SITE_STATIC_IMAGES_PATH
        self.ai_images_source = OBSIDIAN_AI_IMAGES
        self.ai_images_dest = BLOG_SITE_STATIC_AI_IMAGES_PATH

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
        """Verify and sync all images from Obsidian to website folder, including AI images."""
        try:
            self.logger.info("Verifying and syncing images:")
            self.logger.info(f"  Source: {self.images_source}")
            self.logger.info(f"  Destination: {self.images_dest}")

            # Validate directories
            for directory in [self.dest_path, self.images_source, self.images_dest]:
                if not directory.exists():
                    self.logger.error(f"  Directory not found: {directory}")
                    raise FileNotFoundError(f"Directory not found: {directory}")
                self.logger.debug(f"  ✓ Validated: {directory}")

            # Create destination directory if it doesn't exist
            self.images_dest.mkdir(parents=True, exist_ok=True)

            # Verify markdown files for standard images
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
                
                # Verify and copy markdown images
                markdown_links = re.findall(r'!\[.*?\]\(/images/([^)]+)\)', content)
                if markdown_links:
                    self.logger.info(f"    Found {len(markdown_links)} image references:")
                    for image in markdown_links:
                        source_path = self.images_source / image
                        dest_path = self.images_dest / image
                        
                        # Check if source image exists
                        if source_path.exists():
                            # Copy image if it doesn't exist in destination or if source is newer
                            if not dest_path.exists() or (source_path.stat().st_mtime > dest_path.stat().st_mtime):
                                self.logger.info(f"      Copying: {image}")
                                shutil.copy2(source_path, dest_path)
                                self.changes_made = True
                            self.logger.info(f"      ✓ {dest_path}")
                        else:
                            self.logger.warning(f"      ✗ Source image missing: {source_path}")
                else:
                    self.logger.info("    No images found")

            # --- New Section: Sync AI Images ---
            self.logger.info("Verifying and syncing AI images:")
            self.logger.info(f"  AI Source: {self.ai_images_source}")
            self.logger.info(f"  AI Destination: {self.ai_images_dest}")

            # Validate AI image directories
            for directory in [self.ai_images_source, self.ai_images_dest]:
                if not directory.exists():
                    self.logger.error(f"  Directory not found: {directory}")
                    raise FileNotFoundError(f"Directory not found: {directory}")
                self.logger.debug(f"  ✓ Validated: {directory}")

            # Create AI destination directory if it doesn't exist
            self.ai_images_dest.mkdir(parents=True, exist_ok=True)

            # Copy new or updated AI images
            for source_file in self.ai_images_source.glob('*'):
                dest_file = self.ai_images_dest / source_file.name
                if not dest_file.exists() or (source_file.stat().st_mtime > dest_file.stat().st_mtime):
                    self.logger.info(f"      Copying AI image: {source_file.name}")
                    shutil.copy2(source_file, dest_file)
                    self.changes_made = True
                self.logger.info(f"      ✓ {dest_file}")

            # Delete AI images in destination that no longer exist in source
            for dest_file in self.ai_images_dest.glob('*'):
                source_file = self.ai_images_source / dest_file.name
                if not source_file.exists():
                    self.logger.info(f"      Deleting AI image: {dest_file.name}")
                    dest_file.unlink()
                    self.changes_made = True

            return True
            
        except Exception as e:
            self.logger.error(f"Image verification failed: {e}")
            self.logger.exception("Detailed error trace:")
            return False

    def sync_content(self) -> bool:
        """Sync content from Obsidian to Hugo."""
        try:
            self.dest_path.mkdir(parents=True, exist_ok=True)
            
            source_files = [f for f in self.origin_path.glob('*.md')]
            self.logger.info(f"Checking {len(source_files)} files for changes:")
            
            files_processed = 0
            for source_file in source_files:
                self.logger.info(f"Checking file: {source_file.name}")
                
                dest_file = self.dest_path / source_file.name

                with open(source_file, "r") as file:
                    content = file.read()
                
                content = self._process_image_paths_in_content(content, source_file)
                
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

    def _process_image_paths_in_content(self, content: str, source_file: Path) -> str:
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
    deploy_manager = DeploymentManager()
    
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