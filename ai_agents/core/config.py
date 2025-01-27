import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import logging

# Add project root to Python path
PROJECT_ROOT = Path(os.getenv('PROTOBLOG_PROJECT_ROOT'))
if not PROJECT_ROOT:
    raise ValueError("PROTOBLOG_PROJECT_ROOT environment variable is not set")
sys.path.append(str(PROJECT_ROOT))

# Load environment variables
load_dotenv()

# Agent Types
BLOG_RESEARCHER_AI_AGENT = "blog_researcher_ai_agent"
BLOG_ARTIST_AI_AGENT = "blog_artist_ai_agent"
BLOG_RESEARCHER_TOPIC_ENGINEER = 'topic_engineer'
BLOG_RESEARCHER_TOPIC_RESEARCHER = 'topic_researcher'
BLOG_ARTIST_PROMPT_ARTIST = 'prompt_artist'
BLOG_ARTIST_RANDOM_PROMPT_ARTIST = 'random_prompt_artist'

# Paths
POSTS_PATH = PROJECT_ROOT / "content" / "posts"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

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