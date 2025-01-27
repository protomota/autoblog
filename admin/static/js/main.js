// Agent names data will be provided by Flask
const agentNames = window.agentNamesData;

// Add display name mappings
const displayNames = {
    'blog_researcher_ai_agent': 'Blog Researcher AI Agent',
    'blog_artist_ai_agent': 'Blog Artist AI Agent',
    'topic_researcher': 'Topic Researcher (Provide any Topic)',
    'topic_engineer': 'Topic Engineer (Provide a Python Engineering Topic)',
    'prompt_artist': 'Prompt Artist (Provide a Image Prompt)',
    'random_prompt_artist': 'Random Prompt Artist (Let the AI Dream an Image Prompt)'
};

function runMidjourneyServer() {
    fetch('/run-midjourney', {
        method: 'POST',
    })
    .then(response => response.text())
    .then(data => {
        console.log('Midjourney Webhook Server started:', data);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error);  // Add this line to show any errors
    });
}

function runNGROKServer() {
    fetch('/run-ngrok', {
        method: 'POST',
    })
    .then(response => response.text())
    .then(data => {
        console.log('NGROK Server started:', data);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error);  // Add this line to show any errors
    });
}

// Function to update agent names based on agent type
function updateAgentNames() {
    const agentType = document.getElementById('agent_type').value;
    const agentNameSelect = document.getElementById('agent_name');

    // Clear existing options
    agentNameSelect.innerHTML = '';

    if (agentType === 'blog_artist_ai_agent') {
        // Sort the options to put random_prompt_artist first
        const sortedNames = agentNames[agentType].sort((a, b) => {
            if (a === 'random_prompt_artist') return -1;
            if (b === 'random_prompt_artist') return 1;
            return 0;
        });
        
        // Add options in the sorted order
        sortedNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = displayNames[name] || name;
            
            // Set default selection for artist agent
            if (name === 'random_prompt_artist') {
                option.selected = true;
            }
            
            agentNameSelect.appendChild(option);
        });
    } else {
        // Sort the options to put topic_researcher first
        const sortedNames = agentNames[agentType].sort((a, b) => {
            if (a === 'topic_researcher') return -1;
            if (b === 'topic_researcher') return 1;
            return 0;
        });
        
        // Add options in the sorted order
        sortedNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = displayNames[name] || name;
            
            // Set default selection for researcher agent
            if (name === 'topic_researcher') {
                option.selected = true;
            }
            
            agentNameSelect.appendChild(option);
        });
    }

    // Call updateFieldVisibility to refresh fields based on new agent name
    updateFieldVisibility();
}

// Function to update field visibility based on agent type and name
function updateFieldVisibility() {
    const agentType = document.getElementById('agent_type').value;
    const agentName = document.getElementById('agent_name').value;
    const topicField = document.getElementById('topic_field');
    const imageField = document.getElementById('image_field');
    const webhookUrlField = document.getElementById('webhook_url_field');

    // Clear values when agent name changes
    document.getElementById('image_prompt').value = '';
    document.getElementById('webhook_url').value = '';
    document.getElementById('topic').value = '';

    if (agentType === 'blog_researcher_ai_agent') {
        topicField.classList.remove('hidden');
        imageField.classList.add('hidden');
        webhookUrlField.classList.add('hidden');
        document.getElementById('topic').required = true;
        document.getElementById('image_prompt').required = false;
        document.getElementById('webhook_url').required = false;
    } else if (agentType === 'blog_artist_ai_agent') {
        webhookUrlField.classList.remove('hidden');
        document.getElementById('webhook_url').required = true;
        
        if (agentName === 'random_prompt_artist') {
            topicField.classList.add('hidden');
            imageField.classList.add('hidden');
            document.getElementById('topic').required = false;
            document.getElementById('image_prompt').required = false;
        } else {
            topicField.classList.add('hidden');
            imageField.classList.remove('hidden');
            document.getElementById('topic').required = false;
            document.getElementById('image_prompt').required = true;
        }
    }
}

