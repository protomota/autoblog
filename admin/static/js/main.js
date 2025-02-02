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

// Add agent type mappings
const agentTypeMapping = {
    'topic_researcher': 'blog_researcher_ai_agent',
    'topic_engineer': 'blog_researcher_ai_agent',
    'prompt_artist': 'blog_artist_ai_agent',
    'random_prompt_artist': 'blog_artist_ai_agent'
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
    const currentValue = agentNameSelect.value; // Store current value before clearing

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
            
            // Restore previous selection if it exists, otherwise use default
            if (name === currentValue || (!currentValue && name === 'random_prompt_artist')) {
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
            
            // Restore previous selection if it exists, otherwise use default
            if (name === currentValue || (!currentValue && name === 'topic_researcher')) {
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
    const serverSection = document.getElementById('server_section');
    const chaosSliderField = document.getElementById('chaos_slider_field');

    // Just update visibility and requirements, don't clear any values
    if (agentType === 'blog_researcher_ai_agent') {
        topicField.classList.remove('hidden');
        imageField.classList.add('hidden');
        webhookUrlField.classList.add('hidden');
        serverSection.classList.add('hidden');
        chaosSliderField.classList.add('hidden');
        document.getElementById('topic').required = true;
        document.getElementById('image_prompt').required = false;
        document.getElementById('webhook_url').required = false;
    } else if (agentType === 'blog_artist_ai_agent') {
        webhookUrlField.classList.remove('hidden');
        serverSection.classList.remove('hidden');
        chaosSliderField.classList.remove('hidden');
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

// Add a function to append log messages
function appendToConsole(consoleLog, message, className = '') {
    const timestamp = new Date().toLocaleTimeString();
    consoleLog.innerHTML += `<pre class="${className}">[${timestamp}] ${message}</pre>`;
    // Auto-scroll to bottom
    consoleLog.scrollTop = consoleLog.scrollHeight;
}

// Function to save form values to localStorage
function saveFormValues() {
    const formData = {
        agent_type: document.getElementById('agent_type').value,
        agent_name: document.getElementById('agent_name').value,
        topic: document.getElementById('topic').value,
        image_prompt: document.getElementById('image_prompt').value,
        webhook_url: document.getElementById('webhook_url').value,
        chaos_percentage: document.getElementById('chaos_percentage').value,
        filename: document.getElementById('filename').textContent
    };
    console.log('Saving form data:', formData);
    localStorage.setItem('generateFormData', JSON.stringify(formData));
}

// Function to load form values from localStorage
function loadFormValues() {
    const savedData = localStorage.getItem('generateFormData');
    console.log('Loading saved data:', savedData);
    
    if (savedData) {
        const formData = JSON.parse(savedData);
        
        // Set agent type first
        const agentTypeSelect = document.getElementById('agent_type');
        if (formData.agent_type) {
            agentTypeSelect.value = formData.agent_type;
            // Trigger change event to update agent names dropdown
            agentTypeSelect.dispatchEvent(new Event('change'));
        }
        
        // Set agent name after small delay to ensure dropdown is populated
        setTimeout(() => {
            const agentNameSelect = document.getElementById('agent_name');
            if (formData.agent_name) {
                agentNameSelect.value = formData.agent_name;
                // Trigger change event to update field visibility
                agentNameSelect.dispatchEvent(new Event('change'));
            }
            
            // Set other form values
            if (formData.topic) document.getElementById('topic').value = formData.topic;
            if (formData.image_prompt) document.getElementById('image_prompt').value = formData.image_prompt;
            if (formData.webhook_url) document.getElementById('webhook_url').value = formData.webhook_url;
            if (formData.chaos_percentage) {
                const chaosSlider = document.getElementById('chaos_percentage');
                chaosSlider.value = formData.chaos_percentage;
                document.getElementById('chaos_value').textContent = formData.chaos_percentage;
            }

            // Restore filename and show container if filename exists
            if (formData.filename) {
                const filenameElement = document.getElementById('filename');
                const filenameContainer = document.getElementById('filename-container');
                const deployButton = document.getElementById('deployButton');
                
                filenameElement.textContent = formData.filename;
                filenameContainer.classList.remove('hidden');
                deployButton.classList.remove('hidden');
            }
        }, 100);
    }
}

// Add event listeners to save form values on change
function setupFormPersistence() {
    const formElements = [
        'agent_type',
        'agent_name',
        'topic',
        'image_prompt',
        'webhook_url',
        'chaos_percentage'
    ];
    
    formElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            // Save on any input change
            element.addEventListener('input', saveFormValues);
            element.addEventListener('change', saveFormValues);
            // For text inputs and textareas, also save on keyup and blur
            if (element.type === 'text' || element.type === 'url' || element.tagName.toLowerCase() === 'textarea') {
                element.addEventListener('keyup', saveFormValues);
                element.addEventListener('blur', saveFormValues);
            }
        }
    });
}

// Add deployment function
async function deployPosts() {
    const deployButton = document.getElementById('deployButton');
    const deployButtonText = document.getElementById('deployButtonText');
    const deployButtonSpinner = document.getElementById('deployButtonSpinner');
    const consoleLog = document.getElementById('console-log');

    // Disable button and show loading state
    deployButton.disabled = true;
    deployButtonText.textContent = 'Deploying...';
    deployButtonSpinner.classList.remove('hidden');

    try {
        appendToConsole(consoleLog, 'Starting blog deployment...');
        
        const response = await fetch('/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
            appendToConsole(consoleLog, data.message, 'success');
        } else {
            throw new Error(data.message || 'Deployment failed');
        }
    } catch (error) {
        console.error('Error during deployment:', error);
        appendToConsole(consoleLog, `Error: ${error.message}`, 'error');
    } finally {
        // Reset button state
        deployButton.disabled = false;
        deployButtonText.textContent = 'Deploy Posts to Blog';
        deployButtonSpinner.classList.add('hidden');
    }
}

// Voice over button handler
async function generateVoiceOver() {
    const voiceOverButton = document.getElementById('voiceOverButton');
    const voiceOverButtonText = document.getElementById('voiceOverButtonText');
    const voiceOverButtonSpinner = document.getElementById('voiceOverButtonSpinner');
    const consoleLog = document.getElementById('console-log');
    const filename = document.getElementById('filename').textContent;

    // Disable button and show loading state
    voiceOverButton.disabled = true;
    voiceOverButtonText.textContent = 'Generating Voice Over...';
    voiceOverButtonSpinner.classList.remove('hidden');

    try {
        appendToConsole(consoleLog, 'Starting voice over generation...');
        
        const response = await fetch('/generate-voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename })
        });

        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success) {
            appendToConsole(consoleLog, data.message, 'success');
        } else {
            throw new Error(data.message || 'Voice over generation failed');
        }
    } catch (error) {
        console.error('Error during voice over generation:', error);
        appendToConsole(consoleLog, `Error: ${error.message}`, 'error');
    } finally {
        // Reset button state
        voiceOverButton.disabled = false;
        voiceOverButtonText.textContent = 'Generate Voice Over';
        voiceOverButtonSpinner.classList.add('hidden');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners
    document.getElementById('agent_type').addEventListener('change', () => {
        updateAgentNames();
        saveFormValues(); // Save after updating agent names
    });
    
    document.getElementById('agent_name').addEventListener('change', () => {
        updateFieldVisibility();
        saveFormValues(); // Save after updating visibility
    });

    // Add server button listeners
    document.getElementById('ngrokButton').addEventListener('click', () => {
        startServer('ngrok http 9119');
    });

    document.getElementById('midjourneyButton').addEventListener('click', () => {
        startServer('.start_midjourney_webhook');
    });

    // Add chaos slider listener
    const chaosSlider = document.getElementById('chaos_percentage');
    const chaosValue = document.getElementById('chaos_value');
    
    chaosSlider.addEventListener('input', function() {
        chaosValue.textContent = this.value;
        saveFormValues(); // Save when slider changes
    });

    // Add deployment button listener
    document.getElementById('deployButton').addEventListener('click', deployPosts);

    // Add voice over button listener
    document.getElementById('voiceOverButton').addEventListener('click', generateVoiceOver);

    // Initialize fields
    updateAgentNames();
    updateFieldVisibility();

    // Add form persistence
    setupFormPersistence();
    loadFormValues();

    // Form submission handler
    document.getElementById('generateForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        saveFormValues();
        
        // Get UI elements
        const generateButton = document.getElementById('generateButton');
        const buttonText = document.getElementById('buttonText');
        const buttonSpinner = document.getElementById('buttonSpinner');
        const consoleLog = document.getElementById('console-log');
        const deployButton = document.getElementById('deployButton');
        
        // Disable button and show spinner
        generateButton.disabled = true;
        buttonText.textContent = 'Generating...';
        buttonSpinner.classList.remove('hidden');
        
        // Hide deploy button when starting generation
        deployButton.classList.add('hidden');
        
        // Clear the blog URL container when starting new generation
        const urlContainer = document.getElementById('filename-container');
        urlContainer.classList.add('hidden');
        document.getElementById('filename').textContent = '';
        
        // Initialize console
        consoleLog.innerHTML = '';
        appendToConsole(consoleLog, 'Starting post generation...');

        const agent_name = document.getElementById('agent_name').value;
        // Map the agent type to the correct backend value
        const agent_type = agentTypeMapping[agent_name] || agent_name;
        const topic = document.getElementById('topic').value;
        const image_prompt = document.getElementById('image_prompt').value;
        const webhook_url = document.getElementById('webhook_url').value;
        const chaos_percentage = document.getElementById('chaos_percentage').value;

        try {
            appendToConsole(consoleLog, `Agent Type: ${agent_type}`);
            appendToConsole(consoleLog, `Agent Name: ${agent_name}`);
            
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
                
                // Only add image_prompt if not random_prompt_artist
                if (agent_name === 'random_prompt_artist') {
                    // Don't include image_prompt for random_prompt_artist
                    appendToConsole(consoleLog, 'Using random prompt generation...');
                } else {
                    // For prompt_artist, require and include the image prompt
                    if (!image_prompt.trim()) {
                        throw new Error('Image prompt is required for artist agent');
                    }
                    requestBody.image_prompt = image_prompt.trim();
                }
                
                // Always include chaos_percentage for artist agents
                requestBody.chaos_percentage = document.getElementById('chaos_percentage').value;
            }

            appendToConsole(consoleLog, 'Sending request to server...');
            
            // Add timeout to the fetch request
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 600000); // 10 minute timeout

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody),
                    signal: controller.signal
                });

                clearTimeout(timeout);

                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }

                appendToConsole(consoleLog, 'Response received from server...');
                const data = await response.json();
                
                if (data.success) {
                    // Show success message with any additional information
                    let successMessage = data.message || 'Post generated successfully!';
                    if (data.details) {
                        successMessage += '\n\nDetails:\n' + data.details;
                    }
                    appendToConsole(consoleLog, successMessage, 'success');
                    
                    // Handle filename display and deploy button
                    if (data.filename) {
                        const filenameElement = document.getElementById('filename');
                        filenameElement.textContent = data.filename;
                        document.getElementById('filename-container').classList.remove('hidden');
                        appendToConsole(consoleLog, `Blog Post generated successfully: ${data.filename}`);
                        // Show both buttons when filename is displayed
                        document.getElementById('voiceOverButton').classList.remove('hidden');
                        deployButton.classList.remove('hidden');
                    }
                } else {
                    throw new Error(data.message || 'Unknown server error');
                }
            } catch (fetchError) {
                if (fetchError.name === 'AbortError') {
                    throw new Error('Request timed out after 10 minutes. Please try again.');
                }
                throw fetchError;
            }
        } catch (error) {
            console.error('Error during post generation:', error);
            const errorMessage = error.message || 'An unexpected error occurred';
            appendToConsole(consoleLog, `Error: ${errorMessage}`, 'error');
            
            if (errorMessage.includes('Deployment failed')) {
                alert('Deployment failed. Please check the console log for more details and ensure all required servers are running.');
            }
        } finally {
            // Reset button state
            generateButton.disabled = false;
            buttonText.textContent = 'Generate Post';
            buttonSpinner.classList.add('hidden');
        }
    });

    // Add window unload listener to ensure values are saved before page refresh
    window.addEventListener('beforeunload', () => {
        saveFormValues();
    });
});