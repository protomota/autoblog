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

    async def generate(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            templates = await self._load_templates()
            image_paths = await self._generate_images()
            gallery_code = self._create_gallery_code(image_paths)
            
            blog_content = await self.agent.anthropic.ask(
                self._format_prompt(templates['agent_prompt'], templates['enhanced_prompt'])
            )
            
            if not blog_content:
                return None, None, None
                
            metadata = await self._generate_metadata(self.agent.image_prompt)
            pages = self._format_pages(templates, metadata, blog_content, gallery_code)
            
            return (
                self._generate_filename(metadata['title_summary']),
                pages['blog_page']
            )
        except Exception as e:
            logger.error(f"Error generating artist post: {str(e)}")
            return None, None, None

    async def _generate_images(self) -> Dict[str, str]:
        current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        await self._save_timestamp(current_timestamp)
        
        return {
            'top_left': f"/images/openmid/openmid_{current_timestamp}_top_left.png",
            'top_right': f"/images/openmid/openmid_{current_timestamp}_top_right.png",
            'bottom_left': f"/images/openmid/openmid_{current_timestamp}_bottom_left.png",
            'bottom_right': f"/images/openmid/openmid_{current_timestamp}_bottom_right.png"
        }

    async def _save_timestamp(self, timestamp: str):
        temp_dir = PROJECT_ROOT / "tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        timestamp_file = temp_dir / "current_image_timestamp.txt"
        timestamp_file.write_text(timestamp)

    def _create_gallery_code(self, image_paths: Dict[str, str]) -> str:
        return "{{< gallery images=\"" + ",".join(image_paths.values()) + "\" >}}"

    def _format_prompt(self, agent_prompt: str, enhanced_prompt: str) -> str:
        formatted_prompt = agent_prompt.format(image_prompt=self.agent.image_prompt)
        return f"{formatted_prompt}\n\n{enhanced_prompt}"

    async def _generate_metadata(self, content: str) -> Dict[str, str]:
        return {
            'title': await self.agent.generate_title(content),
            'tags': await self.agent.generate_tags(content),
            'title_summary': await self.agent.generate_title_summary(content),
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

    def _generate_filename(self, title_summary: str) -> str:
        return f"{datetime.now().strftime('%Y-%m-%d')}-{title_summary}.md"