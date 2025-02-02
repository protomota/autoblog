from datetime import datetime
from typing import Tuple, Optional, Dict
from pathlib import Path
import os
import json

# Configure logging
from blogi.core.config import logger, PROJECT_ROOT, timestamp_manager

class ArtistPostGenerator:
    def __init__(self, agent):
        self.agent = agent
        self.image_service = None
        
    async def _load_templates(self) -> Dict[str, str]:
        templates = {}
        paths = {
            'agent_prompt': self.agent.agent_prompt_path,
            'enhanced_prompt': self.agent.enhanced_prompt_path,
            'disclaimer': self.agent.disclaimer_path,
            'frontmatter': self.agent.frontmatter_path,
            'blog_template': self.agent.blog_page_template_path
        }
        
        for name, path in paths.items():
            content = await self.agent.read_file(str(path))
            if not content:
                raise ValueError(f"Failed to load template: {name}")
            templates[name] = content
            
        return templates

    async def generate_blog_post(self) -> Tuple[str, str]:
        """Generate a blog post with images.
        Returns:
            Tuple[str, str]: A tuple containing (filename, blog_page)
        """
        logger.info("\n=== Starting Blog Post Generation ===")
        try:
            logger.info("Loading templates...")
            templates = await self._load_templates()
            
            logger.info("Generating image file paths...")
            image_paths = await self._generate_image_file_paths()
            
            logger.info("Creating gallery code...")
            gallery_code = self._create_gallery_code(image_paths)
            
            logger.info("Requesting blog content from AI...")
            blog_content = await self.agent.anthropic.ask(
                self._format_prompt(templates['agent_prompt'], templates['enhanced_prompt'])
            )
            logger.info(f"Received blog content (length: {len(blog_content) if blog_content else 0} characters)")
            
            # Save blog_content to config.json
            logger.info("Saving blog content to config file...")
            config_data = {
                'blog_content': blog_content,
                'timestamp': datetime.now().isoformat()
            }
            
            config_path = Path('tmp/config.json')
            try:
                # Create tmp directory if it doesn't exist
                config_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Ensuring directory exists: {config_path.parent}")
                
                # Create or update the config file
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved blog content to config file: {config_path}")
                
                # Verify file was created
                if config_path.exists():
                    logger.info(f"Verified config file exists. Size: {config_path.stat().st_size} bytes")
                else:
                    logger.error(f"Failed to create config file at: {config_path.absolute()}")
                    
            except Exception as e:
                logger.error(f"Failed to save config file: {str(e)}")
                logger.error(f"Attempted to save at absolute path: {config_path.absolute()}")
                logger.error(f"Current working directory: {Path.cwd()}")
                raise  # Re-raise the exception for the outer try-catch block
            
            if not blog_content:
                logger.error("Failed to generate blog content")
                return "default.md", "Failed to generate content"
                
            logger.info("Generating metadata...")
            metadata = await self._generate_metadata(self.agent.image_prompt)
            logger.info(f"Generated metadata: {metadata}")
            
            logger.info("Formatting pages...")
            pages = self._format_pages(templates, metadata, blog_content, gallery_code)
            
            filename = self._generate_filename(metadata['filename'])
            blog_page = pages['blog_page']
            
            logger.info(f"Blog post generation completed successfully. Filename: {filename}")
            logger.info("=== Blog Post Generation Completed ===\n")
            
            return filename, blog_page
            
        except Exception as e:
            logger.error("=== Blog Post Generation Failed ===")
            logger.error(f"Error generating artist post: {str(e)}", exc_info=True)
            return "error.md", f"Error generating post: {str(e)}"

    async def _generate_image_file_paths(self) -> Dict[str, str]:
        new_timestamp = str(int(datetime.now().timestamp()))
        timestamp_manager.update(new_timestamp)
        
        current_timestamp = timestamp_manager.timestamp
        logger.info(f"SAVED IMAGE_TIMESTAMP: {current_timestamp}")
        
        return {
            'top_left': f"/images/ai_images/midjourney_{current_timestamp}_top_left.png",
            'top_right': f"/images/ai_images/midjourney_{current_timestamp}_top_right.png",
            'bottom_left': f"/images/ai_images/midjourney_{current_timestamp}_bottom_left.png",
            'bottom_right': f"/images/ai_images/midjourney_{current_timestamp}_bottom_right.png"
        }
    
    def _create_gallery_code(self, image_paths: Dict[str, str]) -> str:
        return "{{< gallery images=\"" + ",".join(image_paths.values()) + "\" >}}"

    def _format_prompt(self, agent_prompt: str, enhanced_prompt: str) -> str:
        formatted_prompt = agent_prompt.format(image_prompt=self.agent.image_prompt)
        return f"{formatted_prompt}\n\n{enhanced_prompt}"

    async def _generate_metadata(self, content: str) -> Dict[str, str]:
        return {
            'title': await self.agent.generate_title(content),
            'tags': await self.agent.generate_tags(content),
            'filename': await self.agent.generate_filename(content),
            'date': datetime.now().strftime('%Y-%m-%d')
        }

    def _format_pages(self, templates: Dict[str, str], metadata: Dict[str, str], 
                     content: str, gallery_code: str) -> Dict[str, str]:
        frontmatter = templates['frontmatter'].format(
            title=metadata['title'],
            tags=metadata['tags'],
            date=metadata['date'],
            author="AI Agent Dali"
        )

        return {
            'blog_page': templates['blog_template'].format(
                frontmatter=frontmatter,
                disclaimer=templates['disclaimer'],
                prompt=self.agent.image_prompt,
                content=content,
                gallery=gallery_code
            )
        }

    def _generate_filename(self, filename: str) -> str:
        return f"{datetime.now().strftime('%Y-%m-%d')}-{filename}.md"