import aiofiles
import logging
import sys
from pathlib import Path
from typing import Optional

# Configure logging
from ai_agents.core.config import logger

async def read_file(filepath: str) -> Optional[str]:
    try:
        async with aiofiles.open(filepath, mode='r') as file:
            return await file.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {str(e)}")
        return None

async def save_file(filepath: Path, content: str) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(filepath, mode='w') as file:
            await file.write(content)
        return True
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return False