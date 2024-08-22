import os
from tidb_vector.integrations import TiDBVectorClient
from data_preprocessing import (
    generate_embeddings
)
DIAGNOSIS_PHRASES = [
    "diagnose me", "what do i have",
    "what's wrong with me", "what is my condition",
    "do I have a disease", "am I sick",
    "why am I feeling this way", "what's causing this",
    "is this serious", "should I be worried",
    "what does this pain mean", "explain my health issue",
    "medical interpretation needed", "assess my health",
    "could this be dangerous", "what's happening to me",
    "identify my problem"
]
def setup_diagnosis_vector_store():
    diagnosis_vector_store = TiDBVectorClient(
        connection_string=os.getenv('TIDB_DATABASE_URL'),
        table_name="diagnosis_phrases",
        distance_strategy="cosine",
        vector_dimension=768,
        drop_existing_table=True
    )
    for phrase in DIAGNOSIS_PHRASES:
        embedding = generate_embeddings(phrase)
        diagnosis_vector_store.insert(
            ids = [phrase],
            texts = [phrase],
            embeddings= [embedding],
            metadatas = [{"type": "diagnosis_phrase"}]
        )
    return diagnosis_vector_store
diagnosis_vector_store = setup_diagnosis_vector_store()

def is_diagnosis_request(query_embedding, threshold = 0.85):
    results = diagnosis_vector_store.query(query_embedding, top_k = 1)
    if results:
        return (1 - results[0].distance) > threshold
    return False