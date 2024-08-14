# Preprocess data from Medline Connect
# Use Jina AI for embeddings generalization
# Store embeddings and associated metadata in TiDB

import os
import pymysql
import requests
import csv
from typing import List, Dict, Optional
from time import sleep
from dotenv import load_dotenv
from tidb_vector.integrations import TiDBVectorClient

load_dotenv()
JINAAI_API_KEY = os.getenv('JINAAI_API_KEY')
MEDLINEPLUS_CONNECT_BASE_URL = "https://connect.medlineplus.gov/service"
ICD10_CODE_SYSTEM = "2.16.840.1.113883.6.90"
# CONNECTION_STRING = os.getenv('TIDB_DATABASE_URL')

def generate_embeddings(text: str):
    JINAAI_API_URL = 'https://api.jina.ai/v1/embeddings'
    JINAAI_HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {JINAAI_API_KEY}'
    }
    JINAAI_REQUEST_DATA = {
        'input': [text],
        'model': 'jina-embeddings-v2-base-en'  # with dimension 768
    }
    response = requests.post(JINAAI_API_URL, headers=JINAAI_HEADERS, json=JINAAI_REQUEST_DATA)
    return response.json()['data'][0]['embedding']

def get_db_connection():
    return pymysql.connect(
        host = "gateway01.us-east-1.prod.aws.tidbcloud.com",
        port = 4000,
        user = "4LGwjP9LLkyZsPM.root",
        password = "8UtljhBzTizGLCmZ",
        database = "test",
        ssl_verify_cert = True,
        ssl_verify_identity = True,
        ssl_ca = "/etc/ssl/cert.pem"
    )

def setup_vector_store():
    return TiDBVectorClient(
        connection_string=os.getenv('TIDB_DATABASE_URL'),
        table_name="health_topics",
        distance_strategy="cosine",
        vector_dimension=768,  # Dimension of Jina embeddings
        drop_existing_table=True
    )

