from llama_index.vector_stores.tidbvector import TiDBVectorStore
from llama_index import VectorStoreIndex, StorageContext
from llama_index.schema import Document
from embedding_data import generate_embeddings
from data_retriever import get_medline_info, get_nearby_clinics, get_user_location, format_clinic_info
from config import CONNECTION_STRING

def setup_index():
    # Reconnect to the TiDBVectorStore
    tidb_vector_store = TiDBVectorStore(
        connection_string=CONNECTION_STRING,
        table_name="health_topics",
        distance_strategy="cosine",
        vector_dimension=768,
        drop_existing_table=False
    )

    # Recreate the index
    storage_context = StorageContext.from_defaults(vector_store=tidb_vector_store)
    index = VectorStoreIndex([], storage_context=storage_context)
    return index

def get_response(user_query):
    # Use LlamaIndex for querying
    query_engine = index.as_query_engine()
    response = query_engine.query(user_query)
    
    return str(response)

def chatbot():
    print("Welcome to the Medical Chatbot. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = get_response(user_input)
        print("Chatbot:", response)

if __name__ == "__main__":
    chatbot()