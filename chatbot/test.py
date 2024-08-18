import os
import logging
from dotenv import load_dotenv
# from tidb_vector.integrations import TiDBVectorClient

# from data_preprocessing import (
#     generate_embeddings, setup_disease_vector_store,
#     create_health_topics_table, fetch_medlineplus_data, 
#     store_disease_in_tidb, load_disease_codes
# )
from hospital_functions import (
    create_hospitals_table, get_user_location,
    find_nearest_hospital, embed_hospital_info,
    store_hospital_in_tidb, setup_hospital_vector_store
)

# DISEASE_CODES_FILE = "disease_codes.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment_variables():
    logger.info("Testing environment variables...")
    required_vars = ['TIDB_DATABASE_URL', 'GG_MAPS_API_KEY']  # Removed 'JINAAI_API_KEY'
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"{var} not set in environment variables")
            return False
    logger.info("All required environment variables are set.")
    return True

def test_database_setup():
    logger.info("Testing database setup...")
    try:
        # create_health_topics_table()
        create_hospitals_table()
        logger.info("Database tables created successfully.")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def test_vector_stores():
    logger.info("Testing vector store setup...")
    try:
        # disease_vector_store = setup_disease_vector_store()
        hospital_vector_store = setup_hospital_vector_store()
        logger.info("Vector stores set up successfully.")
        return hospital_vector_store
    except Exception as e:
        logger.error(f"Error setting up vector stores: {e}")
        return None

# def test_disease_code_mapping():
#     logger.info("Testing disease code mapping...")
#     disease_codes = load_disease_codes(DISEASE_CODES_FILE)
#     test_diseases = [("Type 2 Diabetes", "E11"), ("Hypertension", "I10"), ("Asthma", "J45")]
#     for disease_name, expected_code in test_diseases:
#         code = disease_codes.get(disease_name.lower())
#         if code == expected_code:
#             logger.info(f"✓ Correct code mapping: {disease_name} -> {code}")
#         else:
#             logger.error(f"✗ Incorrect code mapping: {disease_name} -> {code} (Expected: {expected_code})")
#     return disease_codes

# def test_medlineplus_data_ingestion(disease_codes, disease_vector_store):
#     logger.info("Testing MedlinePlus data ingestion...")
#     test_diseases = ["Type 2 Diabetes", "Hypertension", "Asthma"]
#     for disease_name in test_diseases:
#         code = disease_codes.get(disease_name.lower())
#         if code:
#             logger.info(f"Processing disease: {disease_name} (Code: {code})")
#             data = fetch_medlineplus_data(code)
#             if data:
#                 logger.info(f"Found {len(data)} results for {disease_name}")
#                 for item in data:
#                     try:
#                         store_disease_in_tidb(item, disease_vector_store)
#                         logger.info(f"✓ Stored item: {item['title']}")
#                     except Exception as e:
#                         logger.error(f"✗ Error storing item: {item['title']}. Error: {str(e)}")
#             else:
#                 logger.warning(f"No data found for disease: {disease_name} (Code: {code})")
#         else:
#             logger.warning(f"No code found for disease: {disease_name}")

# def test_disease_vector_search(disease_vector_store):
#     logger.info("Testing disease vector search...")
#     test_queries = [
#         "What are the symptoms of asthma?",
#         "How is diabetes treated?",
#         "What causes hypertension?"
#     ]
#     for query in test_queries:
#         query_embedding = generate_embeddings(query)
#         search_results = disease_vector_store.query(query_embedding, top_k=1)
#         if search_results:
#             result = search_results[0]
#             logger.info(f"Query: '{query}'")
#             logger.info(f"Top result - ID: {result.id}, Distance: {result.distance}, Metadata: {result.metadata}")
#         else:
#             logger.error(f"No results found for query: '{query}'")

def test_hospital_functions(hospital_vector_store):
    logger.info("Testing hospital functions...")
    user_lat, user_long = get_user_location()
    if user_lat and user_long:
        logger.info(f"User location: Latitude {user_lat}, Longitude {user_long}")
        hospitals = find_nearest_hospital(user_lat, user_long)
        if hospitals:
            logger.info(f"Found {len(hospitals)} nearby hospitals")
            embedded_hospitals = embed_hospital_info(hospitals)
            for hospital in embedded_hospitals:
                try:
                    store_hospital_in_tidb(hospital, hospital_vector_store)
                    logger.info(f"✓ Stored hospital: {hospital['name']}")
                except Exception as e:
                    logger.error(f"✗ Error storing hospital: {hospital['name']}. Error: {str(e)}")
        else:
            logger.warning("No nearby hospitals found")
    else:
        logger.error("Failed to get user location")

def main():
    load_dotenv()

    if not test_environment_variables():
        return

    if not test_database_setup():
        return

    hospital_vector_store = test_vector_stores()
    if not hospital_vector_store:
        return

    # disease_codes = test_disease_code_mapping()
    # test_medlineplus_data_ingestion(disease_codes, disease_vector_store)
    # test_disease_vector_search(disease_vector_store)
    test_hospital_functions(hospital_vector_store)

    logger.info("All tests completed.")

if __name__ == "__main__":
    main()