def create_health_topics_table():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_topics (
                id BIGINT AUTO_RANDOM PRIMARY KEY,
                title VARCHAR(255),
                summary TEXT,
                link VARCHAR(255),
                code VARCHAR(50),
                code_system VARCHAR(50),
                embedding LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
        connection.commit()
        print("health_topics table created successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()

def create_clinics_table():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinics (
                id BIGINT AUTO_RANDOM PRIMARY KEY,
                place_id VARCHAR(255) UNIQUE,
                name VARCHAR(255),
                address VARCHAR(255),
                latitude FLOAT,
                longitude FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
        connection.commit()
        print("clinics table created successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()
#### CODE READER ########################################################################
def load_disease_codes(file_path: str) -> Dict[str, str]:
    disease_codes = {}
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  
        for row in reader:
            if len(row) == 2:
                disease_name, code = row
                disease_codes[disease_name.lower()] = code
    return disease_codes

def get_disease_code(disease_name, file_path):
    disease_codes = load_disease_codes(file_path)
    return disease_codes.get(disease_name.lower())

##### FETCHING PROBLEM #####
'''Fix: Switch to search with disease code'''
# def fetch_medlineplus_data(condition, max_retries=3):
#     base_url = "https://connect.medlineplus.gov/application"
#     params = {
#         "mainSearchCriteria.v.cs": "name",#"2.16.840.1.113883.6.90",
#         "mainSearchCriteria.v.c": condition,
#         "knowledgeResponseType": "application/json"
#     }
    
#     for attempt in range(max_retries):
#         try:
#             response = requests.get(base_url, params=params)
#             response.raise_for_status()  
            
#             data = response.json()
#             if 'feed' in data and 'entry' in data['feed']:
#                 entries = data['feed']['entry']
#                 if not isinstance(entries, list):
#                     entries = [entries]
                
#                 results = []
#                 for entry in entries:
#                     result = {
#                         'title': entry.get('title', ''),
#                         'summary': entry.get('summary', {}).get('_value', ''),
#                         'link': next((link['href'] for link in entry.get('link', []) if link.get('title') == 'MedlinePlus Health Information'), None),
#                         'code': entry.get('id', '').split('/')[-1],
#                         'code_system': 'MedlinePlus'

#                         # 'title': entry.get('title', ''),
#                         # 'summary': entry.get('summary', ''),
#                         # 'link': next((link['href'] for link in entry.get('link', []) if link.get('rel') == 'alternate'), None),
#                         # 'code': entry.get('category', [{}])[0].get('term'),
#                         # 'code_system': entry.get('category', [{}])[0].get('scheme')
#                     }
#                     results.append(result)
                
#                 return results
            
#             return None
        
#         except requests.RequestException as e:
#             if attempt == max_retries - 1:
#                 print(f"Error fetching data: {e}")
#                 return None
#             sleep(1) 
#     return None

def fetch_medlineplus_data(code):
    url = f"{MEDLINEPLUS_CONNECT_BASE_URL}?mainSearchCriteria.v.cs={ICD10_CODE_SYSTEM}&mainSearchCriteria.v.c={code}&knowledgeResponseType=application/json"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        entries = data.get('feed', {}).get('entry', [])

        if not isinstance(entries, list):
            entries = [entries]

        results = []
        for entry in entries:
            title = entry.get('title', {}).get('_value', '') if isinstance(entry.get('title'), dict) else entry.get('title', '')
            summary = entry.get('summary', {}).get('_value', '')
            link = next((l.get('href') for l in entry.get('link', []) if l.get('rel') == 'alternate'), '')


            results.append({
                'title': title,
                'summary': summary,
                'link': link,
                'code': code,
                'code_system': ICD10_CODE_SYSTEM
            })
        return results
    else:
        print(f"Error fetching data for code {code}: Status code {response.status_code}")
        return None


def store_in_tidb(item, vector_store):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # check if item exists
            # check_sql = "SELECT id, title, summary, link FROM health_topics WHERE code = %s"
            # cursor.execute(check_sql, (item['code'],))
            # existing_data = cursor.fetchone()

            embedding = generate_embeddings(item['summary'])
            embedding_str = ','.join(map(str, embedding))

            # if existing_data:
            #     # Update existing entry
            #     update_sql = """
            #     UPDATE health_topics 
            #     SET title = %s, summary = %s, link = %s, code_system = %s, embedding = %s
            #     WHERE code = %s
            #     """
            #     cursor.execute(update_sql, (
            #         item['title'],
            #         item['summary'],
            #         item['link'],
            #         item['code_system'],
            #         embedding_str,
            #         item['code']
            #     ))
                # If the item exists, append new information
                # existing_title, existing_summary, existing_link = existing_data
                # new_title = f"{existing_title}; {item['title']}"
                # new_summary = f"{existing_summary}\n\nAdditional Information:\n{item['summary']}"
                # new_link = f"{existing_link}; {item['link']}"
            # else:
            insert_sql = """
            INSERT INTO health_topics 
            (title, summary, link, code, code_system, embedding) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                item['title'],
                item['summary'],
                item['link'],
                item['code'],
                item['code_system'],
                embedding_str
            ))

            cursor.execute("SELECT LAST_INSERT_ID()")
            db_id = cursor.fetchone()[0]
        connection.commit()
        print(f"Inserted new item with ID: {db_id}")
                # If it's a new item, use the provided information
            #     new_title = item['title']
            #     new_summary = item['summary']
            #     new_link = item['link']
            
            # embedding = generate_embeddings(new_summary)
            # embedding_str = ','.join(map(str, embedding))
            # sql = """
            # INSERT INTO health_topics 
            # (title, summary, link, code, code_system, embedding) 
            # VALUES (%s, %s, %s, %s, %s, %s)
            # ON DUPLICATE KEY UPDATE
            # title = VALUES(title),
            # summary = VALUES(summary),
            # link = VALUES(link),
            # code_system = VALUES(code_system),
            # embedding = VALUES(embedding)
            # """

        #     cursor.execute(sql, (
        #         new_title,
        #         new_summary,
        #         new_link,
        #         item['code'],
        #         item['code_system'],
        #         embedding_str
        #     ))
        # connection.commit()
        # print(f"Successfully stored item: {item['title']}")

        # Add to vector store
        vector_store.insert(
            ids=[str(db_id)],
            texts=[item['summary']],
            embeddings=[embedding],
            metadata=[{
                "title": item['title'],
                "link": item['link'],
                "code": item['code'],
                "code_system": item['code_system']
            }]
        )

    except Exception as e:
        print(f"An error occurred while storing the item: {e}")
        connection.rollback()

    finally:
        connection.close()
    
def ingest_medlineplus_data(conditions):
    for condition in conditions:
        data = fetch_medlineplus_data(condition)
        if data:
            for item in data:
                store_in_tidb(item)
                print(item)



