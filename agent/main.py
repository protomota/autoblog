import asyncio
import argparse
import logging
import sys
import traceback
import os
from datetime import datetime
from pathlib import Path

# Add the parent directory of the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up one more level to include the project root
sys.path.append(str(PROJECT_ROOT))

print(f"Debug - Current sys.path: {sys.path}")  # Debug print to see Python path
print(f"Debug - Project root: {PROJECT_ROOT}")   # Debug print to verify project root

# Now import the logger
from blogi.core.config import logger

logger.info("\n=== Starting Blog Generation Script ===")
logger.info(f"Script started at: {datetime.now()}")
logger.info(f"Project root: {PROJECT_ROOT}")
logger.info(f"Python path: {sys.path}")

# Use absolute imports consistently
from blogi.core.config import (
    BLOG_RESEARCHER_AI_AGENT,
    BLOG_ARTIST_AI_AGENT
)
from blogi.core.agent import BlogAgent

from blogi.services.process_image_service import ProcessImageService
from blogi.utils.validation import verify_paths, check_dependencies
from blogi.utils.path_utils import ensure_directory_structure
from blogi.services.openai_random_image_prompt_service import OpenAIRandomImagePromptService

def setup_argparser() -> argparse.ArgumentParser:
    logger.info("Setting up argument parser")
    parser = argparse.ArgumentParser(description='Generate a blog post')
    parser.add_argument('--agent_name', type=str, required=True, help='AI Agent prompts directory name')
    parser.add_argument('--agent_type', type=str, required=True, help='Type of AI Agent')
    parser.add_argument('--topic', type=str, help='Research topic (required for researcher agent)')
    parser.add_argument('--image_prompt', type=str, help='Image prompt (required for artist agent)')
    parser.add_argument('--webhook_url', type=str, help='Webhook URL for artist agent')
    logger.info("Argument parser setup complete")
    return parser

def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser):
    logger.info("\n=== Validating Arguments ===")
    logger.info(f"Received arguments: {args}")
    
    # Add valid agent types check
    valid_agent_types = [BLOG_RESEARCHER_AI_AGENT, BLOG_ARTIST_AI_AGENT]
    logger.info(f"Checking agent type. Valid types: {valid_agent_types}")
    if args.agent_type not in valid_agent_types:
        logger.error(f"Invalid agent type: {args.agent_type}")
        parser.error(f"--agent_type must be one of: {', '.join(valid_agent_types)}")
    
    # Existing validation
    if args.agent_type == BLOG_ARTIST_AI_AGENT:
        logger.info("Validating artist agent requirements")
        if not args.webhook_url:
            logger.error("Missing webhook URL for artist agent")
            parser.error("--webhook_url is required for artist agent")
    elif args.agent_type == BLOG_RESEARCHER_AI_AGENT:
        logger.info("Validating researcher agent requirements")
        if not args.topic:
            logger.error("Missing topic for researcher agent")
            parser.error("--topic is required for researcher agent")
    
    logger.info("Arguments validation successful")

async def generate_and_save_content(agent: BlogAgent):
    logger.info("\n=== Starting Content Generation ===")
    try:
        logger.info("Generating blog post")
        result = await agent.generate_blog_post()
        
        if not result:
            logger.error("Blog post generation returned no result")
            return False

        filename, blog_page = result
        logger.info(f"Blog post generated successfully")
        logger.info(f"Generated filename: {filename}")
        
        # Save blog post
        logger.info("Saving blog post to content directory")
        filepath = await agent.save_to_content(filename, blog_page)
        if not filepath:
            logger.error("Failed to save blog post - no filepath returned")
            raise Exception("Failed to save blog post")
        
        logger.info(f"Blog post saved successfully at: {filepath}")
        print(f"GENERATED_FILE={filename}")
        return True
    except Exception as e:
        logger.error(f"Error in generate_and_save_content: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False

async def main():
    start_time = datetime.now()
    logger.info(f"\n=== Main Process Started at {start_time} ===")

    try:
        # Initial checks
        logger.info("Performing initial system checks")
        if not check_dependencies():
            logger.error("Dependency check failed")
            return 1
        if not ensure_directory_structure():
            logger.error("Directory structure check failed")
            return 1
        logger.info("Initial checks passed successfully")

        # Parse and validate arguments
        logger.info("Setting up and validating arguments")
        parser = setup_argparser()
        args = parser.parse_args()
        logger.info(f"Parsed arguments: {args}")
        validate_args(args, parser)

        # Verify paths for agent
        logger.info(f"Verifying paths for agent: {args.agent_name}")
        if not verify_paths(args.agent_name):
            logger.error("Path verification failed")
            return 1
        logger.info("Path verification successful")

        # Generate random image prompt if needed
        if args.agent_type == BLOG_ARTIST_AI_AGENT and not args.image_prompt:
            logger.info("Generating random image prompt for artist agent")
            prompt_service = OpenAIRandomImagePromptService()
            args.image_prompt = prompt_service.generate_random_image_prompt()
            logger.info(f"Generated image prompt: {args.image_prompt}")

        # Initialize image service for artist agent
        if args.agent_type == BLOG_ARTIST_AI_AGENT:
            logger.info("Initializing image service for artist agent")
            image_service = ProcessImageService(
                agent_name=args.agent_name,
                webhook_url=args.webhook_url,
                image_prompt=args.image_prompt
            )
            logger.info("Image service initialized successfully")

        # Generate blog post
        logger.info("Initializing blog agent")
        async with BlogAgent(
            agent_name=args.agent_name,
            agent_type=args.agent_type,
            topic=args.topic,
            image_prompt=args.image_prompt
        ) as agent:
            logger.info("Starting content generation")
            if not await generate_and_save_content(agent):
                logger.error("Content generation failed")
                return 1
            logger.info("Content generation completed successfully")

        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        return 0

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return 1
    finally:
        if 'agent' in locals():
            logger.info("Cleaning up agent resources")
            await agent.cleanup()
            logger.info("Cleanup completed")

if __name__ == "__main__":
    logger.info("\n=== Script Execution Started ===")
    exit_code = asyncio.run(main())
    logger.info(f"Script completed with exit code: {exit_code}")
    sys.exit(exit_code)