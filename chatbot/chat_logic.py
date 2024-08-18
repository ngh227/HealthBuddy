import os
import logging
from llama_index.llms.huggingface import HuggingFaceInferenceAPI

from data_preprocessing import (
    generate_embeddings, setup_disease_vector_store,
    create_health_topics_table, fetch_medlineplus_data,
    store_disease_in_tidb, load_disease_codes
)

from hospital_functions import (
    setup_hospital_vector_store, get_user_location,
    find_nearest_hospital, embed_hospital_info,
    store_hospital_in_tidb, create_hospitals_table,
    is_hospital_request
)

from diagnosis import (
    is_diagnosis_request
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DISEASE_CODES_FILE = "disease_codes.csv"

def populate_disease_data (disease_vector_store, disease_codes):
    for disease_name, code in disease_codes.items():
        data = fetch_medlineplus_data(code)
        if data:
            for item in data:
                store_disease_in_tidb(item, disease_vector_store)
            logger.info(f"Added data for {disease_name}")
        else:
            logger.warning(f"No data found for {disease_name}")

def populate_hospital_data(hospital_vector_store):
    user_lat, user_long = get_user_location()
    if user_lat and user_long:
        hospitals = find_nearest_hospital(user_lat, user_long)
        embedded_hospitals = embed_hospital_info(hospitals)
        for hospital in embedded_hospitals:
            store_hospital_in_tidb(hospital, hospital_vector_store)
        logger.info(f'Added data')
    else:
        logger.warning(f"Failed to get user's location")

def perform_vector_search(vector_store, query_embedding, top_k = 3):
    return vector_store.query(query_embedding, top_k=top_k)

def setup_chatbot():
# setup database tables
    create_health_topics_table()
    create_hospitals_table()
# setup vector stores
    disease_vector_store = setup_disease_vector_store()
    hospital_vector_store = setup_hospital_vector_store()
# load disease codes
    disease_codes = load_disease_codes(DISEASE_CODES_FILE) 
    populate_disease_data(disease_vector_store, disease_codes)
    populate_hospital_data(hospital_vector_store)
# setup hugging face model:
    llm = HuggingFaceInferenceAPI(
        model_name = "mistralai/Mixtral-8x7B-Instruct-v0.1",
        token = os.getenv("HUGGINGFACEHUB_API_KEY")
)
    return disease_vector_store, hospital_vector_store, llm

def get_nearest_hospitals():
    user_lat, user_long = get_user_location()
    if user_lat and user_long:
        return find_nearest_hospital(user_lat, user_long, max_result=3)
    return []

def format_hospital_info(hospitals):
    if not hospitals:
        return "Sorry, I couldn't find any nearby hospitals at the moment."
    return "\n".join([f"- {hospital['name']}: {hospital['address']}" for hospital in hospitals])

def chatbot(user_input, disease_vector_store, hospital_vector_store, llm):
    query_embedding = generate_embeddings(user_input)

    # check if it's a diagnosis request
    if is_diagnosis_request(query_embedding):
        nearest_hospitals = get_nearest_hospitals()
        hospital_info = format_hospital_info(nearest_hospitals)
        return f"I'm not able to provide a diagnosis. Please consult with a heathcare professional. Here are the nearest hospitals:\n\n{hospital_info}"
    
    # check if it's a hospital request
    if is_hospital_request(query_embedding):
        nearest_hospitals = get_nearest_hospitals()
        hospital_info = format_hospital_info(nearest_hospitals)
        return f"Here are the nearest hospitals based on your location:\n\n{hospital_info}"
    
    # if it's neither, proceed with disease information search
    disease_search_result = perform_vector_search(disease_vector_store, query_embedding)
    hospital_search_result = perform_vector_search(hospital_vector_store, query_embedding)

    all_search_result = disease_search_result + hospital_search_result
    all_search_result.sort(key = lambda x: x.distance)

    top_results = all_search_result[:3]

    if not top_results:
        return "Sorry, I don't have specific information about that"
    
    context = "\n".join([result.document for result in top_results])

    prompt = f"""Context information:
{context}

User question: {user_input}

Based on the context information provided, please answer the user's question.
Keep the answer concise and to the point. If you're not sure, say so.

Answer:"""
    
    response = llm.complete(prompt)
    return response


def main():
    disease_vector_store, hospitals_vector_store, llm = setup_chatbot()
    print("Chatbot is ready. You can start asking questions. 'exit' to exit")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break
        response = chatbot(user_input, disease_vector_store, hospitals_vector_store, llm)
        print("Chatbot:", response)

if __name__ == "__main__":
    main()