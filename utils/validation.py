import shutil
import logging
import os
from pathlib import Path
from blogi.core.config import logger, PROJECT_ROOT

def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    logger.info("Checking system dependencies...")
    
    # List of required command-line tools
    dependencies = [
        'git',  # For version control
        'hugo'  # For static site generation
    ]
    
    missing_deps = []
    
    for dep in dependencies:
        if shutil.which(dep) is None:
            logger.error(f"Missing dependency: {dep}")
            missing_deps.append(dep)
        else:
            logger.info(f"Found dependency: {dep}")
    
    if missing_deps:
        logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
        return False
    
    logger.info("All dependencies found")
    return True

def verify_paths(agent_name: str) -> bool:
    """Verify that all required paths exist and create them if they don't."""
    logger.info(f"Verifying paths for agent: {agent_name}")
    
    # Use absolute paths based on PROJECT_ROOT
    required_paths = [
        Path(PROJECT_ROOT) / "prompts" / agent_name,
        Path(PROJECT_ROOT) / "content",
        Path(PROJECT_ROOT) / "static"
    ]
    
    for path in required_paths:
        logger.info(f"Checking path: {path}")
        if not path.exists():
            logger.info(f"Creating directory: {path}")
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Successfully created directory: {path}")
            except Exception as e:
                logger.error(f"Failed to create directory {path}: {str(e)}")
                return False
        else:
            logger.info(f"Found existing path: {path}")
    
    logger.info("All required paths verified/created")
    return True