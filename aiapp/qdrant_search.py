from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import numpy as np
from decouple import config

QDRANT_KEY = config("QDRANT_KEY")
QDRANT_URL = config("QDRANT_URL")

#예시 임베딩
def dummy_embedding(text):
    np.random.seed(hash(text)% (2**32))
    return np.random.rand(1536).tolist()

client = QdrantClient(
    url = QDRANT_URL,
    api_key = QDRANT_KEY

)
# print(client.get_collections())
COLLECTION_NAME = "stock_segments"

def search_segments(company, question, top_k=5):
    query_vector = dummy_embedding(question)
    
    hits = client.search(
        collection_name=COLLECTION_NAME, 
        query_vector=query_vector,
        limit = top_k, 
        query_filter=Filter(
            must = [
                FieldCondition(
                    key = "company", 
                    match=MatchValue(value=company)
                )
            ]
        ),
        with_payload = True
    )
    return [hit.payload["text"] for hit in hits]
