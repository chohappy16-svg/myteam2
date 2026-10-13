"""
Sprint 6-5: 3대 SME 대표 도메인 E2E 자동 벤치마크 스크립트 (test_domain_benchmarks.py)

검증 도메인:
1. SHOP-101 (D2C 패션 쇼핑몰)  -> 개인화 추천 AI 도입 지시 (ROAS/호스팅 제약)
2. SAAS-202 (초기 B2B SaaS)     -> AI 보안 가이드라인 및 업무 자동화 지시 (개발인력 부족/전환율 제약)
3. LOGI-303 (스마트 풀필먼트)    -> AI 배차 최적화 및 물류비 절감 지시 (WMS 패키지/원가 절감 제약)
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

from auth import PRESET_PROFILES, generate_session_thread_id
from core.graph import app_graph


class TestSME3DomainBenchmarks(unittest.TestCase):
    def run_e2e_pipeline_for_profile(self, preset_key: str, instruction: str) -> dict:
        """단일 도메인 프로필에 대한 LangGraph E2E 파이프라인 자동 실행 및 메트릭 수집"""
        profile = PRESET_PROFILES[preset_key]
        user_id = profile["user_id"]
        thread_id = generate_session_thread_id(f"BENCH_{user_id}")
        config = {"configurable": {"thread_id": thread_id}}

        # app.py와 동일한 SME 자사 맥락 합성 로직
        enriched_query = f"""[소속 기업: {profile['company']} | 사업 영역: {profile['domain_bm']}]
[인프라/리소스 제약: {profile['constraints']}]
[집중 관리 KPI: {profile['kpi']}]
[실무자 지시문]: {instruction}"""

        initial_input = {
            "user_id": user_id,
            "raw_query": enriched_query,
            "company_context": {
                "company": profile["company"],
                "domain_bm": profile["domain_bm"],
                "constraints": profile["constraints"],
                "kpi": profile["kpi"],
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
            "profile": profile,
            "elapsed_sec": elapsed_sec,
            "state": final_snapshot.values
        }

    def test_benchmark_a_shopping_mall(self):
        """[벤치마크 A] D2C 패션 쇼핑몰 (SHOP-101) E2E 검증"""
        instruction = "타사 패션몰 AI 개인화 마케팅 솔루션 도입 동향 및 실제 ROAS 개선 사례 조사"
        res = self.run_e2e_pipeline_for_profile("SHOPPING", instruction)

        report = res["state"].get("final_report", "")
        anchors = res["state"].get("anchors", {})

        # 검증 기준: 런타임 에러 없이 보고서 생성 및 자사 제약/KPI 반영 확인
        self.assertTrue(len(report) > 300, "보고서 분량이 기준치(300자)에 미달합니다.")
        self.assertIn("kpi", anchors)
        self.assertIn("constraints", anchors)
        print(f"\n[BENCHMARK A: SHOP-101] 소요시간: {res['elapsed_sec']}초 | 보고서 길이: {len(report)}자")

    def test_benchmark_b_b2b_saas(self):
        """[벤치마크 B] 초기 B2B SaaS 스타트업 (SAAS-202) E2E 검증"""
        instruction = "생성형 AI 사내 도입 거버넌스 및 워크플로우 자동화 도구 도입 타당성 검토"
        res = self.run_e2e_pipeline_for_profile("SAAS", instruction)

        report = res["state"].get("final_report", "")
        anchors = res["state"].get("anchors", {})

        self.assertTrue(len(report) > 300, "보고서 분량이 기준치(300자)에 미달합니다.")
        self.assertIn("kpi", anchors)
        self.assertIn("constraints", anchors)
        print(f"\n[BENCHMARK B: SAAS-202] 소요시간: {res['elapsed_sec']}초 | 보고서 길이: {len(report)}자")

    def test_benchmark_c_smart_logistics(self):
        """[벤치마크 C] 스마트 풀필먼트 물류 (LOGI-303) E2E 검증"""
        instruction = "물류 AI 배차 자동화 및 소규모 풀필먼트 운송 원가 절감 사례 조사"
        res = self.run_e2e_pipeline_for_profile("LOGISTICS", instruction)

        report = res["state"].get("final_report", "")
        anchors = res["state"].get("anchors", {})

        self.assertTrue(len(report) > 300, "보고서 분량이 기준치(300자)에 미달합니다.")
        self.assertIn("kpi", anchors)
        self.assertIn("constraints", anchors)
        print(f"\n[BENCHMARK C: LOGI-303] 소요시간: {res['elapsed_sec']}초 | 보고서 길이: {len(report)}자")


if __name__ == "__main__":
    unittest.main()
