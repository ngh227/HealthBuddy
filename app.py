from flask import Flask, jsonify, render_template, request, session
import google.generativeai as genai
from dotenv import load_dotenv
import os
import uuid
from src.chat import create_chat_history_table, store_chat_message, get_chat_history
from src.chat import setup_chatbot, chatbot

# Load environment variables
load_dotenv()

# Configure the generative AI model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
app.secret_key = os.urandom(24) 

create_chat_history_table()
disease_vector_store = setup_chatbot()

@app.route('/')
def index():
    try:
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        chat_history_entries = get_chat_history(session['session_id'])
        formatted_history = [
            {"user": entry[0], "bot": entry[1]} for entry in chat_history_entries
        ]
        return render_template('chatbot.html', chat_history=formatted_history)
    except Exception as e:
        app.logger.error(f"Error fetching chat history: {str(e)}")
        return render_template('chatbot.html', chat_history=[])

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        user_input = request.json.get('user_input')
        if not user_input:
            return jsonify({"error": "No user input provided."}), 400

        chat_history_entries = get_chat_history(session['session_id'])
        chat_history = [(entry[0], entry[1]) for entry in chat_history_entries]

        response, updated_chat_history = chatbot(user_input, disease_vector_store, chat_history)

        store_chat_message(session['session_id'], user_input, response)
        formatted_response = response.replace('\n', '<br>')
        
        return jsonify({"response": formatted_response})
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

if __name__ == '__main__':
    app.run(debug=True)
    