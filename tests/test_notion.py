'''
Notion 부품 단위 테스트 코드 (test_notion.py)
노션 API 호출 지연 시간을 측정하고, 샘플 SCQA 마크다운 블록이 데이터베이스에 정상 페이지로 생성되는지 단독 검증하는 스크립트입니다.
'''

import os
import time
from dotenv import load_dotenv
from notion_client import Client

# 1. 환경변수 로드
load_dotenv()
notion_token = os.getenv("NOTION_TOKEN")
database_id = os.getenv("NOTION_DATABASE_ID")

if not notion_token or not database_id:
    raise ValueError("❌ .env 파일에서 NOTION_TOKEN 또는 NOTION_DATABASE_ID를 확인하세요.")

notion = Client(auth=notion_token)

print("=" * 60)
print("🚀 Notion API 단독 전송 테스트 시작")
print("=" * 60)

start_time = time.time()

try:
    # 2. 노션 DB에 샘플 테스트 페이지 생성
    test_title = "[테스트 브리프] 물류 AI 배차 솔루션 도입 분석"
    
    new_page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "이름": {
                "title": [
                    {"text": {"content": test_title}}
                ]
            }
        },
        children=[
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "1. 상황 및 당면 과제 (SCQA)"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "• 테스트 본문: B사의 AI 배차 도입에 따른 당사 레거시 연동 비용 분석 초안입니다."}}
                    ]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "📌 So-What Agent 자동 생성 테스트 페이지"}}],
                    "icon": {"emoji": "🤖"}
                }
            }
        ]
    )

    elapsed_time = time.time() - start_time
    page_url = new_page.get("url")

    print(f"⏱️ 소요 시간: {elapsed_time:.2f}초")
    print(f"🔗 생성된 페이지 URL: {page_url}")
    print("\n✅ [Notion 단위 테스트 통과] 페이지 생성 및 URL 발급 정상 작동 (TC-5.4 기준 충족)")

except Exception as e:
    elapsed_time = time.time() - start_time
    print(f"❌ 전송 실패 ({elapsed_time:.2f}초): {e}")
    print("\n💡 점검 가이드:")
    print(" 1. 노션 데이터베이스의 제목 컬럼 이름이 'Name' 또는 'title'인지 확인")
    print(" 2. 노션 DB 우측 상단 '···' -> '연결(Connections)'에 생성한 봇이 연결되어 있는지 확인")

print("=" * 60)