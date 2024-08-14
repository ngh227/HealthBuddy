import os
import logging
from dotenv import load_dotenv
from tidb_vector.integrations import TiDBVectorClient

# Import all the functions from your existing code
from data_preprocessing import (
    generate_embeddings, get_db_connection, setup_vector_store,
    create_health_topics_table, create_clinics_table,
    fetch_medlineplus_data, store_in_tidb, load_disease_codes
)

DISEASE_CODES_FILE = "disease_codes.csv"  # Path to your CSV file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_medlineplus_data_ingestion():
    # Load environment variables
    load_dotenv()
    
    # Ensure the JINAAI_API_KEY is set
    if not os.getenv('JINAAI_API_KEY'):
        logger.error("JINAAI_API_KEY not set in environment variables")
        return

    # Ensure the TIDB_DATABASE_URL is set
    if not os.getenv('TIDB_DATABASE_URL'):
        logger.error("TIDB_DATABASE_URL not set in environment variables")
        return

    # Create necessary tables
    logger.info("Creating tables...")
    create_health_topics_table()
    create_clinics_table()

    # Setup vector store
    logger.info("Setting up vector store...")
    vector_store = setup_vector_store()

    # Load disease codes
    disease_codes = load_disease_codes(DISEASE_CODES_FILE)

    # Test with the three suggested diseases
    test_diseases = ["Type 2 Diabetes", "Hypertension", "Asthma"]

    logger.info("Fetching and storing data for diseases:")
    for disease_name in test_diseases:
        code = disease_codes.get(disease_name.lower())
        if code:
            logger.info(f"Processing disease: {disease_name} (Code: {code})")
            data = fetch_medlineplus_data(code)
            if data:
                logger.info(f"Found {len(data)} results")
                for item in data:
                    try:
                        store_in_tidb(item, vector_store)
                        logger.info(f"Stored item: {item['title']}")
                    except Exception as e:
                        logger.error(f"Error storing item: {item['title']}. Error: {str(e)}")
            else:
                logger.warning(f"No data found for disease: {disease_name} (Code: {code})")
        else:
            logger.warning(f"No code found for disease: {disease_name}")

    logger.info("Testing complete!")

    # Test vector search
    logger.info("Testing vector search...")
    test_query = "What are the symptoms of diabetes?"
    query_embedding = generate_embeddings(test_query)
    search_results = vector_store.query(query_embedding, top_k=3)
    logger.info(f"Search results for query: '{test_query}'")
    for result in search_results:
        logger.info(f"ID: {result.id}, Distance: {result.distance}, Metadata: {result.metadata}")

if __name__ == "__main__":
    test_medlineplus_data_ingestion()