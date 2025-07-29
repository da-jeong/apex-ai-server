# 실제 실행해서 업로드
from qdrant_upload import upload_segments

######한번만 컬렉션 삭제
# from qdrant_upload import client, COLLECTION_NAME
# client.delete_collection(collection_name=COLLECTION_NAME)

#예시임..
company = "SK 하이닉스"

segments = [
    "SK하이닉스는 메모리 반도체 업황 회복으로 실적 개선 기대가 커지고 있다.",
    "최근 외국인 투자자의 순매수세가 이어지고 있다.",
    "중국 수출 제한 우려가 있으나 단기 이슈로 해석되는 분위기다."
]

upload_segments(company, segments)