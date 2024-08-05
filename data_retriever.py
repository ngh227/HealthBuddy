# data_retriever.py

import requests
from config import CONNECTION_STRING, MEDLINEPLUS_CONNECT_BASE_URL, GG_MAPS_API_KEY, IPAPI_URL
import pandas as pd
import googlemaps
from embedding_data import generate_embeddings

def get_medline_info(code, code_system='2.16.840.1.113883.6.90'):
    url = f"{MEDLINEPLUS_CONNECT_BASE_URL}?mainSearchCriteria.v.cs={code_system}&mainSearchCriteria.v.c={code}&knowledgeResponseType=application/json"
    response = requests.get(url)
    if response.status_code==200:
        data = response.json()
        entries = data.get('feed', {}).get('entry', [])

        results = []
        for entry in entries:
            title = entry.get('title', {}).get('_value', '')
            summary = entry.get('summary', {}).get('_value', '')
            link = next((l.get('href') for l in entry.get('link', []) if l.get('ref') == 'alternate'), '')

            results.append({
                'title': title,
                'summary': summary,
                'link': link
            })
        return results
    return None

# get user location using Geolocation API
def get_user_location():
    try:
        response = requests.get(IPAPI_URL)
        if response.status_code == 200:
            data = response.json()
            return data['latitude'], data['longitude']
    except Exception as e:
        print(f"Error getting location: {e}")
    return None

# get nearby clinics
def get_nearby_clinics(lat, lng, keyword=None):
    gmaps = googlemaps.Client(key=GG_MAPS_API_KEY)
    
    location = (lat, lng)
    radius = 5000  # Search within 5km radius
    type = 'hospital'
    
    try:
        if keyword:
            places_result = gmaps.places_nearby(location=location, radius=radius, type=type, keyword=keyword)
        else:
            places_result = gmaps.places_nearby(location=location, radius=radius, type=type)
        
        return places_result.get('results', [])[:3]  # return top 3 results
    except Exception as e:
        print(f"Error finding nearby hospital: {e}")
        return []
    
def format_clinic_info(clinics):
    if clinics:
        clinic_info = "Nearby clinics: \n"
        for i, clinic in enumerate(clinics, 1):
            clinic_info += f"{i}. {clinic['name']}, {clinic['fullAddress']}\n"
        return clinic_info
    return "Unable to retrieve clinic information"

def store_health_info(info, code, code_system, clinics, user_location):
    documents = []
    for entry in info:
        combined_text = f"{entry['title']} {entry['summary']}"
        doc = Document(text=combined_text, metadata={"code": code, "code_system": code_system})
        documents.append(doc)
    
    # use LlamaIndex to index and store the documents
    index.insert_nodes(documents)

    