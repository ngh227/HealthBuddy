import os
import google.generativeai as genai
import logging
import torch
from typing import List, Tuple
from dotenv import load_dotenv
from data_preprocessing import (
    generate_embeddings, setup_disease_vector_store,
    create_health_topics_table, fetch_medlineplus_data,
    store_disease_in_tidb, load_disease_codes
)
from hospital_functions import get_user_location, find_nearest_hospital, is_hospital_request
from diagnosis import is_diagnosis_request

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DISEASE_CODES_FILE = "disease_codes.csv"
MAX_VECTOR_SEARCHES = 3
SIMILARITY_THRESHOLD = 0.8

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def populate_disease_data(disease_vector_store, disease_codes):
    for disease_name, code in disease_codes.items():
        data = fetch_medlineplus_data(code)
        if data:
            for item in data:
                store_disease_in_tidb(item, disease_vector_store)
            logger.info(f"Added data for {disease_name}")
        else:
            logger.warning(f"No data found for {disease_name}")

def perform_vector_search(vector_store, query_embedding, top_k=3):
    return vector_store.query(query_embedding, top_k=top_k)

def format_nearest_hospital():
    user_lat, user_long = get_user_location()
    hospitals = find_nearest_hospital(user_lat, user_long)
    formatted_string = ''
    for hospital in hospitals:
        formatted_string += f"{hospital['name']} at {hospital['address']}\n"
    return formatted_string

def setup_chatbot():
    try:
        logger.info("Setting up chatbot...")
        create_health_topics_table()
        disease_vector_store = setup_disease_vector_store()
        disease_codes = load_disease_codes(DISEASE_CODES_FILE)
        if not disease_codes:
            logger.warning("No disease codes loaded. Check the content of the disease codes file.")
        populate_disease_data(disease_vector_store, disease_codes)
        logger.info("Chatbot setup completed successfully.")
        return disease_vector_store
    except Exception as e:
        logger.error(f"Error setting up chatbot: {str(e)}", exc_info=True)
        raise
#### CHAT HISTORY #####
def format_chat_history(chat_history: List[Tuple[str, str]], max_history: int = 3) -> str:
    formatted_history = ""
    for i, (human, ai) in enumerate(chat_history[-max_history:], 1):
        formatted_history += f"Human {i}: {human}\nAI assistant {i}: {ai}\n\n"
    return formatted_history.strip()

def generate_context(user_input, disease_vector_store, top_k=3, max_context_length=500):
    query_embedding = generate_embeddings(user_input)
    search_results = perform_vector_search(disease_vector_store, query_embedding, top_k=top_k)

    if not search_results:
        return None
    
    sorted_results = sorted(search_results, key = lambda x: 1 - x.distance, reverse=True)

    context = ""
    current_length = 0

    for result in sorted_results:
        document = result.document
        similarity = 1 - result.distance

        if similarity < 0.7:
            continue
        
        if current_length + len(document) <= max_context_length:
            context += document + " "
            current_length += len(document) + 1
        else:
            remaining_length = max_context_length - current_length
            context += document[:remaining_length]
            break
    return context.strip()

def generate_prompt(user_input, context, chat_history):
    formatted_chat_history = format_chat_history(chat_history)
    prompt = f"""You are an AI assistant assistant specializing in health information. Follow these guidelines strictly:
1. Answer questions ONLY using the information provided in {context}. Do not use any external knowledge. If {context} is empty, say that you don't have that information in your database
2. If the information to answer the question is not in the context, say: "I don't have specific information about that in my database."
3. Always maintain a professional and empathetic tone.

Context: {context}

Current conversation: {formatted_chat_history}

Human: {user_input}
AI assistant:"""
    return prompt
    
def generate_response(user_input: str, context: str, chat_history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
    prompt = generate_prompt(user_input, context, chat_history)
    response = model.generate_content(prompt)
    response_text = response.text
    chat_history.append((user_input, response_text))

    if len(chat_history) > 3:
        chat_history = chat_history[-3:]
    return response_text, chat_history

def chatbot(user_input: str, disease_vector_store, chat_history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
    hospital_suggestions = format_nearest_hospital()
    try:
        query_embedding = generate_embeddings(user_input)

        if is_diagnosis_request(query_embedding):
            response = f"I'm not able to provide a diagnosis. Please consult with a healthcare professional: {hospital_suggestions}"
            chat_history.append((user_input, response))
            return response, chat_history

        if is_hospital_request(query_embedding):
            response = f"The nearest hospitals based on your location are:\n{hospital_suggestions}"
            chat_history.append((user_input, response))
            return response, chat_history
        
        context = generate_context(user_input, disease_vector_store)
        if not context:
            response = f"I don't have specific information about that in my database. For more information, please contact your nearest healthcare providers:\n{hospital_suggestions}"
            chat_history.append((user_input, response))
            return response, chat_history

        response, updated_chat_history = generate_response(user_input, context, chat_history)
        return f"{response}", updated_chat_history
    except Exception as e:
        logger.error(f"Error in chatbot function: {str(e)}", exc_info=True)
        return "I'm sorry, I encountered an error while processing your request. Could you please try again?"

def main():
    try:
        disease_vector_store = setup_chatbot()
        chat_history: List[Tuple[str, str]] = []
        print("Chatbot is ready. You can start asking questions. Type 'exit' to quit.")

        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break
            response, chat_history = chatbot(user_input, disease_vector_store, chat_history)
            print("Chatbot:", response)
    except Exception as e:
        logger.error(f"Fatal error in main function: {str(e)}", exc_info=True)
        print("An unexpected error occurred. Please check the logs for more information.")

if __name__ == "__main__":
    main()