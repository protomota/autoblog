import os
import sys
import re
import subprocess
import logging
import datetime
import shutil
from pathlib import Path
from typing import Optional, Tuple

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

class DeployManager:
    def __init__(self):
        self.human_blog_url = os.getenv('HUMAN_BLOG_URL')
        self.obsidian_notes_path = Path(os.getenv('OBSIDIAN_NOTES_PATH'))
        self.human_blog_site_path = Path(os.getenv('HUMAN_BLOG_SITE_PATH'))
        self.source_path = self.obsidian_notes_path / 'posts'
        self.dest_path = self.human_blog_site_path / 'content' / 'posts'
        self.changes_made = False  # Add this flag to track changes
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

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
        """Get the latest file and generate blog URL."""
        try:
            files = sorted(self.source_path.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)
            if not files:
                return False, None, "No markdown files found"
            
            latest_file = files[0]
            file_name = latest_file.stem.lower()
            blog_url = f"{self.human_blog_url}/{file_name}/"
            
            self.logger.info("-" * 40)
            self.logger.info(f"BLOG_URL={blog_url}")
            self.logger.info("-" * 40)
            
            return True, blog_url, None
        except Exception as e:
            return False, None, str(e)

    def sync_images(self) -> bool:
        """Verify all images are properly synced."""
        try:
            site_static_images_dir = self.human_blog_site_path / 'static' / 'images'
            obsidian_images_dir = self.obsidian_notes_path / 'images'

            self.logger.info("Verifying image sync:")
            self.logger.info(f"  Source: {obsidian_images_dir}")
            self.logger.info(f"  Destination: {site_static_images_dir}")

            # Validate directories
            for directory in [self.dest_path, obsidian_images_dir, site_static_images_dir]:
                if not directory.exists():
                    self.logger.error(f"  Directory not found: {directory}")
                    raise FileNotFoundError(f"Directory not found: {directory}")
                self.logger.debug(f"  ✓ Validated: {directory}")

            # Verify all markdown files have correct image paths
            md_files = list(self.dest_path.glob('*.md'))
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
                        image_path = site_static_images_dir / image
                        if image_path.exists():
                            self.logger.info(f"      ✓ {image_path}")
                        else:
                            self.logger.warning(f"      ✗ Missing: {image_path}")
                            self.changes_made = True  # Set flag when images are copied
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
            source_files = [f for f in self.source_path.glob('*.md')]
            self.logger.info(f"Checking {len(source_files)} files for changes:")
            
            files_processed = 0
            for source_file in source_files:

                self.logger.info(f"Checking file: {source_file.name}")
                
                # Check if file needs to be synced
                dest_file = self.dest_path / source_file.name

                # Read content to check for images
                with open(source_file, "r") as file:
                    content = file.read()
                
                # Find all image references (both Obsidian and Markdown formats)
                obsidian_images = re.findall(r'\[\[([^]]*\.png)\]\]', content)
                markdown_images = re.findall(r'!\[.*?\]\(/images/([^)]+)\)', content)
                images = obsidian_images + markdown_images
                missing_images = False

                self.logger.info(f"Checking images: {images}")
                
                # Check if any images are missing in destination
                for image in images:

                    self.logger.info(f"Checking image: {image}")

                    new_image_name = image.replace(' ', '_')
                    dest_image = self.human_blog_site_path / 'static' / 'images' / new_image_name
                    self.logger.info(f"  - {source_file.name} (checking image: {image})")
                    if not dest_image.exists():
                        missing_images = True
                        self.logger.info(f"  - {source_file.name} (missing image: {image})")
                        
                        # Copy the missing image
                        image_source = self.obsidian_notes_path / 'images' / image
                        if image_source.exists():
                            # Ensure the destination directory exists
                            dest_image.parent.mkdir(parents=True, exist_ok=True)
                            # Copy the image
                            shutil.copy2(str(image_source), str(dest_image))
                            self.logger.info(f"    ✓ Copied missing image: {image} -> {dest_image}")
                            self.changes_made = True  # Set flag when images are copied
                        else:
                            self.logger.warning(f"    ✗ Source image not found: {image_source}")

                # Skip if destination exists, is newer than source, and has all images
                if (dest_file.exists() and 
                    dest_file.stat().st_mtime >= source_file.stat().st_mtime and 
                    not missing_images):
                    self.logger.info(f"  - {source_file.name} (no changes)")
                    continue
                
                self.logger.info(f"  - {source_file.name} (needs update)")

                files_processed += 1
                filename = source_file.name
                blog_url = f"{self.human_blog_url}/posts/{filename[:-3].lower().replace(' ', '-')}/"
                self.logger.info(f"  - {filename}")
                self.logger.info(f"    URL: {blog_url}")
                
                # Read content and process images
                with open(source_file, "r") as file:
                    content = file.read()
                
                # Find and replace image links
                images = re.findall(r'\[\[([^]]*\.png)\]\]', content)
                self.logger.info(f"    Found {len(images)} images to process")
                
                for image in images:
                    self.logger.info(f"    Processing image: {image}")
                    # Replace spaces with underscores in image filename
                    new_image_name = image.replace(' ', '_')
                    
                    # Rename the image in Obsidian notes folder if needed
                    obsidian_image = self.obsidian_notes_path / 'images' / image
                    new_obsidian_image = self.obsidian_notes_path / 'images' / new_image_name
                    if obsidian_image.exists() and obsidian_image != new_obsidian_image:
                        obsidian_image.rename(new_obsidian_image)
                        self.logger.info(f"    ✓ Renamed Obsidian image: {image} -> {new_image_name}")
                        self.changes_made = True
                    
                    # Prepare the Markdown-compatible link
                    markdown_image = f"[Image](/images/{new_image_name})"
                    content = content.replace(f"[[{image}]]", markdown_image)
                
                # Write processed content back to source file
                with open(source_file, "w") as file:
                    file.write(content)
                self.logger.info(f"    ✓ Updated source file")
                
                # Write processed content to destination
                with open(dest_file, "w") as file:
                    file.write(content)
                self.logger.info(f"    ✓ Created destination file")
            
            if files_processed > 0:
                self.changes_made = True  # Set flag when files are processed
                self.logger.info(f"Content sync completed successfully ({files_processed} files updated)")
            else:
                self.logger.info("No files needed updating")
            return True
            
        except Exception as e:
            self.logger.error(f"Sync failed: {e}")
            self.logger.exception("Detailed error trace:")
            return False

    def build_hugo(self) -> bool:
        """Build Hugo site."""
        success, output = self.run_command(['hugo'], cwd=self.human_blog_site_path)
        if not success:
            self.logger.error(f"Hugo build failed: {output}")
        return success

    def git_operations(self) -> bool:
        """Handle all git operations."""
        try:
            # Add all changes
            self.run_command(['git', 'add', '.'], cwd=self.human_blog_site_path)
            
            # Check for changes
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                 cwd=self.human_blog_site_path, 
                                 capture_output=True)
            
            if result.returncode == 1:  # Changes exist
                commit_message = f"New Blog Post on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.run_command(['git', 'commit', '-m', commit_message], cwd=self.human_blog_site_path)
                
                # Push to main
                self.run_command(['git', 'push', 'origin', 'main'], cwd=self.human_blog_site_path)
                
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
                         cwd=self.human_blog_site_path,
                         stderr=subprocess.DEVNULL)
            
            # Create new hostinger-deploy branch
            self.run_command(['git', 'subtree', 'split', '--prefix', 'public', '-b', 'hostinger-deploy'],
                           cwd=self.human_blog_site_path)
            
            # Force push to hostinger
            self.run_command(['git', 'push', 'origin', 'hostinger-deploy:hostinger-humanblog', '--force'],
                           cwd=self.human_blog_site_path)
            
            # Cleanup
            self.run_command(['git', 'branch', '-D', 'hostinger-deploy'],
                           cwd=self.human_blog_site_path)
            
            return True
        except Exception as e:
            self.logger.error(f"Hostinger deployment failed: {e}")
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
    deploy_manager = DeployManager()
    
    # Run sync operations first
    if not all([
        deploy_manager.sync_content(),
        deploy_manager.sync_images()
    ]):
        return False

    # Only proceed with build and git operations if changes were made
    if deploy_manager.changes_made:
        if all([
            deploy_manager.build_hugo(),
            deploy_manager.git_operations()
        ]):
            deploy_manager.show_success_notification()
            return True
    else:
        deploy_manager.logger.info("No changes detected - skipping build and git operations")
        deploy_manager.show_success_notification(no_changes=True)
        return True
    
    return False

if __name__ == "__main__":
    main() 