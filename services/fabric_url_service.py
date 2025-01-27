import subprocess
import urllib.parse

# Configure logging
from blogi.core.config import logger

class FabricService:
    """Service for handling Fabric URL processing and command execution."""
    
    @staticmethod
    def extract_wisdom_of_url(url: str) -> str:
        """
        Executes a Fabric command for the given URL using AppleScript.
        
        Args:
            url (str): The URL to process with Fabric
            
        Returns:
            str: The output from the Fabric command
        """
        # Encode URL to handle special characters
        encoded_url = urllib.parse.quote(url)
        
        # AppleScript command to open Terminal and run fabric
        apple_script = f'''
        tell application "Terminal"
            activate
            set result to do shell script "fabric -u \\"{encoded_url}\\" | extract_wisdom"
            return result
        end tell
        '''
        
        # Execute AppleScript and capture the output
        result = subprocess.run(
            ['osascript', '-e', apple_script],
            capture_output=True,
            text=True
        )
        
        return result.stdout.strip()

# Example usage (commented out)
# if __name__ == "__main__":
#     url = "https://example.com"
#     FabricUrlService.extract_wisdom_of_url(url)