// Function to start a server process
async function startServer(command) {
    try {
        const response = await fetch('/start_server', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command })
        });
        const data = await response.json();
        if (!data.success) {
            console.error('Failed to start server:', data.message);
        }
    } catch (error) {
        console.error('Error starting server:', error);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners
    document.getElementById('agent_type').addEventListener('change', updateAgentNames);
    document.getElementById('agent_name').addEventListener('change', updateFieldVisibility);

    // Add server button listeners
    document.getElementById('ngrokButton').addEventListener('click', () => {
        startServer('ngrok http 9119');
    });

    document.getElementById('midjourneyButton').addEventListener('click', () => {
        startServer('.start_midjourney_webhook');
    });

    // Initialize fields
    updateAgentNames();
    updateFieldVisibility();

    // Form submission handler
    document.getElementById('generateForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get UI elements
        const generateButton = document.getElementById('generateButton');
        const buttonText = document.getElementById('buttonText');
        const buttonSpinner = document.getElementById('buttonSpinner');
        
        // Disable button and show loading state
        generateButton.disabled = true;
        buttonText.textContent = 'Generating Post...';
        buttonSpinner.classList.remove('hidden');
        
        // Clear the blog URL container when starting new generation
        const urlContainer = document.getElementById('blog-url-container');
        urlContainer.classList.add('hidden');
        document.getElementById('blog-url').href = '';
        document.getElementById('blog-url').textContent = '';
        
        const formData = {
            agent_type: document.getElementById('agent_type').value,
            agent_name: document.getElementById('agent_name').value
        };
        
        const agent_type = formData.agent_type;
        const agent_name = formData.agent_name;
        const topic = document.getElementById('topic').value;
        const image_prompt = document.getElementById('image_prompt').value;
        const webhook_url = document.getElementById('webhook_url').value;

        // Clear previous output
        document.getElementById('console-log').innerHTML = '<pre>Executing command...</pre>';

        try {
            // Log the request data for debugging
            console.log('Sending request with data:', {
                agent_type,
                agent_name,
                topic: topic.trim(),
                image_prompt: image_prompt.trim(),
                webhook_url: webhook_url.trim()
            });

            // Construct the request body based on agent type
            const requestBody = {
                agent_type: agent_type,
                agent_name: agent_name
            };

            // Add topic or image_prompt based on agent type
            if (agent_type === 'blog_researcher_ai_agent') {
                if (!topic.trim()) {
                    throw new Error('Topic is required for researcher agent');
                }
                requestBody.topic = topic.trim();
            } else if (agent_type === 'blog_artist_ai_agent') {
                if (!webhook_url.trim()) {
                    throw new Error('Webhook URL is required for artist agent');
                }
                requestBody.webhook_url = webhook_url.trim();
                
                if (agent_name !== 'random_prompt_artist' && !image_prompt.trim()) {
                    throw new Error('Image prompt is required for artist agent');
                }
                if (image_prompt.trim()) {
                    requestBody.image_prompt = image_prompt.trim();
                }
            }

            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            
            if (data.success) {
                const consoleLog = document.getElementById('console-log');
                consoleLog.innerHTML = `<pre class="success">${data.message}</pre>`;
                
                // Handle blog URL
                if (data.blog_url) {
                    const urlLink = document.getElementById('blog-url');
                    urlLink.href = data.blog_url;
                    urlLink.textContent = data.blog_url;
                    urlContainer.classList.remove('hidden');
                }
            } else {
                // Enhanced error logging with more details
                console.error('Server returned error:', data);
                const errorMessage = data.message || 'Unknown server error';
                const details = data.details || '';
                const fullError = `${errorMessage}${details ? '\n\nDetails:\n' + details : ''}`;
                throw new Error(fullError);
            }
        } catch (error) {
            console.error('Full error:', error);
            const consoleLog = document.getElementById('console-log');
            consoleLog.innerHTML = `<pre class="error">Error: ${error.message}</pre>`;
            
            // Add alert for critical errors
            if (error.message.includes('Deployment failed')) {
                alert('Deployment failed. Please check the console log for more details and ensure all required servers are running.');
            }
        } finally {
            // Reset button state
            generateButton.disabled = false;
            buttonText.textContent = 'Generate Post';
            buttonSpinner.classList.add('hidden');
        }
    });
});