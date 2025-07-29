from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from .qdrant_search import search_segments
import re
from django.core.cache import cache
from decouple import config

API_KEY = config("API_KEY")
ENDPOINT = config("API_URL")

# Create your views here.
# @csrf_exempt
# def feedback(request):
#     if request.method == 'POST':
#         body = json.loads(request.body)
#         company = body.get('company')
#         question = body.get('question')
#         # segments = body.get('segments', [])
#         #Qdrant 에서 관련 문단 3개 가져오기
#         segments = search_segments(company, question, top_k=3)
#         #가져온 문단 하나의 문자열로 묶기
#         context = "\n".join(f"{i+1}) {s}" for i, s in enumerate(segments))

#         prompt = f"""다음은 주식 관련 정보입니다:
# {context}

# 사용자 질문: "{question}"
# 아래 항목을 정확히 형식에 맞춰 출력해주세요: 

# 1. 권고 : 매수 / 보유 / 매도 중 하나 (예: 권고: 매수)
# 2. 추천 강도 : 강 / 중 / 약 중 하나 (예: 추천 강도 : 강)
# 3. 판단 근거 : 
# - 근거1
# - 근거2
# - 근거3 ....
# 4. 근거 상세 보기: 상세 설명 텍스트 (50~100자)
# """

#         # API KEY와 endpoint
#         API_KEY = "Bearer nv-cfbdd2fc8f8b4b19ab04c950fd9718b6LaTN" 
#         ENDPOINT = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"

#         #헤더
#         headers = {
#             "Content-Type": "application/json",
#             "Authorization": API_KEY
#             }

#         # 메시지 구성
#         data = {
#             "messages": [
#                 {"role": "system", "content": "당신은 주식 투자 전문가입니다."},
#                 {"role": "user", "content": prompt}
#             ],
#             "temperature": 0.5,
#             "topP": 0.8,
#             "topK": 0,
#             "maxTokens": 512,
#             "repeatPenalty": 5.0,
#             "includeAiFilters": True
#         }
#         response = requests.post(ENDPOINT, headers=headers, data=json.dumps(data))

#         if response.status_code == 200:
#             result = response.json()
#             answer = result["result"]["message"]["content"]
        
#             parsed = parse_feedback_answer(answer)

