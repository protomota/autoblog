from dotenv import load_dotenv
load_dotenv()

import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
claude = os.getenv('ANTHROPIC_API_KEY')

print(project_root)
print(claude)
