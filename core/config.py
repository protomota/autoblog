import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup Source Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up one more level to reach protomota root

# Add to Python path
sys.path.append(str(PROJECT_ROOT))

# Handle optional environment variables with default values or None checks
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", None)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
USERAPI_AI_API_KEY = os.getenv("USERAPI_AI_API_KEY", None)
USERAPI_AI_ACCOUNT_HASH = os.getenv("USERAPI_AI_ACCOUNT_HASH", None)
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', None)

BLOG_URL = os.getenv("BLOG_URL", None)

OBSIDIAN_NOTES_PATH = Path(os.getenv("OBSIDIAN_NOTES_PATH", "")) if os.getenv("OBSIDIAN_NOTES_PATH") else None

# Setup Long Paths
BLOGI_ROOT = PROJECT_ROOT / "blogi"
sys.path.append(str(BLOGI_ROOT))

BLOG_SITE_REPO = os.getenv("BLOG_SITE_REPO", "my_blog")

BLOG_SITE_PATH = PROJECT_ROOT / BLOG_SITE_REPO
BLOG_SITE_STATIC_IMAGES_PATH = BLOG_SITE_PATH / "static" / "images"
BLOG_SITE_STATIC_AI_IMAGES_PATH = BLOG_SITE_PATH / "static" / "images" / "ai_images"
BLOG_SITE_POSTS_PATH = BLOG_SITE_PATH / "content" / "posts"
PROMPTS_DIR = PROJECT_ROOT / "blogi" / "prompts"

OBSIDIAN_AI_POSTS_PATH = OBSIDIAN_NOTES_PATH / "ai_posts"
OBSIDIAN_AI_IMAGES = OBSIDIAN_NOTES_PATH / "images" / "ai_images"
OBSIDIAN_POSTS_PATH = OBSIDIAN_NOTES_PATH / "posts"
OBSIDIAN_IMAGES_PATH = OBSIDIAN_NOTES_PATH / "images"


# Agent Types
BLOG_RESEARCHER_AI_AGENT = "blog_researcher_ai_agent"
BLOG_ARTIST_AI_AGENT = "blog_artist_ai_agent"
BLOG_RESEARCHER_TOPIC_ENGINEER = "topic_engineer"
BLOG_RESEARCHER_TOPIC_RESEARCHER = "topic_researcher"
BLOG_ARTIST_PROMPT_ARTIST = "prompt_artist"
BLOG_ARTIST_RANDOM_PROMPT_ARTIST = "random_prompt_artist"



# API Config
CLAUDE_MODEL = "claude-3-haiku-20240307"
OPENAI_MODEL = "gpt-4o-mini"

MIDJOURNEY_ASPECT_RATIO = "7:4"
MIDJOURNEY_CHAOS_PERCENTAGE = "0"  # Default value, will be overridden by UI
    
USERAPI_AI_API_BASE_URL = "https://api.userapi.ai/midjourney/v2"   

BRAVE_SEARCH_TIMEOUT = 30
MAX_SEARCH_RESULTS = 3

# Debug mode flag - set to True to enable DEBUG logging
DEBUG_MODE = False

# Set base logging level based on DEBUG_MODE
BASE_LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'

BLOG_AGENT_TYPES = [
    BLOG_RESEARCHER_AI_AGENT, 
    BLOG_ARTIST_AI_AGENT
]
BLOG_AGENT_NAMES = {
    BLOG_RESEARCHER_AI_AGENT: [BLOG_RESEARCHER_TOPIC_ENGINEER, BLOG_RESEARCHER_TOPIC_RESEARCHER],
    BLOG_ARTIST_AI_AGENT: [BLOG_ARTIST_PROMPT_ARTIST, BLOG_ARTIST_RANDOM_PROMPT_ARTIST]
}

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

class FilenameManager:
    def __init__(self):
        self._filename = "0000000000"
    
    @property
    def filename(self):
        return self._filename
    
    def update(self, new_filename: str):
        self._filename = new_filename
        logger.info(f"Updated IMAGE_FILENAME to: {self._filename}")

class ChaosPercentageManager:
    def __init__(self):
        self._chaos_percentage = "0"
    
    @property
    def chaos_percentage(self):
        return self._chaos_percentage
    
    def update(self, new_percentage: str):
        self._chaos_percentage = new_percentage
        logger.info(f"Updated MIDJOURNEY_CHAOS_PERCENTAGE to: {self._chaos_percentage}")

# Create instances
filename_manager = FilenameManager()
chaos_percentage_manager = ChaosPercentageManager()