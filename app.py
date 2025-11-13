from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from finance_ai_chatbot import FinanceAIChatbot
from datetime import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AI_API_KEY")

app = Flask(__name__)
CORS(app)

# Simple user storage (in production, use a proper database)
USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

# Initialize storage files
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(CHATS_FILE):
    with open(CHATS_FILE, 'w') as f:
        json.dump({}, f)

try:
    bot = FinanceAIChatbot(api_key, "final_combined.csv")
    print(f"Chatbot initialized successfully using model: {bot.model_name}")
except Exception as e:
    print(f"Error initializing chatbot: {e}")
    bot = None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'})
        
        # Load users
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
        
        # Check if user exists
        if username in users:
            if users[username] == password:
                return jsonify({'success': True, 'message': 'Login successful'})
            else:
                return jsonify({'success': False, 'message': 'Invalid password'})
        else:
            # Create new user
            users[username] = password
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f)
            return jsonify({'success': True, 'message': 'Account created and logged in'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        if not bot:
            return jsonify({
                'response': '❌ Chatbot not initialized properly. Check your Gemini API key.',
                'error': True
            }), 500

        data = request.get_json()
        message = data.get('message', '').strip()
        username = data.get('username')
        chat_id = data.get('chat_id')

        if not message:
            return jsonify({
                'response': 'Please enter a message.',
                'error': False
            })

        response = bot.get_response(message)
        bot.total_queries += 1

        # Save chat history if user is logged in
        if username:
            with open(CHATS_FILE, 'r') as f:
                all_chats = json.load(f)
            
            if username not in all_chats:
                all_chats[username] = {}
            
            # Create new chat or append to existing
            if not chat_id:
                chat_id = f"chat_{datetime.now().timestamp()}"
                all_chats[username][chat_id] = {
                    'id': chat_id,
                    'title': message[:50] + ('...' if len(message) > 50 else ''),
                    'timestamp': datetime.now().isoformat(),
                    'messages': []
                }
            
            # Add messages
            all_chats[username][chat_id]['messages'].append({
                'text': message,
                'isUser': True,
                'timestamp': datetime.now().isoformat()
            })
            all_chats[username][chat_id]['messages'].append({
                'text': response,
                'isUser': False,
                'timestamp': datetime.now().isoformat()
            })
            
            with open(CHATS_FILE, 'w') as f:
                json.dump(all_chats, f)

        return jsonify({
            'response': response,
            'error': False,
            'chat_id': chat_id if username else None
        })

    except Exception as e:
        return jsonify({
            'response': f'Error: {str(e)}',
            'error': True
        }), 500

@app.route('/chat_history', methods=['GET'])
def chat_history():
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({'chats': []})
        
        with open(CHATS_FILE, 'r') as f:
            all_chats = json.load(f)
        
        user_chats = all_chats.get(username, {})
        chats_list = list(user_chats.values())
        # Sort by timestamp, newest first
        chats_list.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'chats': chats_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_chat', methods=['GET'])
def load_chat():
    try:
        username = request.args.get('username')
        chat_id = request.args.get('chat_id')
        
        if not username or not chat_id:
            return jsonify({'error': 'Missing parameters'}), 400
        
        with open(CHATS_FILE, 'r') as f:
            all_chats = json.load(f)
        
        chat = all_chats.get(username, {}).get(chat_id)
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        return jsonify({'messages': chat['messages']})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    try:
        if not bot:
            return jsonify({'error': 'Chatbot not initialized'}), 500

        duration = (datetime.now() - bot.session_start).seconds // 60
        return jsonify({
            'total_queries': bot.total_queries,
            'cache_entries': len(bot.response_cache),
            'session_minutes': duration
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'chatbot_ready': bot is not None
    })

@app.route('/categorize', methods=['POST'])
def categorize():
    try:
        data = request.get_json()
        description = data.get('description', '')
        amount = data.get('amount', '')
        if not description:
            return jsonify({'category': 'Uncategorized'})
        prompt = f"Classify this transaction: '{description}' for ₹{amount}. " \
                 f"Categories: ['Food', 'Transport', 'Utilities', 'Shopping', 'Investment', 'Salary', 'Other'].\n" \
                 f"Return only one best category."
        response = bot.model.generate_content(prompt)
        return jsonify({'category': response.text.strip()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Gemini Finance Chatbot Server")
    print("Server: http://localhost:5000")
    print("Frontend: http://localhost:5000/")
    print("API Endpoint: http://localhost:5000/chat")

    app.run(debug=True, port=5000, host='0.0.0.0')