# config.py

import os 
from dotenv import load_dotenv

load_dotenv()

JINAAI_API_KEY = os.getenv('JINAAI_API_KEY')
MEDLINEPLUS_CONNECT_BASE_URL = "https://connect.medlineplus.gov/service"
CONNECTION_STRING = os.getenv('TIDB_DATABASE_URL')
IPAPI_URL = 'https://ipapi.co/json/'
GG_MAPS_API_KEY = os.getenv('GG_MAPS_API_KEY')