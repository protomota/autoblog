import subprocess
import logging
from pathlib import Path
import os

# Configure logging
from blogi.core.config import logger

def check_dependencies() -> bool:
    required_commands = ['git', 'rsync', 'python', 'hugo']
    for cmd in required_commands:
        if subprocess.run(['which', cmd], capture_output=True).returncode != 0:
            logging.error(f"Missing dependency: {cmd}")
            return False
    return True

def verify_paths(agent_name: str) -> bool:
    try:
        # Get the project root (two levels up from this file)
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        project_root = current_dir.parent.parent

        required_paths = {
            'base_prompts': project_root / "blogi" / "prompts" / agent_name,
            'agent_prompt': project_root / "blogi" / "prompts" / agent_name / "agent_prompt.txt",
            'enhanced_prompt': project_root / "blogi" / "prompts" / agent_name / "enhanced_prompt.txt",
            'disclaimer': project_root / "blogi" / "prompts" / agent_name / "disclaimer.txt",
            'five_words_prompt': project_root / "blogi" / "prompts" / "_common" / "five_word_summary.txt",
            'summarize_content': project_root / "blogi" / "prompts" / "_common" / "summarize_content.txt"
        }
        
        for name, path in required_paths.items():
            if not path.exists():
                logger.error(f"Required path not found: {path}")
                return False
        return True
    except Exception as e:
        logging.error(f"Path verification error: {str(e)}")
        return False