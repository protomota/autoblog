import asyncio
import argparse
import logging
import sys
import traceback
import os
from datetime import datetime
from pathlib import Path

# Use absolute imports consistently
from ai_agents.core.config import (
    BLOG_RESEARCHER_AI_AGENT,
    BLOG_ARTIST_AI_AGENT,
    PROJECT_ROOT
)
from ai_agents.core.agent import BlogAgent

from services.process_image_service import ProcessImageService
from utils.validation import verify_paths, check_dependencies
from utils.path_utils import ensure_directory_structure
from services.openai_random_image_prompt_service import OpenAIRandomImagePromptService

# Configure logging
from ai_agents.core.config import logger

def setup_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Generate a blog post')
    parser.add_argument('--agent_name', type=str, required=True, help='AI Agent prompts directory name')
    parser.add_argument('--agent_type', type=str, required=True, help='Type of AI Agent')
    parser.add_argument('--topic', type=str, help='Research topic (required for researcher agent)')
    parser.add_argument('--image_prompt', type=str, help='Image prompt (required for artist agent)')
    parser.add_argument('--webhook_url', type=str, help='Webhook URL for artist agent')
    return parser

def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser):
    if args.agent_type == BLOG_ARTIST_AI_AGENT:
        if not args.webhook_url:
            parser.error("--webhook_url is required for artist agent")
    elif args.agent_type == BLOG_RESEARCHER_AI_AGENT:
        if not args.topic:
            parser.error("--topic is required for researcher agent")

async def generate_and_save_content(agent: BlogAgent):
    filename, blog_page = await agent.generate_blog_post()
    
    if not filename or not blog_page:
        logger.error("Failed to generate blog post")
        return False

    # Save blog post
    try:
        filepath = await agent.save_to_content(filename, blog_page)
        if not filepath:
            raise Exception("Failed to save blog post")
        print(f"GENERATED_FILE={filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save blog post: {e}")
        return False

async def main():
    start_time = datetime.now()

    try:
        # Initial checks
        if not check_dependencies() or not ensure_directory_structure():
            return 1

        # Parse and validate arguments
        parser = setup_argparser()
        args = parser.parse_args()
        validate_args(args, parser)

        # Verify paths for agent
        if not verify_paths(args.agent_name):
            logger.error("Path verification failed")
            return 1

        # Generate random image prompt if needed
        if args.agent_type == BLOG_ARTIST_AI_AGENT and not args.image_prompt:
            prompt_service = OpenAIRandomImagePromptService()
            args.image_prompt = prompt_service.generate_random_image_prompt()

        # Initialize image service for artist agent
        if args.agent_type == BLOG_ARTIST_AI_AGENT:
            ProcessImageService(
                agent_name=args.agent_name,
                webhook_url=args.webhook_url,
                image_prompt=args.image_prompt
            )

        # Generate blog post
        async with BlogAgent(
            agent_name=args.agent_name,
            agent_type=args.agent_type,
            topic=args.topic,
            image_prompt=args.image_prompt
        ) as agent:
            if not await generate_and_save_content(agent):
                return 1

        logger.info(f"Total execution time: {(datetime.now() - start_time).total_seconds():.2f} seconds")
        return 0

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1
    finally:
        if 'agent' in locals():
            await agent.cleanup()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))