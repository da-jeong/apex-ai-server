# 데이터를 벡터로 만들어서 qdrant에 업로드
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, CollectionStatus
from decouple import config

QDRANT_KEY = config("QDRANT_KEY")
QDRANT_URL = config("QDRANT_URL")
#임시 함수
def dummy_embedding(text):
    np.random.seed(hash(text) % (2**32))
    return np.random.rand(1536).tolist()

#Qdrant 연결
# client = QdrantClient(host="localhost", port=6333)
client = QdrantClient(
    url = QDRANT_URL,
    api_key = QDRANT_KEY

)

#컬렉션 이름
COLLECTION_NAME = "stock_segments"

#컬렉션 생성 함수 이미 존재하면 생략하기
def create_collection_if_not_exists():
    existing = [col.name for col in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name = COLLECTION_NAME, 
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="company", 
            field_schema="keyword"
        )
        print(f"컬렉션 '{COLLECTION_NAME}' 생성 완료 (인덱스 포함)")
    else:
        # 인덱스가 없을 수도 있으니 다시 생성 시도
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="company", 
                field_schema="keyword"
            )
            print("인덱스 추가 생성 완료")
        except Exception as e:
            print("인덱스 이미 있음 또는 오류:", e)


#segements 업로드
def upload_segments(company, segments):
    create_collection_if_not_exists()

    points = []
    for i, text in enumerate(segments):
        embedding = dummy_embedding(text)
        point = PointStruct(
            id=i, 
            vector=embedding, 
            payload={
                "company":company, 
                "text" : text
            }
        )
        points.append(point)
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"{len(points)}개 업로드 완료")