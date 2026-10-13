'''
Tavily 부품 단위 테스트 코드 (test_tavily.py)
기사 본문 스니펫 수집 여부와 TC-1 기준(검색 소요 시간 15초 이내)을 한 번에 검증하는 테스트 스크립트
'''

import os
import time
from dotenv import load_dotenv
from tavily import TavilyClient

# 1. 환경변수 로드
load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError("❌ .env 파일에서 TAVILY_API_KEY를 찾을 수 없습니다.")

client = TavilyClient(api_key=api_key)

# 2. 테스트 쿼리 실행 (물류 AI 배차 관련 실무 지시 시뮬레이션)
query = "물류 AI 배차 최적화 도입 동향"
print(f"🔍 검색 시작: '{query}'")

start_time = time.time()

response = client.search(
    query=query,
    search_depth="basic",
    max_results=5,
    include_raw_content=False
)

elapsed_time = time.time() - start_time

# 3. 결과 및 TC-1 기준 검증 출력
articles = response.get("results", [])
print(f"\n⏱️ 소요 시간: {elapsed_time:.2f}초 (TC-1 기준: 15초 이내)")
print(f"📦 수집 기사 수: {len(articles)}건 (목표: 5건)\n")

for i, article in enumerate(articles, 1):
    print(f"[{i}] {article.get('title')}")
    print(f"    - URL: {article.get('url')}")
    print(f"    - 내용 스니펫(앞 100자): {article.get('content')[:100]}...\n")

if elapsed_time <= 15 and len(articles) >= 2:
    print("✅ [Tavily 단위 테스트 통과] 기사 수집 및 속도 기준 충족")
else:
    print("⚠️ [기준 미달] 소요 시간 또는 수집 건수를 확인하세요.")