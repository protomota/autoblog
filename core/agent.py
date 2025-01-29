import os
import logging
import anthropic
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from openai import OpenAI
 # Make sure this import is at the top

# Use absolute imports
from blogi.services.anthropic_service import AnthropicService
from blogi.services.brave_search_service import BraveSearchClient
from blogi.core.web_service import WebService
from blogi.generators.artist import ArtistPostGenerator
from blogi.generators.researcher import ResearcherPostGenerator
from blogi.services.process_image_service import ProcessImageService
from blogi.utils.validation import verify_paths, check_dependencies
from blogi.utils.path_utils import ensure_directory_structure
from blogi.services.openai_random_image_prompt_service import OpenAIRandomImagePromptService

# Configuration
from blogi.core.config import (
        logger, 
        CLAUDE_MODEL, 
        BLOG_RESEARCHER_AI_AGENT, 
        BLOG_ARTIST_AI_AGENT, 
        OBSIDIAN_AI_POSTS_PATH, 
        PROMPTS_DIR
    )

class BlogAgent:
    def __init__(self, agent_name: str, agent_type: str, topic: Optional[str] = None, 
                 image_prompt: Optional[str] = None, webhook_url: Optional[str] = None,
                 model: str = CLAUDE_MODEL):
        
        logger.info("\n=== Initializing BlogAgent ===")
        logger.info(f"Parameters:")
        logger.info(f"  - Agent Name: {agent_name}")
        logger.info(f"  - Agent Type: {agent_type}")
        logger.info(f"  - Topic: {topic}")
        logger.info(f"  - Image Prompt: {image_prompt}")
        logger.info(f"  - Webhook URL: {webhook_url}")
        
        self._validate_agent_type(agent_type)
        self._validate_requirements(agent_type, topic, webhook_url)
        
        self.web_service = WebService()
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.topic = topic
        self.image_prompt = image_prompt
        self.webhook_url = webhook_url
        self.model = model
        
        # Initialize as None
        self.sessions = []
        self.anthropic = None
        self.brave_client = None
        self._is_closed = False
        
        # Set up paths
        self._setup_paths()
        
        # Validate initialization
        self._validate_initialization()

    def _validate_agent_type(self, agent_type: str):
        """Validate the agent type."""
        valid_types = [BLOG_RESEARCHER_AI_AGENT, BLOG_ARTIST_AI_AGENT]
        if agent_type not in valid_types:
            raise ValueError(f"Invalid agent_type: {agent_type}. Must be one of: {valid_types}")

    def _validate_requirements(self, agent_type: str, topic: Optional[str], webhook_url: Optional[str]):
        """Validate agent-specific requirements."""
        if agent_type == BLOG_RESEARCHER_AI_AGENT and not topic:
            raise ValueError("Topic is required for researcher agent")
        if agent_type == BLOG_ARTIST_AI_AGENT and not webhook_url:
            raise ValueError("Webhook URL is required for artist agent")

    def _setup_paths(self):
        """Set up all required paths."""
        # Set up paths for templates and prompts
        prompts_base = PROMPTS_DIR
        agent_prompts = os.path.join(prompts_base, self.agent_name)
        common_prompts = os.path.join(prompts_base, "_common")

        # Agent-specific paths
        self.agent_prompt_path = os.path.join(agent_prompts, "agent_prompt.txt")
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

    @classmethod
    async def create(cls, agent_type, agent_name, topic=None, image_prompt=None, webhook_url=None):
        """Create a blog post using the specified agent."""
        try:
            # Create an instance of BlogAgent
            agent = cls(
                agent_type=agent_type,
                agent_name=agent_name,
                topic=topic,
                image_prompt=image_prompt,
                webhook_url=webhook_url
            )
            
            # Generate the blog post using the appropriate generator
            generator = (
                ArtistPostGenerator(agent) if agent_type == BLOG_ARTIST_AI_AGENT
                else ResearcherPostGenerator(agent)
            )
            
            # Use context manager and call the appropriate method
            async with agent:  # Use context manager to handle initialization and cleanup
                # Both generators use generate_blog_post()
                result = await generator.generate_blog_post()
                
                if isinstance(result, tuple):
                    filepath = result[0] if result else None
                else:
                    filepath = result
                    
                if filepath:
                    return True, "Blog post generated successfully", str(filepath)
                else:
                    return False, "Failed to generate blog post", None
                
        except Exception as e:
            error_msg = f"Error in blog generation: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    def _validate_initialization(self):
        if not os.getenv('ANTHROPIC_API_KEY'):
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        if self.agent_type not in [BLOG_ARTIST_AI_AGENT, BLOG_RESEARCHER_AI_AGENT]:
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
            
            if self.agent_type == BLOG_RESEARCHER_AI_AGENT:
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
                ArtistPostGenerator(self) if self.agent_type == BLOG_ARTIST_AI_AGENT
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
        """Generate a blog post using the appropriate generator."""
        try:
            generator = (
                ArtistPostGenerator(self) if self.agent_type == BLOG_ARTIST_AI_AGENT
                else ResearcherPostGenerator(self)
            )
            return await generator.generate_blog_post()  # Both generators use generate_blog_post()
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
            return f'{response.replace('"', "").strip()}' if response else default_title
        except Exception as e:
            logger.error(f"Title generation error: {str(e)}")
            return default_title

    async def generate_filename(self, content: str) -> str:
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
        
    async def save_to_obsidian_notes(self, filename: str, content: str) -> Optional[str]:
        """Save content to an Post."""
        try:
            # Ensure filename is a string
            if isinstance(filename, tuple):
                filename = filename[0] if filename else "default.md"
            
            # Ensure filename has .md extension
            if not filename.endswith('.md'):
                filename = f"{filename}.md"
            
            # Create directory if it doesn't exist
            OBSIDIAN_AI_POSTS_PATH.mkdir(parents=True, exist_ok=True)
            
            # Create full filepath
            obsidian_ai_posts_filepath = OBSIDIAN_AI_POSTS_PATH / filename
            
            # Write content to file
            async with aiofiles.open(obsidian_ai_posts_filepath, mode='w') as file:
                await file.write(content)
            
            logger.info(f"Successfully saved to {obsidian_ai_posts_filepath}")
            # Output the file path in the format expected by deploy_manager
            print(f"POST_FILE_PATH={obsidian_ai_posts_filepath}")
            return str(obsidian_ai_posts_filepath)
        except Exception as e:
            logger.error(f"Error saving to Posts: {str(e)}")
            return None

    async def close(self):
        """Clean up any resources used by the agent."""
        if hasattr(self, 'client') and self.client:
            await self.client.close()