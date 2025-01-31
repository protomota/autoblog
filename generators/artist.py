from datetime import datetime
from typing import Tuple, Optional, Dict
from pathlib import Path
import os

# Configure logging
from blogi.core.config import logger, PROJECT_ROOT

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
        try:
            templates = await self._load_templates()
            image_paths = await self._generate_image_file_paths()
            gallery_code = self._create_gallery_code(image_paths)
            
            blog_content = await self.agent.anthropic.ask(
                self._format_prompt(templates['agent_prompt'], templates['enhanced_prompt'])
            )
            
            if not blog_content:
                return "default.md", "Failed to generate content"
                
            metadata = await self._generate_metadata(self.agent.image_prompt)
            pages = self._format_pages(templates, metadata, blog_content, gallery_code)
            
            filename = self._generate_filename(metadata['filename'])
            blog_page = pages['blog_page']
            
            return filename, blog_page
            
        except Exception as e:
            logger.error(f"Error generating artist post: {str(e)}")
            return "error.md", f"Error generating post: {str(e)}"

    async def _generate_image_file_paths(self) -> Dict[str, str]:
        image_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        os.environ['IMAGE_TIMESTAMP'] = image_timestamp

        saved_timestamp = os.getenv('IMAGE_TIMESTAMP')

        logger.info(f"SAVED IMAGE_TIMESTAMP: {saved_timestamp}")
        breakpoint()

        return {
            'top_left': f"images/{image_timestamp}_top_left.png",
            'top_right': f"images/{image_timestamp}_top_right.png",
            'bottom_left': f"images/{image_timestamp}_bottom_left.png",
            'bottom_right': f"images/{image_timestamp}_bottom_right.png"
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