import os
import logging
import torch
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
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

tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-cased-distilled-squad')
model = DistilBertForQuestionAnswering.from_pretrained('distilbert-base-cased-distilled-squad')

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

def generate_response(user_input, context):
    try:
        inputs = tokenizer(user_input, context, return_tensors = "pt", max_length=512, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
        answer_start = torch.argmax(outputs.start_logits)
        answer_end = torch.argmax(outputs.end_logits) + 1
        answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end]))

        return answer

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return "I encountered an error while generating a response."

def chatbot(user_input, disease_vector_store):
    hospital_suggestions = format_nearest_hospital()
    try:
        query_embedding = generate_embeddings(user_input)

        if is_diagnosis_request(query_embedding):
            return f"I'm not able to provide a diagnosis. Please consult with a healthcare professional: {hospital_suggestions}"

        if is_hospital_request(query_embedding):
            return f"The nearest hospitals based on your location are:\n{hospital_suggestions}"
        context = generate_context(user_input, disease_vector_store)
        if not context:
            return f"I don't have specific information about that in my database. For more information, please contact one of these healthcare providers:\n{hospital_suggestions}"
        response = generate_response(user_input, context)
        return f"Based on the information in my database: {response}"

    except Exception as e:
        logger.error(f"Error in chatbot function: {str(e)}", exc_info=True)
        return "I'm sorry, I encountered an error while processing your request. Could you please try again?"

def main():
    try:
        disease_vector_store = setup_chatbot()
        print("Chatbot is ready. You can start asking questions. Type 'exit' to quit.")

        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break
            response = chatbot(user_input, disease_vector_store)
            print("Chatbot:", response)
    except Exception as e:
        logger.error(f"Fatal error in main function: {str(e)}", exc_info=True)
        print("An unexpected error occurred. Please check the logs for more information.")

if __name__ == "__main__":
    main()
