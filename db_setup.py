# db_setup.py

import pymysql
from config import CONNECTION_STRING
from llama_index.vector_stores.tidbvector import TiDBVectorStore

def setup_vector_store():
    tidb_vector_store = TiDBVectorStore(
        connection_string = CONNECTION_STRING,
        table_name = "health_topics",
        distance_strategy = "cosine",
        vector_dimension = 768,
        drop_existing_table=False
    )
    return tidb_vector_store

# def create_vector_table():
#     # Parse the connection string to get the necessary components
#     parts = CONNECTION_STRING.split('/')
#     database = parts[-1].split('?')[0]
#     host_port = parts[2].split('@')[1].split(':')
#     host = host_port[0]
#     port = int(host_port[1])
#     user_pass = parts[2].split('@')[0].split(':')
#     user = user_pass[0]
#     password = user_pass[1]

#     # Connect to the database
#     connection = pymysql.connect(
#         host=host,
#         port=port,
#         user=user,
#         password=password,
#         database=database
#     )

#     try:
#         with connection.cursor() as cursor:
#             # Create the vector table
#             cursor.execute("""
#             CREATE TABLE IF NOT EXISTS health_topics (
#                 id BIGINT AUTO_RANDOM PRIMARY KEY,
#                 text TEXT,
#                 metadata JSON,
#                 vector VECTOR(768) AS (embedding) STORED,
#                 embedding BLOB
#             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
#             """)
        
#         print("Vector table 'health_topics' created successfully.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         connection.close()

if __name__ == "__main__":
    setup_vector_store()