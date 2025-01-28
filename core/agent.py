import os
import logging
import anthropic
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Use absolute imports
from blogi.services.anthropic_service import AnthropicService
from blogi.services.brave_search_service import BraveSearchClient
from blogi.core.web_service import WebService
from blogi.generators.artist_post import ArtistPostGenerator
from blogi.generators.researcher_post import ResearcherPostGenerator
from blogi.core.config import CLAUDE_MODEL, PROJECT_ROOT, AI_POSTS_PATH

# Configure logging
from blogi.core.config import logger

class BlogAgent:
    def __init__(self, agent_name: str, agent_type: str, topic: Optional[str] = None, 
                 image_prompt: Optional[str] = None, model: str = CLAUDE_MODEL):
        
        # Initialize project root
        
        self.web_service = WebService()
        
        # Basic attributes
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.topic = topic
        self.image_prompt = image_prompt
        self.model = model
        
        # Initialize as None
        self.sessions = []
        self.anthropic = None
        self.brave_client = None
        self._is_closed = False
        
        # Set up paths for templates and prompts
        prompts_base = PROJECT_ROOT / "blogi" / "prompts"
        agent_prompts = os.path.join(prompts_base, agent_name)
        common_prompts = os.path.join(prompts_base, "_common")

        # Set up paths
        self.agent_prompt_path = os.path.join(agent_prompts, "agent-prompt.txt")
        self.enhanced_prompt_path = os.path.join(agent_prompts, "enhanced_prompt.txt")
        self.disclaimer_path = os.path.join(agent_prompts, "disclaimer.txt")
        self.blog_page_template_path = os.path.join(agent_prompts, "blog_page_template.md")
        
        # Base paths    
        self.base_prompts_path = Path(agent_prompts)
        self.common_prompts_path = Path(common_prompts)
        
        # Common templates
        self.frontmatter_path = os.path.join(common_prompts, "frontmatter.md")
        self.tags_prompt_path = self.common_prompts_path / "tags_prompt.txt"
        self.title_prompt_path = self.common_prompts_path / "summarize_for_title.txt"
        self.five_words_prompt_path = self.common_prompts_path / "five_word_summary.txt"
        self.summarize_content_path = self.common_prompts_path / "summarize_content.txt"
        
        # Validate initialization
        self._validate_initialization()

    def _validate_initialization(self):
        if not os.getenv('ANTHROPIC_API_KEY'):
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        if self.agent_type not in ["blog_artist_ai_agent", "blog_researcher_ai_agent"]:
            raise ValueError(f"Invalid agent_type: {self.agent_type}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_services()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def create_session(self):
        """Create and track a new client session."""
        session = aiohttp.ClientSession()
        self.sessions.append(session)
        return session

    async def initialize_services(self):
        """Initialize all required services."""
        if self._is_closed:
            raise RuntimeError("Agent has been closed")
            
        try:
            # Create main session
            main_session = await self.create_session()
            
            # Initialize services
            self.anthropic = AnthropicService(self.model)
            if hasattr(self.anthropic, 'session'):
                self.anthropic.session = await self.create_session()
            
            if self.agent_type == "blog_researcher_ai_agent":
                self.brave_client = BraveSearchClient()
                self.brave_client.session = await self.create_session()
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            await self.cleanup()
            raise

    async def cleanup(self):
        """Cleanup all resources."""
        if self._is_closed:
            return

        errors = []
        try:
            # Close all tracked sessions
            for session in self.sessions:
                try:
                    if session and not session.closed:
                        await session.close()
                except Exception as e:
                    errors.append(f"Error closing session: {str(e)}")
            
            if self.anthropic:
                try:
                    await self.anthropic.cleanup()
                except Exception as e:
                    errors.append(f"Error cleaning up anthropic: {str(e)}")
            
            if self.brave_client and hasattr(self.brave_client, 'cleanup'):
                try:
                    await self.brave_client.cleanup()
                except Exception as e:
                    errors.append(f"Error cleaning up brave client: {str(e)}")
        except Exception as e:
            errors.append(f"Error during cleanup: {str(e)}")
        finally:
            if errors:
                logger.error("Cleanup errors occurred:\n" + "\n".join(errors))
            self._is_closed = True
            self.sessions = []
            self.anthropic = None
            self.brave_client = None

    async def process(self):
        """Main processing method."""
        async with self:
            return await self.run()

    async def run(self):
        try:
            generator = (
                ArtistPostGenerator(self) if self.agent_type == "blog_artist_ai_agent"
                else ResearcherPostGenerator(self)
            )
            return await generator.generate()
        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            return None

    async def read_file(self, filepath: str) -> Optional[str]:
        """Read a file asynchronously."""
        try:
            async with aiofiles.open(filepath, mode='r') as file:
                return await file.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return None

    async def generate_blog_post(self):
        try:
            generator = (
                ArtistPostGenerator(self) if self.agent_type == "blog_artist_ai_agent"
                else ResearcherPostGenerator(self)
            )
            return await generator.generate()
        finally:
            await self.close()
    
    async def generate_title(self, content: str) -> str:
        """Generate a title from the content."""
        default_title = "Default Title Post Is Here"
        if not content:
            return default_title
            
        try:
            prompt = await self.read_file(str(self.title_prompt_path))
            response = await self.anthropic.ask(prompt.format(content=content))
            return response.strip().strip('"\'') if response else default_title
        except Exception as e:
            logger.error(f"Title generation error: {str(e)}")
            return default_title

    async def generate_title_summary(self, content: str) -> str:
        """Generate a 5-word summary for use in the filename."""
        default_title = "Default-Title-Post-Is-Here"
        try:
            prompt = await self.read_file(str(self.five_words_prompt_path))
            response = await self.anthropic.ask(prompt.format(content=content))
            if response:
                summary = response.strip().replace(' ', '-')
                words = summary.split('-')
                return '-'.join(words[:5] if len(words) > 5 else words + ['Update'] * (5 - len(words)))
            return default_title
        except Exception as e:
            logger.error(f"Title summary generation error: {str(e)}")
            return default_title

    async def generate_tags(self, content: str) -> str:
        """Generate tags for the content."""
        try:
            tags_prompt = await self.read_file(str(self.tags_prompt_path))
            return await self.anthropic.ask(tags_prompt.format(content=content))
        except Exception as e:
            logger.error(f"Tags generation error: {str(e)}")
            return "[]"
        
    async def save_to_content(self, filename: str, content: str) -> Optional[str]:
        """Save content to an Post."""
        try:
            AI_POSTS_PATH.mkdir(parents=True, exist_ok=True)
            filepath = AI_POSTS_PATH / filename
            
            async with aiofiles.open(filepath, mode='w') as file:
                await file.write(content)
            
            logger.info(f"Successfully saved to {filepath}")
            # Output the file path in the format expected by deploy_manager
            print(f"FILE_PATH={filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving to Posts: {str(e)}")
            return None

    async def close(self):
        """Clean up any resources used by the agent."""
        if hasattr(self, 'client') and self.client:
            await self.client.close()