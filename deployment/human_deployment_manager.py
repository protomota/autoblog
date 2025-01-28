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
    OBSIDIAN_NOTES_PATH,
    HUMAN_BLOG_SITE_STATIC_IMAGES_PATH,
    OBSIDIAN_HUMAN_IMAGES_PATH,
    HUMAN_BLOG_URL,
    HUMAN_BLOG_SITE_PATH,
    OBSIDIAN_HUMAN_POSTS_PATH,
    HUMAN_POSTS_PATH
)

# Debug mode flag - set to True to enable DEBUG logging
DEBUG_MODE = False

# Set base logging level based on DEBUG_MODE
BASE_LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=BASE_LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

# Create logger instance
logger = setup_logging()

from .base_deployment_manager import BaseDeployManager

class HumanDeployManager(BaseDeployManager):
    def __init__(self):
        super().__init__()
        self.dest_path = HUMAN_POSTS_PATH
        self.post_file_path = OBSIDIAN_HUMAN_POSTS_PATH
        self.blog_url_base = HUMAN_BLOG_URL

    def sync_images(self) -> bool:
        """Verify all images are properly synced."""
        try:
            self.logger.info("Verifying image sync:")
            self.logger.info(f"  Source: {OBSIDIAN_HUMAN_IMAGES_PATH}")
            self.logger.info(f"  Destination: {HUMAN_BLOG_SITE_STATIC_IMAGES_PATH}")

            # Validate directories
            for directory in [HUMAN_POSTS_PATH, OBSIDIAN_HUMAN_IMAGES_PATH, HUMAN_BLOG_SITE_STATIC_IMAGES_PATH]:
                if not directory.exists():
                    self.logger.error(f"  Directory not found: {directory}")
                    raise FileNotFoundError(f"Directory not found: {directory}")
                self.logger.debug(f"  ✓ Validated: {directory}")

            # Verify all markdown files have correct image paths
            md_files = list(HUMAN_POSTS_PATH.glob('*.md'))
            self.logger.info(f"Verifying {len(md_files)} markdown files:")

            for filepath in md_files:
                self.logger.info(f"  File: {filepath.name}")
                with open(filepath, "r") as file:
                    content = file.read()
                
                # Check for any remaining Obsidian-style links
                obsidian_links = re.findall(r'\[\[([^]]*\.png)\]\]', content)
                if obsidian_links:
                    self.logger.warning(f"    Found {len(obsidian_links)} unconverted image links!")
                
                # Verify all markdown-style images exist
                markdown_links = re.findall(r'!\[.*?\]\(/images/([^)]+)\)', content)
                if markdown_links:
                    self.logger.info(f"    Found {len(markdown_links)} image references:")
                    for image in markdown_links:
                        image_path = HUMAN_BLOG_SITE_STATIC_IMAGES_PATH / image
                        if image_path.exists():
                            self.logger.info(f"      ✓ {image_path}")
                        else:
                            self.logger.warning(f"      ✗ Missing: {image_path}")
                            self.changes_made = True
                else:
                    self.logger.info("    No images found")

            self.logger.info("Image verification completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Image verification failed: {e}")
            self.logger.exception("Detailed error trace:")
            return False

    def sync_content(self) -> bool:
        """Sync content from Obsidian to Hugo."""
        try:
            # Create destination directory if it doesn't exist
            self.dest_path.mkdir(parents=True, exist_ok=True)
            
            # Get list of files and process them
            source_files = [f for f in OBSIDIAN_HUMAN_POSTS_PATH.glob('*.md')]
            self.logger.info(f"Checking {len(source_files)} files for changes:")
            
            files_processed = 0
            for source_file in source_files:
                self.logger.info(f"Checking file: {source_file.name}")
                
                # Check if file needs to be synced
                dest_file = HUMAN_POSTS_PATH / source_file.name

                # Read content to check for images
                with open(source_file, "r") as file:
                    content = file.read()
                
                # Process images and update content
                content = self._process_images(content, source_file)
                
                # Write processed content back
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
            
            # Handle image in Obsidian folder
            obsidian_image = OBSIDIAN_HUMAN_IMAGES_PATH / image
            new_obsidian_image = OBSIDIAN_HUMAN_IMAGES_PATH / new_image_name
            if obsidian_image.exists() and obsidian_image != new_obsidian_image:
                obsidian_image.rename(new_obsidian_image)
                self.logger.info(f"    ✓ Renamed Obsidian image: {image} -> {new_image_name}")
                self.changes_made = True
            
            # Update content with markdown-style link
            markdown_image = f"![Image](/images/{new_image_name})"
            content = content.replace(f"[[{image}]]", markdown_image)
            
        return content

    def build_hugo(self, site_path: Path) -> bool:
        """Build Hugo site."""
        success, output = self.run_command(['hugo'], cwd=site_path)
        if not success:
            self.logger.error(f"Hugo build failed: {output}")
        return success

    def show_success_notification(self, no_changes=False):
        """Show success notification on macOS."""
        try:
            message = "No changes detected!" if no_changes else "Deployment completed successfully!"
            subprocess.run(['osascript', '-e', f'display dialog "{message}"'])
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")

def main():
    """Main entry point for deployment process."""
    deploy_manager = HumanDeployManager()
    
    # Run sync operations first
    if not all([
        deploy_manager.sync_content(),
        deploy_manager.sync_images()
    ]):
        return False

    # Only proceed with build and git operations if changes were made
    if deploy_manager.changes_made:
        if all([
            deploy_manager.build_hugo(HUMAN_BLOG_SITE_PATH),
            deploy_manager.git_operations(HUMAN_BLOG_SITE_PATH)
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