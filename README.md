# Guide to implementing protoblog AI Agent Blog Post Generator and Deployment Pipeline

This project implements an automated system for researching topics, generating blog posts using AI, creating AI-generated images, and deploying them to a website. It combines Claude AI's research capabilities, OpenAI's image prompt generation, and Midjourney's image creation with web research and automated deployment processes.

Blog Site: [https://blog.protomota.com/](https://blog.protomota.com/)

For instructions on how this site was created, please read here: [https://blog.protomota.com/posts/2025-01-13-hugo-blog-pipeline/](https://blog.protomota.com/posts/2025-01-13-hugo-blog-pipeline/)

## Overview

The system consists of three main components:

1. `blog_researcher_ai_agent.py`: A Python script that handles topic research and content generation
2. `blog_artist_ai_agent.py`: A Python script that generates AI art using OpenAI for prompts and Midjourney for image creation
3. `megascript.sh`: A shell script that orchestrates the entire process from content generation to website deployment

## Features

- Automated web research using Brave Search API
- Content generation using Claude AI (Anthropic)
- AI image generation using OpenAI (prompts) and Midjourney (images)
- Markdown file generation for Obsidian compatibility
- Automatic website building and deployment using Hugo
- Git-based version control and deployment
- Support for multiple AI agent configurations
- Automated image processing and link handling
- Notification system for process status
- Webhook server for handling Midjourney image generation callbacks

## Prerequisites

- Python 3.x
- Zsh shell
- Hugo static site generator
- Git
- Obsidian (for note storage)
- Required Python packages:
  - anthropic
  - aiohttp
  - aiofiles
  - beautifulsoup4
  - python-dotenv
  - flask
  - pillow
  - openai

## Environment Setup

After GIT clone, make sure to make the shell scripts executable.
```shell
chmod +x after_image_load.sh
chmod +x megascript.sh
chmod +x generate_image_post.sh
```

Create a `.env` file with the following credentials and paths:
```
# API Credentials
ANTHROPIC_API_KEY=your_anthropic_api_key
BRAVE_SEARCH_API_KEY=your_brave_search_api_key
OPENAI_API_KEY=your_openai_api_key
USERAPI_AI_API_KEY=your_midjourney_api_key
USERAPI_AI_ACCOUNT_HASH=your_midjourney_account_hash

# Image Sync Paths
SITE_OBSIDIAN_POSTS_DIR=/path/to/obsidian/folder
SITE_STATIC_IMAGES_DIR=/path/to/site/static/images
```

## Directory Structure

```
.
├── ai_agents/
│   ├── blog_researcher_ai_agent.py
│   └── blog_artist_ai_agent.py
├── helpers/
│   ├── midjourney_image_service.py
│   ├── openai_random_image_prompt_service.py
│   └── obsidian_image_sync.py
├── prompts/
│   ├── common/
│   │   ├── five-word-summary.txt
│   │   └── summarize-content.txt
│   └── [agent_name]/
│       ├── agent-prompt.txt
│       ├── enhanced-prompt.txt
│       └── disclaimer.txt
├── content/
├── public/
├── megascript.sh
└── midjourney_webhook_server.py
```

## Usage

### Setting Up NGROK for Midjourney Webhooks

For testing purposes, NGROK is recommended to provide Midjourney API with a public endpoint for POST callbacks:

1. Install NGROK:
```bash
# On Mac with Homebrew
brew install ngrok

# Or download from https://ngrok.com/download
```
2. In another terminal, create an NGROK tunnel:
```bash
ngrok http 9119
```
Note: NGROK will provide a URL like `https://abc123.ngrok.io` - use this as your `--webhook_url` parameter



### Testing the Setup

Test the Midjourney webhook functionality:
```bash
cd /PATH_TO_GIT_REPOS/protoblog/utils
python test_midjourney_webhook_server.py --webhook_url "https://your-ngrok-url" --image_url "https://placehold.co/2048x2048/png"
```

### Running AI Agents

The system supports multiple AI agent types and configurations:

Running the AI Agent to Create a Blog Post
Current Agent Types:
1. blog_researcher_ai_agent
	1. Current Agent Names:
		1. topic_blog_poster
		2. engineer_blog_poster
2. blog_artist_ai_agent
	1. Current Agent Names:
		1. artist_blog_poster

Start NGROK to create a proxy tunnel for our Midjourney Image Process Flask Server API: http://localhost:9119
```
ngrok http 9119
```

Start Midjourney Webhook Flask Web Server & API (This server script also manages the downloading and the slicing of the images after it gets a callback from Midjourney)
```shell
cd blogi/utils/utils
python midjourney_webhook_server.py
```

Test Midjourney Webhook Python
```shell
python test_midjourney_webhook_server.py --webhook_url "https://7e99-47-204-135-48.ngrok-free.app" --image_url "https://placehold.co/2048x2048/png"
```

### Local Development

To preview the site locally:
```bash
hugo serve
```

### System Process Flow

When run, the system will:
1. Research the topic using Brave Search (Researcher Agent)
2. Generate content using Claude AI
3. Generate AI art using OpenAI and Midjourney (Artist Agent)
4. Save the post and images to Obsidian
5. Build the website with Hugo
6. Deploy to GitHub pages

## Components

### Blog Researcher AI Agent

The `blog_researcher_ai_agent.py` script:
- Performs web research using Brave Search API
- Extracts and summarizes webpage content
- Generates blog posts using Claude AI
- Saves content in Markdown format
- Key classes:
  - `BraveSearchClient`: Handles web searches
  - `ClaudeAgent`: Manages AI interactions and content generation

### Blog Artist AI Agent

The `blog_artist_ai_agent.py` script:
- Generates creative image prompts using OpenAI
- Creates images using Midjourney API
- Handles webhook callbacks for image generation status
- Key components:
  - `OpenAIRandomImagePromptService`: Generates image prompts
  - `MidJourneyImageService`: Manages image creation
  - `ProcessImageService`: Coordinates the image generation process

### Midjourney Webhook Server

The `midjourney_webhook_server.py` script:
- Handles callbacks from Midjourney API
- Processes and saves generated images
- Splits quad images into individual frames
- Manages image storage in both web and Obsidian directories

### Image Sync Helper

The `obsidian_image_sync.py` script:
- Processes Markdown files to convert Obsidian image links to Hugo-compatible formats
- Automatically copies referenced images from Obsidian to Hugo's static directory
- Handles space characters in image filenames
- Validates directory structures and file existence
- Provides detailed error reporting

### Megascript

The `megascript.sh` script orchestrates:
- Blog post generation
- AI image generation
- File synchronization between Obsidian and Hugo using obsidian_image_sync.py
- Image processing and conversion
- Website building with Hugo
- Git-based deployment
- System notifications and error handling

## Deployment

The system supports dual-branch deployment:
- `main`: Contains the entire project
- `hostinger`: Contains the built website (public directory)

## Configuration

1. Configure Hugo settings in `hugo.toml`

2. Prepare prompt templates in the `prompts` directory:
   - Create agent-specific prompts in a subdirectory
   - Use common prompts for shared functionality

## Error Handling

The system includes:
- Comprehensive logging
- Desktop notifications
- Error status reporting
- Automatic cleanup of temporary branches
- Webhook error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Attribution-NonCommercial-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt)

## Acknowledgments
- [NetworkChuck - Blog Post](https://blog.networkchuck.com/posts/my-insane-blog-pipeline/)
- [Anthropic's Claude AI](https://www.anthropic.com/claude)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI GPT-4](https://openai.com/gpt-4)
- [Midjourney](https://www.midjourney.com/)
- [UserAPI.AI API for Midjourney - (Cost effective and working)](https://userapi.ai/)
- [Brave Search API Documentation](https://api.search.brave.com/app/documentation)
- [Hugo Documentation](https://gohugo.io/documentation/)
- [Hugo Theme TeXify3](https://github.com/michaelneuper/hugo-texify3)

# AI Blog Generation System

An automated blog post generation system that uses AI agents to create both research-based and art-based content, with Hugo static site generation integration.

## Installation

### 1. Clone the Repository
```bash
git clone git@github.com:protomota/autoblog.git
cd autoblog
```

### 2. Set Up Python Environment
It's recommended to use a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```
You should now be in your virtual python environment. Your Terminal command prompt should now be prefixed with the environment name: (venv)
If you need to exit, you can just type `exit`

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the project root:
```bash
PROTOBLOG_PROJECT_ROOT=/path/to/your/project
```

## System Architecture

### 1. Admin Panel (`admin_panel/`)
A web interface for managing blog post generation:

```python
admin_panel/
├── main.py          # Flask server implementation
├── static/
│   ├── css/         # Styling
│   └── js/
│       └── main.js  # Frontend logic
└── templates/
    └── index.html   # Web interface
```

### 2. AI Agents (`ai_agents/`)
Core AI functionality for content generation:

```python
ai_agents/
├── main.py          # Main agent execution logic
├── core/
│   ├── agent.py     # BlogAgent implementation
│   └── config.py    # System configuration
└── utils/
    └── midjourney_webhook_server.py  # Image generation handler
```

### 3. Hugo Blog (`hugo.toml`)
Static site configuration for the generated blog:
- Theme: hugo-texify3
- Integrated commenting system (giscus)
- Buy Me a Coffee integration
- Custom CSS/JS support

## Features

### Research Content Generation
- Topic-based blog post generation
- Support for general topics and Python engineering content
- Automated research and content structuring

### Art Content Generation
- Integration with Midjourney for image generation
- Random prompt generation capability
- Webhook-based image processing

### Deployment
- Automated Git operations
- Hugo static site generation
- Integrated deployment pipeline

## Setup & Configuration

### Environment Variables
```bash
PROTOBLOG_PROJECT_ROOT=/path/to/your/project
```

### Dependencies
```bash
pip install flask python-dotenv asyncio
```

### Server Requirements
- NGROK for webhook handling
- Midjourney webhook server
- Flask development server

## Usage

### Starting the System
1. Start the admin panel:
```bash
python admin_panel/main.py
```

2. Access the web interface at `http://localhost:9229`

### Generating Content

#### Research Posts
1. Select "Blog Researcher AI Agent"
2. Choose agent type (Topic Researcher/Engineer)
3. Enter research topic
4. Click "Generate Post"

#### Art Posts
1. Select "Blog Artist AI Agent"
2. Choose agent type (Prompt/Random Artist)
3. Configure webhook URL
4. Provide image prompt (if not random)
5. Click "Generate Post"

## Technical Details

### Admin Panel (`main.js`)
- Dynamic form handling based on agent type
- Real-time field validation
- Asynchronous post generation
- Error handling and user feedback

### AI Agent System (`main.py`)
```python
async def main():
    # Command line argument handling
    # Path verification
    # Agent initialization
    # Content generation
    # Deployment
```

### Hugo Configuration
- Responsive theme
- SEO optimization
- Social sharing
- Analytics integration
- Comment system

## Error Handling
- Server startup validation
- Input validation
- Process monitoring
- Deployment verification
- User feedback system

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
[Your License Here]

## Support
For professional AI consulting services, visit [protomota.com](https://protomota.com)
