from pathlib import Path
import logging

# Configure logging
from blogi.core.config import logger

def ensure_directory_structure() -> bool:
    try:
        required_dirs = {
            'content': Path("content"),
            'utils': Path("utils"),
            'prompts': Path("prompts")
        }
        
        for dir_path in required_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        return True
    except Exception as e:
        logger.error(f"Directory structure error: {str(e)}")
        return False