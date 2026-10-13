"""Tavily 검색 및 HF 필터링 래퍼 함수 모듈

지연 로딩(Lazy Loading)의 장점:
스크립트 최상단에서 pipeline(...)을 즉시 실행하지 않고 
get_hf_classifier() 안에서 처음 호출될 때 로드하도록 격리했습니다. 
덕분에 단위 테스트나 LangGraph 컴파일 시 
불필요하게 모델을 미리 로딩하느라 몇 초씩 멈춰 있는 현상을 차단합니다.

Notion 텍스트 2,000자 제한 가드:
노션 API는 단일 rich_text 블록의 글자 수가 2,000자를 넘어가면 
validation_error를 발생시킵니다. 
p[:2000] 슬라이싱 가드를 두어 긴 텍스트 입력 시에도 API가 중단되지 않도록 방어했습니다.
"""

import os
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from tavily import TavilyClient
from transformers import pipeline
from notion_client import Client

load_dotenv()

# def search_tavily(query: str, max_results: int = 5) -> List[Dict]:
#     """Tavily Search API를 사용하여 기사를 검색합니다."""
#     # TODO: Tavily 검색 로직 구현
#     return []

# def filter_pr_noise(articles: List[Dict], threshold: float = 0.5) -> List[Dict]:
#     """Hugging Face mDeBERTa-v3 모델을 활용해 홍보성 PR 노이즈를 필터링합니다."""
#     # TODO: HF Zero-Shot 필터링 로직 구현
#     return []

# ==============================================================================
# 1. Hugging Face Zero-Shot 파이프라인 (싱글톤 지연 로딩)
# ==============================================================================
_hf_classifier = None

def get_hf_classifier():
    """
    mDeBERTa 분류기를 1회만 메모리에 적재하여 재사용하는 싱글톤 함수
    """
    global _hf_classifier
    if _hf_classifier is None:
        model_name = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
        _hf_classifier = pipeline(
            "zero-shot-classification",
            model=model_name
        )
    return _hf_classifier


# ==============================================================================
# 2. Tavily 비즈니스 동향 검색 도구 (TC-1 규격)
# ==============================================================================
def search_web_articles(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Tavily Search API를 호출하여 광고/스크립트가 배제된 본문 스니펫을 수집합니다.
    
    Returns:
        List[Dict]: [{'title': str, 'url': str, 'content': str}]
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("❌ .env에 TAVILY_API_KEY가 설정되어 있지 않습니다.")

    client = TavilyClient(api_key=api_key)
    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False
        )
        
        articles = []
        for res in response.get("results", []):
            articles.append({
                "title": res.get("title", ""),
                "url": res.get("url", ""),
                "content": res.get("content", "")
            })
        return articles

    except Exception as e:
        print(f"⚠️ Tavily 검색 중 예외 발생: {e}")
        return []


# ==============================================================================
# 3. HF mDeBERTa PR 노이즈 필터링 도구 (TC-2 규격)
# ==============================================================================
def filter_pr_articles(
    articles: List[Dict[str, str]], 
    threshold: float = 0.5
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    본문 앞 100자를 슬라이싱하여 PR/광고성 기사를 배제합니다.
    
    Returns:
        Tuple[유효_팩트_리스트, 배제된_PR_리스트]
    """
    if not articles:
        return [], []

    classifier = get_hf_classifier()
    candidate_labels = ["홍보성 보도자료 및 이벤트", "실제 비즈니스 지표 및 팩트"]
    pr_label = "홍보성 보도자료 및 이벤트"

    filtered_articles = []
    dropped_articles = []

    for item in articles:
        # 지연 시간 최소화를 위한 본문 앞 100자 슬라이싱
        snippet = item.get("content", "")[:100]
        if not snippet.strip():
            dropped_articles.append(item)
            continue

        result = classifier(
            snippet,
            candidate_labels=candidate_labels,
            hypothesis_template="이 문서는 {}에 관한 내용이다."
        )

        labels = result["labels"]
        scores = result["scores"]
        pr_score = scores[labels.index(pr_label)]

        item_with_meta = dict(item)
        item_with_meta["pr_score"] = float(pr_score)

        if pr_score >= threshold:
            item_with_meta["drop_reason"] = f"PR 확신도 초과 ({pr_score:.4f} >= {threshold})"
            dropped_articles.append(item_with_meta)
        else:
            filtered_articles.append(item_with_meta)

    return filtered_articles, dropped_articles


# ==============================================================================
# 4. Notion 보고서 내보내기 도구 (TC-5.4 규격)
# ==============================================================================
def export_report_to_notion(
    title: str, 
    report_markdown: str, 
    source_urls: Optional[List[str]] = None
) -> Optional[str]:
    """
    생성된 최종 보고서를 노션 데이터베이스에 1장의 페이지로 등록하고 열람 URL을 반환합니다.
    """
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        print("⚠️ .env에 NOTION_TOKEN 또는 NOTION_DATABASE_ID가 없습니다.")
        return None

    notion = Client(auth=notion_token)

    # 1. 기본 블록 구성 (헤더 및 안내 콜아웃)
    blocks = [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": "📌 So-What Agent가 자동 생성한 비즈니스 동향 보고서입니다."}}],
                "icon": {"emoji": "🧭"}
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "보고서 요약 본문"}}]
            }
        }
    ]

    # 2. 마크다운 본문을 문단(paragraph) 블록들로 분할 적재
    paragraphs = [p.strip() for p in report_markdown.split("\n\n") if p.strip()]
    for p in paragraphs[:15]:  # 안전한 1회 블록 전송 개수 제한
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": p[:2000]}}]
            }
        })

    # 3. 출처 URL 콜아웃 추가
    if source_urls:
        url_text = "참고 출처:\n" + "\n".join([f"• {u}" for u in source_urls[:3]])
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": url_text[:2000]}}],
                "icon": {"emoji": "🔗"}
            }
        })

    try:
        new_page = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "이름": {
                    "title": [{"text": {"content": title[:100]}}]
                }
            },
            children=blocks
        )
        return new_page.get("url")
    except Exception as e:
        print(f"❌ Notion 전송 에러: {e}")
        return None