#             return JsonResponse({
#                 "company":company, 
#                 "question":question,
#                 # "raw_answer":answer
#                 "feedback" : parsed
#             })
#         else:
#             return JsonResponse({"error":"HyperCLOVA 응답 오류", "status":response.status_code})
@csrf_exempt
def feedback(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        company = body.get('company')
        question = body.get('question')
        recommendation = body.get('recommendation')
        strength = body.get('strength')

        # 캐시 확인
        cache_key = f"feedback:{company}:{question}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(json.loads(cached), safe=False)#캐시 있음 바로 리턴

        # segments = body.get('segments', [])
        #Qdrant 에서 관련 문단 3개 가져오기
        segments = search_segments(company, question, top_k=5)
        #가져온 문단 하나의 문자열로 묶기
        context = "\n".join(f"{i+1}) {s}" for i, s in enumerate(segments))

        prompt = f"""다음은 주식 관련 정보입니다:
{context}

사용자 질문: "{question}"
[제공된 판단 결과]
- 권고 : {recommendation}
- 추천 강도 : {strength}

아래 항목을 정확히 형식에 맞춰 출력해주세요: 

1. 권고 : {recommendation}
2. 추천 강도 : {strength}
3. 판단 근거 : 
- 근거1
- 근거2
- 근거3 ....
4. 근거 상세 보기: 상세 설명 텍스트 (50~100자)

제공된 정보 범위 내에서 판단하고, 불확실하고 정확하지 않은 내용은 생략해주세요.
"""
        #헤더
        headers = {
            "Content-Type": "application/json",
            "Authorization": API_KEY
            }

        # 메시지 구성
        data = {
            "messages": [
                {"role": "system", "content": "당신은 주식 투자 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 512,
            "repeatPenalty": 5.0,
            "includeAiFilters": True
        }
        response = requests.post(ENDPOINT, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            result = response.json()
            answer = result["result"]["message"]["content"]
        
            parsed = parse_feedback_answer(answer)
            
            result_data = {
                "company":company, 
                "question":question,
                "recommendation" : recommendation,
                "strength" : strength,
                # "raw_answer":answer
                "feedback" : parsed
            }

            #캐시 저장
            cache.set(cache_key, json.dumps(result_data), timeout=600)
            print("캐시 저장 완료:", cache_key)

            return JsonResponse(result_data)
        else:
            return JsonResponse({"error":"HyperCLOVA 응답 오류", "status":response.status_code})

@csrf_exempt
def summary(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        company = body.get('company')
        price = body.get('price')
        change = body.get('change')

        cache_key = f"summary:{company}:{price}:{change}"
        cached = cache.get(cache_key)
        if cached: 
            return JsonResponse(json.loads(cached), safe=False)#캐시 있음 바로 리턴
        
        # segments = body.get('segments', [])
        segments = search_segments(company, "", top_k=5)
        context = "\n".join(segments)

        prompt = f"""다음은 {company} 관련 주식 정보입니다:
{context}

{company}의
현재가: {price}
전일 대비 등락폭: {change}

위의 정보를 바탕으로 2~3문장으로 종목에 대한 간단한 요약 설명을 작성하세요

제공된 정보 범위 내에서 판단하고, 불확실하고 정확하지 않은 내용은 생략해주세요.
"""
        #헤더
        headers = {
            "Content-Type": "application/json",
            "Authorization": API_KEY
            }

        data = {
            "messages": [
                {"role": "system", "content": "당신은 주식 투자 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 512,
            "repeatPenalty": 5.0,
            "includeAiFilters": True
    }

        # API 호출
        response = requests.post(ENDPOINT, headers=headers, data=json.dumps(data))

        # 응답 처리
        if response.status_code == 200:
            result = response.json()
            answer = result["result"]["message"]["content"]
            
            # parsed = parse_summary_answer(answer)

            result_data={
                "company":company,
                "price": price,
                "change" : change,
                "summary" : answer.strip()
            }

            cache.set(cache_key, json.dumps(result_data), timeout=600)
            return JsonResponse(result_data)
        else:
            return JsonResponse({"error": "HyperCLOVA 요약 오류", "status":response.status_code})

@csrf_exempt        
def sentiment(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        company = body.get('company')
        pos_ratio = body.get('pos_ratio')
        neg_ratio = body.get('neg_ratio')
        volume = body.get('volume')
        level = body.get('level')

        cache_key = f"sentiment:{company}:{round(pos_ratio, 3)}:{round(neg_ratio, 3)}:{volume}:{level}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(json.loads(cached), safe=False)

        prompt = f"""
다음은 {company} 종목의 감정 데이터입니다.

긍정 언급 비율 : {round(pos_ratio * 100)}%
부정 언급 비율 : {round(neg_ratio * 100)}%
전체 언급량 : {volume}건
시장 감정 과열 수준 : {level}

이 데이터를 기반으로 아래 항목을 형식에 맞게 출력해주세요: 

1. 이모지 : {level} 에 맞는 이모지 (🔴 = 상/ 🟡 = 중/ 🟢 = 하)
2. 판단 근거 : 
- 근거1
- 근거2
- 근거3 ....

제공된 정보 범위 내에서 판단하고, 불확실하고 정확하지 않은 내용은 생략해주세요.
"""
        #헤더
        headers = {
            "Content-Type": "application/json",
            "Authorization": API_KEY
            }
        
        data = {
        "messages": [
            {"role": "system", "content": "당신은 주식 시장 심리 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "topP": 0.8,
        "topK": 0,
        "maxTokens": 256,
        "repeatPenalty": 5.0,
        "includeAiFilters": True
        }

        # API 호출
        response = requests.post(ENDPOINT, headers=headers, data=json.dumps(data))

        # 응답 처리
        if response.status_code == 200:
            result = response.json()
            answer = result["result"]["message"]["content"]
            
            parsed = parse_sentiment_answer(answer)

            result_data = {
                "company": company,
                "pos_ratio": pos_ratio,
                "neg_ratio": neg_ratio,
                "volume": volume,
                "level": level,
                "sentiment": parsed
            }

            cache.set(cache_key, json.dumps(result_data), timeout=300)

            return JsonResponse(result_data)
        else:
            return JsonResponse({"error": "HyperCLOVA 감정 판단 오류", "status":response.status_code})

        
def parse_feedback_answer(answer_text: str) -> dict:
    try:
        # recommendation_match = re.search(r"권고\s*[:：]\s*(매수|보유|매도)", answer_text)
        # strength_match = re.search(r"추천 강도\s*[:：]\s*(강|중|약)", answer_text)

        # recommendation = recommendation_match.group(1) if recommendation_match else ""
        # strength = strength_match.group(1) if strength_match else ""

        reasons = re.findall(r"[-•]\s*(.+)", answer_text)

        detail_match = re.search(r"근거 상세 보기\s*[:：]\s*(.+)", answer_text)
        detail = detail_match.group(1).strip() if detail_match else ""

        return {
            # "recommendation" : recommendation,
            # "strength" : strength, 
            "reasons" : reasons, 
            "detail" : detail
        }
    except Exception:
        return{
            "reasons" : [], 
            "detail" : "", 
            "raw_answer": answer_text, 
            "error" : "파싱 실패"
        }

def parse_sentiment_answer(answer_text : str) -> dict:
    try:
        # 과열 수준
        level_match = re.search(r"시장 감정 과열 수준\s*[:：]?\s*(상|중|하)", answer_text)
        level = level_match.group(1) if level_match else ""

        # 이모지
        emoji_match = re.search(r"이모지\s*[:：]?\s*(🔴|🟡|🟢)", answer_text)
        emoji = emoji_match.group(1) if emoji_match else ""
            
        # 판단 근거
        reasons = re.findall(r"[•\-–]\s*(.+)", answer_text)

        return {
            "emoji" : emoji, 
            "reasons" : reasons
        }
    except Exception:
        return {
            "emoji" : "", 
            "reasons" : "",
            "raw_answer" : answer_text,
            "error" : "파싱 실패"
        }
