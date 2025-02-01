# Blogi - AI-Powered Blog Post Generator

Blogi is an advanced blog post generation system that uses AI agents to create and manage blog content. It features both research-based and art-based content generation capabilities.

## 🚀 Features

- **AI-Powered Content Generation**
  - Research-based blog posts with automatic topic exploration
  - AI art generation with Midjourney integration
  - Automated deployment to static blog sites

- **Flexible Agent System**
  - Blog Researcher AI Agent
    - Topic Researcher (General Topics)
    - Topic Engineer (Python Engineering Topics)
  - Blog Artist AI Agent
    - Prompt Artist (Custom Image Prompts)
    - Random Prompt Artist (AI-Generated Prompts)

- **Modern Web Interface**
  - Real-time console logging
  - Automatic form value persistence
  - Progress indicators and status updates

## 🛠 Project Structure

*Additional directories such as `utils/` or `services/` may also exist to support various functionalities like image processing or API integrations.*

---

## Installation & Setup

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd blogi
   ```

2. **Create and Activate a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate     # On Unix or macOS
   .\venv\Scripts\activate      # On Windows
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**

   Create a `.env` file in the project root to store your configuration variables. For example:

   ```env
   # API Keys
   ANTHROPIC_API_KEY=your_anthropic_api_key
   USERAPI_AI_API_KEY=your_userapi_ai_api_key
   USERAPI_AI_ACCOUNT_HASH=your_account_hash

   # Blog configuration
   BLOG_URL=your_blog_url
   ```

   *Ensure you configure all necessary variables required by `blogi/core/config.py`.*

---

## Running the Application

The application is set up as a Flask app that is served via Hypercorn for async support.

1. **Start the Application**

   From the project root directory, run:

   ```bash
   python -m blogi.admin.main
   ```

   This starts the server (by default on address 0.0.0.0 port 9229). You can adjust the configuration in `blogi/admin/main.py` as needed.

2. **Access the Interface**

   Open your browser and navigate to:  
   `http://localhost:9229`

---

## Using the Interface

The web interface is accessible via the browser and is designed to be both responsive and interactive:

1. **Configure Your Post**
   - **Agent Type & Name:**  
     Select from the provided dropdown list. The agent type determines the required fields.
   - **Researcher Agent:**  
     - Enter a topic in the Topic field.
     - Click **"Generate Post"**.
   - **Artist Agent:**  
     - A webhook URL is required for processing images.
     - Optionally, provide an image prompt if you don't wish to use a randomly generated prompt.
     - Use the **NGROK** and **Midjourney Webhook Server** buttons (under the server section) to start the required servers.
     - Adjust the chaos percentage (optional) using the slider.
     - Click **"Generate Post"**.

2. **Console Log**  
   The page includes a console log area that displays real-time feedback and error messages during generation and deployment.

3. **Deploying Posts**  
   Once a blog post is generated (the filename becomes visible), you can click the **"Deploy Posts to Blog"** button to sync content, build the static site with Hugo, and push changes via git operations. The result will be visible in the console log area.

---

## Development Notes

- **Requirements File**  
  All required Python packages are listed in `requirements.txt`. Make sure to install them in your virtual environment.

- **Main Server (admin/main.py)**  
  The Flask application and async endpoints are defined here. This file handles:
  - Generating posts using the `BlogAgent` found in `core/agent.py`
  - Starting auxiliary servers (NGROK and Midjourney) using AppleScript commands
  - Deployment logic via `DeploymentManager` from `core/deployment.py`

- **Client-Side Interactions (admin/static/js/main.js)**  
  The main JavaScript file is responsible for:
  - Handling form submissions and AJAX calls to endpoints (`/generate`, `/deploy`, etc.)
  - Managing UI elements such as spinners, button text changes, and form persistence
  - Controlling field visibility based on the selected agent type

- **AI Agents (core/agent.py)**  
  This file contains all the logic for:
  - Validating agent configurations and required fields
  - Generating content, titles, and tags
  - Saving content to the filesystem (e.g., as Obsidian Notes) and preparing paths for deployment

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "Add some feature"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request.

Contributions to enhance functionality or improve documentation are very welcome!

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
