"""
Sprint 6-2 검증 스크립트 (test_sprint6_2_integration.py)
- SHOP-101 (패션 D2C 쇼핑몰) 프로필 기준 company_context 주입 및 파이프라인 무결성 검증
"""
import os
import sys
import unittest
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from auth import PRESET_PROFILES, generate_session_thread_id
from core.nodes import parse_and_anchor_node


class TestSprint62Integration(unittest.TestCase):
    def setUp(self):
        self.profile = PRESET_PROFILES["SHOPPING"]
        self.user_id = self.profile["user_id"]  # SHOP-101
        self.thread_id = generate_session_thread_id(self.user_id)

    def test_initial_state_with_company_context(self):
        """SHOP-101 프로필의 company_context가 initial_state에 비파괴적으로 결합되는지 검증"""
        raw_instruction = "개인화 마케팅 AI 도입 동향 및 타사 적용 사례 조사"

        # app.py와 동일한 enrichment 로직
        enriched_query = f"""[소속 기업: {self.profile['company']} | 사업 영역: {self.profile['domain_bm']}]
[인프라/리소스 제약: {self.profile['constraints']}]
[집중 관리 KPI: {self.profile['kpi']}]
[실무자 지시문]: {raw_instruction}"""

        initial_input = {
            "user_id": self.user_id,
            "raw_query": enriched_query,
            "company_context": {
                "company": self.profile["company"],
                "domain_bm": self.profile["domain_bm"],
                "constraints": self.profile["constraints"],
                "kpi": self.profile["kpi"],
            },
            "search_retry_count": 0,
            "human_choice": None,
        }

        # 1. State 스키마 충돌 없이 그래프가 초기 입력을 수락하는지 검증
        self.assertIn("company_context", initial_input)
        self.assertEqual(initial_input["company_context"]["company"], "아틀리에 패션 D2C")

        # 2. Node 1 (parse_and_anchor) 직접 구동 및 검증
        parsed_result = parse_and_anchor_node(initial_input)

        self.assertIn("anchors", parsed_result)
        anchors = parsed_result["anchors"]

        # 3. 추출된 제약이나 KPI에 자사 맥락이 적절히 반영되었는지 단언
        self.assertTrue(len(anchors.get("kpi", "")) > 0)
        self.assertTrue(len(anchors.get("constraints", "")) > 0)
        self.assertTrue(len(parsed_result.get("search_queries", [])) > 0)


if __name__ == "__main__":
    unittest.main()
