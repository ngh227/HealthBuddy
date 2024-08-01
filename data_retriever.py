import requests
import re
import mysql.connector
import pandas as pd
from config import MEDLINEPLUS_CONNECT_BASE_URL, TIDB_CONFIG

 
def get_medline_info(code, code_system='2.16.840.1.113883.6.90'):
    url = f"{MEDLINEPLUS_CONNECT_BASE_URL}?mainSearchCriteria.v.cs={code_system}&mainSearchCriteria.v.c={code}&knowledgeResponseType=application/json"
    response = requests.get(url)
    if response.status_code==200:
        data = response.json()
        if 'feed' in data and 'entry' in data['feed']:
            return data['feed']['entry'][0]
        return None
''' 
INFO: For diagnosis codes, medline returns:
- page title
- page url
- synonyms, if available ("Also called")
- page summary
- summary attribution
'''
def retrieve_health_data(connection, code, code_system, info):
    cursor = connection.cursor()
    # retrieve disease information
    disease_sql = """
    INSERT INTO diseases (id, name, description, url)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    url = VALUES(url)
    """

    disease_data = (
        code,
        info['title'],
        info.get('summary', ''),
        info['link'][0]['href']
    )
    cursor.execute(disease_sql, disease_data)

    # insert symptoms if available
    summary = info['summary']['_value']
    symptoms_match = re.search(r'Symptoms may include:(.*?)(?:<\/p>|<p>)', summary, re.DOTALL)
    if symptoms_match:
        symptoms_text = symptoms_match.group(1).strip()
        symptoms_text = re.sub(r'<.*?>', '', symptoms_text)  # Remove HTML tags
        symptoms_text = re.sub(r'\s+', ' ', symptoms_text)   # Remove extra whitespace
        symptoms_text = symptoms_text.replace('&nbsp;', ' ') # Replace &nbsp; with space
        symptoms = [symptom.strip() for symptom in symptoms_text.split(',') if symptom.strip()]

        for symptom in symptoms:
            symptom_sql = "INSERT IGNORE INOT symptoms (name) VALUES (%s)"
            cursor.execute(symptom_sql, (symptom,))

            # get the inserted symptom id
            cursor.execute("SELECT id FROM symptoms WHERE name = %s", (symptom,))
            symptom_id = cursor.fetchone()[0]
            # disease - symptom relation
            relation_sql = "INSERT IGNORE INTO disease_symptoms (disease_id, symptom_id) VALUES (%s, %s)"
            cursor.execute(relation_sql, (code, symptom_id))

    connection.commit()


def main():
    connection = mysql.connector.connect(**TIDB_CONFIG)
    
    