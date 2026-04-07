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
                "content": "You are Omega, a highly intelligent AI assistant. You are helpful, witty, thoughtful, and engaging. You provide detailed, insightful responses to any query. Keep responses conversational but informative."
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

@app.route('/api/clear', methods=['POST'])
def api_clear():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
