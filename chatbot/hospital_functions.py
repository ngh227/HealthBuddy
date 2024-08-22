import os
import requests
import logging
from googlemaps import Client as GoogleMaps
from googlemaps.exceptions import ApiError
from datetime import datetime

from dotenv import load_dotenv
from tidb_vector.integrations import TiDBVectorClient
from data_preprocessing import generate_embeddings

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv('GG_MAPS_API_KEY')

HOSPITAL_PHRASES = [
    "find nearest hospital", "closest medical center",
    "emergency room near me", "where's the nearest clinic",
    "closest healthcare facility", "find a hospital",
    "medical help nearby", "urgent care location",
    "nearest doctor's office", "hospital directions"
]

def setup_hospital_vector_store():
    return TiDBVectorClient(
        connection_string=os.getenv('TIDB_DATABASE_URL'),
        table_name="hospitals",
        distance_strategy="cosine",
        vector_dimension=768,
        drop_existing_table=True
    )

def setup_hospital_request_vector_store():
    hospital_request_vector_store = TiDBVectorClient(
        connection_string=os.getenv('TIDB_DATABASE_URL'),
        table_name="hospital_request_phrases",
        distance_strategy="cosine",
        vector_dimension=768,
        drop_existing_table=True
    )
    for phrase in HOSPITAL_PHRASES:
        embedding = generate_embeddings(phrase)
        hospital_request_vector_store.insert(
            ids=[phrase],
            texts=[phrase],
            embeddings=[embedding],
            metadatas=[{"type": "hospital_request_phrase"}]
        )
    return hospital_request_vector_store

hospital_request_vector_store = setup_hospital_request_vector_store()

def is_hospital_request(query_embedding, threshold=0.85):
    results = hospital_request_vector_store.query(query_embedding, top_k=1)
    if results:
        return (1 - results[0].distance) > threshold
    return False

def get_user_location():
    try:
        response = requests.get('https://ipapi.co/json/')
        if response.status_code == 200:
            data = response.json()
            return data.get('latitude'), data.get('longitude')
        else:
            print(f"Error: Unable to fetch location. Status code: {response.status_code}")
            return None, None
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None, None

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def find_nearest_hospital(user_lat, user_long, radius=5000, max_result=3):
    try:
        gmaps = GoogleMaps(key=GOOGLE_MAPS_API_KEY)
        logger.debug("GoogleMaps client initialized")
        
        places_result = gmaps.places_nearby(
            location=(user_lat, user_long),
            radius=radius,
            type='hospital'
        )
        logger.debug(f"API Response: {places_result}")
        
        hospitals = []
        for place in places_result.get('results', [])[:max_result]:
            hospitals.append({
                'name': place['name'],
                'address': place.get('vicinity', 'Address not available'),
                'latitude': place['geometry']['location']['lat'],
                'longitude': place['geometry']['location']['lng']
            })
        
        logger.info(f"Found {len(hospitals)} hospitals")
        return hospitals
    
    except ApiError as e:
        logger.error(f"Google Maps API Error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []