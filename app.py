import os
import json
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Store conversation history
conversation_history = []

def chat_with_omega(user_message):
    """Send a message to Omega and get a response"""
    
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY not set in .env file"
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Prepare the request
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://omega-ai.local",
        "X-OpenRouter-Title": "Omega AI"
    }
    
    payload = {
        "model": "openai/gpt-4o",  # High-quality GPT-4o model
        "messages": [
            {
                "role": "system",
                "content": """You are Omega - Optimal Multitasking Enhanced Guidance Assistant, created by pkd sathaan (mufaad).

You are an exceptionally intelligent, articulate, and engaging AI assistant. Your communication is always clear, eloquent, and grammatically impeccable. You handle complex queries with remarkable ease and provide thoughtful, comprehensive responses.

Your core strengths:
• Delivering insightful, well-articulated answers across all domains
• Providing comprehensive analysis and detailed explanations
• Engaging in meaningful, contextual conversations
• Expert assistance with coding, writing, research, and creative projects
• Thoughtful problem-solving and strategic guidance
• Perfect memory of conversation context
• Analyzing and discussing images thoughtfully when provided

Communication Style: You speak with eloquence and sophistication. Your responses are natural, conversational, yet intellectually rigorous. You adapt seamlessly to different communication needs while maintaining impeccable grammar and clarity. You are genuinely interested in understanding what matters to users and respond with authentic care.

When analyzing images: Describe what you observe, answer questions about the image thoughtfully, and provide relevant insights based on the visual content.

Always deliver the highest quality of thought and expression. Be genuine, helpful, and precise in every interaction."""
            }
        ] + conversation_history,
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the assistant's response
        if "choices" in result and len(result["choices"]) > 0:
            assistant_message = result["choices"][0]["message"]["content"]
            
            # Add assistant message to history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        else:
            return "Error: Unexpected response format from OpenRouter"
            
    except requests.exceptions.RequestException as e:
        return f"Error communicating with OpenRouter: {str(e)}"
    except json.JSONDecodeError:
        return "Error: Invalid response from OpenRouter API"

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat messages"""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    response = chat_with_omega(user_message)
    return jsonify({'response': response})

@app.route('/api/history', methods=['GET'])
def api_history():
    """Get conversation history"""
    return jsonify({'history': conversation_history})

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze an uploaded image"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    user_question = request.form.get('question', 'What do you see in this image?')
    
    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Read image data
    import base64
    image_data = image_file.read()
    image_base64 = base64.standard_b64encode(image_data).decode('utf-8')
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_question
    })
    
    # Prepare request with vision
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://omega-ai.local",
        "X-OpenRouter-Title": "Omega AI"
    }
    
    payload = {
        "model": "openai/gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": "You are Omega, an exceptionally intelligent AI assistant. When analyzing images, provide detailed, insightful observations and answer questions thoughtfully based on what you see."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": user_question
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            assistant_message = result["choices"][0]["message"]["content"]
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            return jsonify({'response': assistant_message})
        else:
            return jsonify({'error': 'Unexpected response from OpenRouter'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Error analyzing image: {str(e)}'}), 500

@app.route('/api/clear', methods=['POST'])
def api_clear():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
