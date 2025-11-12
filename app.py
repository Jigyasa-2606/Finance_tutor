from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from finance_ai_chatbot import FinanceAIChatbot
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AI_API_KEY")

app = Flask(__name__)
CORS(app)

try:
    bot = FinanceAIChatbot(api_key, "final_combined.csv")
    print(f"Chatbot initialized successfully using model: {bot.model_name}")
except Exception as e:
    print(f"Error initializing chatbot: {e}")
    bot = None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

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

        if not message:
            return jsonify({
                'response': 'Please enter a message.',
                'error': False
            })

        response = bot.get_response(message)
        bot.total_queries += 1

        return jsonify({
            'response': response,
            'error': False
        })

    except Exception as e:
        return jsonify({
            'response': f'Error: {str(e)}',
            'error': True
        }), 500

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


if __name__ == '__main__':
    print("Starting Gemini Finance Chatbot Server")
    print("Server: http://localhost:5000")
    print("Frontend: http://localhost:5000/")
    print("API Endpoint: http://localhost:5000/chat")

    app.run(debug=True, port=5000, host='0.0.0.0')
