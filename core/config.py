import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup Source Paths
PROJECT_ROOT = Path(__file__).parent.parent
BLOGI_ROOT = Path(__file__).parent

# Add to Python path
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(BLOGI_ROOT))

# Setup Environment Variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USERAPI_AI_API_KEY = os.getenv("USERAPI_AI_API_KEY")
USERAPI_AI_ACCOUNT_HASH = os.getenv("USERAPI_AI_ACCOUNT_HASH")

OBSIDIAN_NOTES_PATH = os.getenv("OBSIDIAN_NOTES_PATH")
PROJECT_ROOT_ENV = os.getenv("PROJECT_ROOT")  # Renamed to avoid conflict
HUMAN_BLOG_URL = os.getenv("HUMAN_BLOG_URL")
AI_BLOG_URL = os.getenv("AI_BLOG_URL")

# Convert PROJECT_ROOT_ENV to Path if it exists, otherwise use PROJECT_ROOT
PROJECT_ROOT_PATH = Path(PROJECT_ROOT_ENV) if PROJECT_ROOT_ENV else PROJECT_ROOT

# Setup Long Paths
HUMAN_BLOG_SITE_PATH = PROJECT_ROOT_PATH / "human_blog"
HUMAN_BLOG_SITE_STATIC_IMAGES_PATH = HUMAN_BLOG_SITE_PATH / "static" / "images"
HUMAN_POSTS_PATH = HUMAN_BLOG_SITE_PATH / "content" / "posts"
AI_BLOG_SITE_PATH = PROJECT_ROOT_PATH / "ai_blog"
AI_BLOG_SITE_STATIC_IMAGES_PATH = AI_BLOG_SITE_PATH / "static" / "images"
AI_POSTS_PATH = AI_BLOG_SITE_PATH / "content" / "posts"
OBSIDIAN_AI_POSTS_PATH = OBSIDIAN_NOTES_PATH / "ai_posts"
OBSIDIAN_AI_IMAGES_PATH = OBSIDIAN_AI_POSTS_PATH / "images"
OBSIDIAN_HUMAN_POSTS_PATH = OBSIDIAN_NOTES_PATH / "posts"
OBSIDIAN_HUMAN_IMAGES_PATH = OBSIDIAN_NOTES_PATH / "images"
PROMPTS_DIR = BLOGI_ROOT / "prompts"

# Agent Types
BLOG_RESEARCHER_AI_AGENT = "blog_researcher_ai_agent"
BLOG_ARTIST_AI_AGENT = "blog_artist_ai_agent"
BLOG_RESEARCHER_TOPIC_ENGINEER = "topic_engineer"
BLOG_RESEARCHER_TOPIC_RESEARCHER = "topic_researcher"
BLOG_ARTIST_PROMPT_ARTIST = "prompt_artist"
BLOG_ARTIST_RANDOM_PROMPT_ARTIST = "random_prompt_artist"

# API Config
CLAUDE_MODEL = "claude-3-haiku-20240307"
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