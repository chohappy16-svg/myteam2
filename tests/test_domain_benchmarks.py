"""
Sprint 6-5: B2C 이커머스 3대 대표 도메인 E2E 자동 벤치마크 스크립트 (test_domain_benchmarks.py)
[시트 6] B2C 쇼핑몰 마케팅 특화 상용 배포 기준 검증

3대 이커머스 도메인:
1. [패션/애슬레저 D2C] 젝시믹스 자사몰 -> 요가 레깅스 상세페이지 구매 전환율(CVR) 극대화
2. [뷰티/스킨케어 스마트스토어] 네이버 스마트스토어 -> 비건 선크림 객단가(AOV) 상승 세트 번들 구성
3. [건기식/식품 쿠팡 로켓] 쿠팡 파트너몰 -> 단백질 보충제 광고 효율(ROAS) 최적화 및 벤치마크
"""
import os
import sys
import time
import unittest
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from auth import (
    detect_ecommerce_platform,
    diagnose_ecommerce_report_type,
    generate_session_thread_id,
    PRESET_PROFILES,
)
from core.graph import app_graph


class TestECommerce3DomainBenchmarks(unittest.TestCase):
    def run_e2e_ecommerce_pipeline(self, url: str, brand: str, query: str) -> dict:
        """이커머스 URL 및 지시문을 기반으로 E2E LangGraph 파이프라인 실행 및 검증"""
        # 1. Sprint 6-1: 플랫폼 감지 및 프로파일 생성
        meta = detect_ecommerce_platform(url=url, user_brand=brand)
        thread_id = generate_session_thread_id(f"ECOM_{meta['user_id']}")
        config = {"configurable": {"thread_id": thread_id}}

        # 2. Sprint 6-2: 4대 표준 보고서 자동 진단
        diagnosed = diagnose_ecommerce_report_type(query, meta["brand_name"])

        enriched_query = f"""[소속 기업: {meta['brand_name']} | 플랫폼: {meta['platform_name']}]
[진단 보고서 유형: {diagnosed['title']}]
[플랫폼 제약: {meta['constraints']}]
[목표 KPI: {meta['kpi']}]
[실무자 지시문]: {query}"""

        initial_input = {
            "user_id": meta["user_id"],
            "raw_query": enriched_query,
            "company_context": {
                "company": meta["brand_name"],
                "domain_bm": meta["platform_name"],
                "constraints": meta["constraints"],
                "kpi": meta["kpi"],
                "diagnosed_report_title": diagnosed["title"]
            },
            "search_retry_count": 0,
            "human_choice": None,
        }

        start_time = time.time()

        # Step 1: START -> Node 1, 2, 3 -> interrupt_before=["human_gate"]
        for _ in app_graph.stream(initial_input, config=config):
            pass

        gate_snapshot = app_graph.get_state(config)
        self.assertIn("outline", gate_snapshot.values, "HITL 게이트 직전 목차가 생성되지 않았습니다.")
        self.assertEqual(len(gate_snapshot.values["outline"]), 3, "목차는 정확히 3개여야 합니다.")

        # Step 2: HITL Gate 승인 (Approve) 주입
        app_graph.update_state(
            config,
            {"human_choice": "approve"},
            as_node="human_gate"
        )

        # Step 3: Node 4 (Draft Final Report) -> END
        for _ in app_graph.stream(None, config=config):
            pass

        final_snapshot = app_graph.get_state(config)
        elapsed_sec = round(time.time() - start_time, 2)

        return {
            "meta": meta,
            "diagnosed": diagnosed,
            "elapsed_sec": elapsed_sec,
            "state": final_snapshot.values
        }

    def test_benchmark_a_fashion_d2c(self):
        """[벤치마크 1] 패션 D2C 자사몰: 젝시믹스 요가 레깅스 CVR 개선 전략"""
        url = "https://www.xexymix.com"
        brand = "젝시믹스"
        query = "여성 요가 레깅스 자사몰 상세페이지 후기 배치 및 구매 전환율(CVR) 극대화 전략"

        res = self.run_e2e_ecommerce_pipeline(url, brand, query)
        report = res["state"].get("final_report", "")

        self.assertEqual(res["diagnosed"]["type_key"], "CVR")
        self.assertTrue(len(report) > 300, "보고서 분량이 기준치(300자)에 미달합니다.")
        self.assertIn("|", report, "타사 벤치마크 마크다운 비교 표가 누락되었습니다.")
        print(f"\n[BENCHMARK 1: 패션 D2C ({brand})] 소요시간: {res['elapsed_sec']}초 | 보고서 길이: {len(report)}자")

    def test_benchmark_b_beauty_smartstore(self):
        """[벤치마크 2] 네이버 스마트스토어: 비건 선크림 객단가(AOV) 세트 번들 구성 전략"""
        url = "https://smartstore.naver.com/purebeauty"
        brand = ""  # 브랜드명 미입력 테스트 (스토어 ID 자동 추출)
        query = "여름 시즌 비건 선크림 묶음 세트 및 사은품 프로모션으로 객단가(AOV) 상승 방안"

        res = self.run_e2e_ecommerce_pipeline(url, brand, query)
        report = res["state"].get("final_report", "")

        self.assertEqual(res["diagnosed"]["type_key"], "AOV")
        self.assertTrue(len(report) > 300, "보고서 분량이 기준치(300자)에 미달합니다.")
        self.assertIn("|", report, "타사 벤치마크 마크다운 비교 표가 누락되었습니다.")
        print(f"\n[BENCHMARK 2: 스마트스토어 ({res['meta']['brand_name']})] 소요시간: {res['elapsed_sec']}초 | 보고서 길이: {len(report)}자")

    def test_benchmark_c_food_coupang(self):
        """[벤치마크 3] 쿠팡 로켓그로스: 단백질 보충제 광고 효율(ROAS) 최적화 전략"""
        url = "https://www.coupang.com/vp/products/protein123"
        brand = "프로틴랩"
        query = "단백질 쉐이크 타사 광고 소재별 성과 분석 및 메타 광고 ROAS 최적화 방안"

        res = self.run_e2e_ecommerce_pipeline(url, brand, query)
        report = res["state"].get("final_report", "")

        self.assertEqual(res["diagnosed"]["type_key"], "ROAS")
        self.assertTrue(len(report) > 300, "보고서 분량이 기준치(300자)에 미달합니다.")
        self.assertIn("|", report, "타사 벤치마크 마크다운 비교 표가 누락되었습니다.")
        print(f"\n[BENCHMARK 3: 쿠팡 ({brand})] 소요시간: {res['elapsed_sec']}초 | 보고서 길이: {len(report)}자")


if __name__ == "__main__":
    unittest.main()
