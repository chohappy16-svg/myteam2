"""
Sprint 6-1 단위 검증 스크립트 (test_auth_unit.py)
- SME 3대 프리셋 무결성 검증
- 사번 유효성 및 세션 격리 ID 생성기 검증 (Zero-Regression)
- AI 프로파일링 안전 폴백(Safe Fallback) 검증 (무중단 화면 복구)
"""
import unittest
from unittest.mock import patch
from auth import (
    validate_employee_id,
    generate_session_thread_id,
    analyze_company_profile,
    PRESET_PROFILES,
    DEFAULT_SME_FALLBACK,
    DEFAULT_CUSTOM_PROFILE,
)


class TestAuthSprint6(unittest.TestCase):
    def test_sme_preset_profiles_integrity(self):
        """SME 3대 맞춤형 프리셋(쇼핑몰, SaaS, 물류) 데이터 무결성 검증"""
        expected_keys = ["SHOPPING", "SAAS", "LOGISTICS"]
        for key in expected_keys:
            self.assertIn(key, PRESET_PROFILES, f"프리셋 키 '{key}'가 누락되었습니다.")
            p = PRESET_PROFILES[key]

            # 필수 비즈니스 맥락 3대 요소 필드 확인
            self.assertIn("domain_bm", p)
            self.assertIn("constraints", p)
            self.assertIn("kpi", p)

            # 세부 값 유효성 확인
            self.assertTrue(len(p["user_id"]) >= 3)
            self.assertTrue(len(p["domain_bm"]) > 5)
            self.assertTrue(len(p["constraints"]) > 5)
            self.assertTrue(len(p["kpi"]) > 5)
            self.assertTrue(p["badge_color"].startswith("#"))

    def test_employee_id_validation(self):
        """사번 규격 검증(validate_employee_id) 동작 확인 (하위 호환)"""
        # 정상 사번
        valid_samples = ["SHOP-101", "SAAS-202", "LOGI-303", "EMP-84920", "AI-001"]
        for s in valid_samples:
            is_valid, clean_id = validate_employee_id(s)
            self.assertTrue(is_valid, f"{s} 검증 실패")
            self.assertEqual(clean_id, s.upper())

        # 비정상 사번 (빈값, 특수문자 포함 등)
        self.assertFalse(validate_employee_id("")[0])
        self.assertFalse(validate_employee_id("   ")[0])
        self.assertFalse(validate_employee_id("A@B#C")[0])

    def test_thread_id_isolation_format(self):
        """세션 격리용 thread_id 포맷(thread_{user_id}_{hash}) 및 고유성 검증"""
        user_id = "SHOP-101"
        tid1 = generate_session_thread_id(user_id)
        tid2 = generate_session_thread_id(user_id)

        # 규격 확인
        self.assertTrue(tid1.startswith(f"thread_{user_id}_"))
        self.assertTrue(tid2.startswith(f"thread_{user_id}_"))

        # 8자리 고유 해시 기반 격리 확인
        self.assertEqual(len(tid1.split("_")[-1]), 8)
        self.assertNotEqual(tid1, tid2)

    def test_analyze_company_profile_safe_fallback_on_empty(self):
        """브랜드명이 비어있는 경우 안전하게 기본 폴백값을 반환하는지 검증"""
        result = analyze_company_profile("", "")
        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["domain_bm"], DEFAULT_SME_FALLBACK["domain_bm"])
        self.assertEqual(result["constraints"], DEFAULT_SME_FALLBACK["constraints"])
        self.assertEqual(result["kpi"], DEFAULT_SME_FALLBACK["kpi"])

    @patch("auth.os.getenv")
    def test_analyze_company_profile_safe_fallback_on_api_error(self, mock_getenv):
        """API 키가 없거나 외부 통신 에러 발생 시 예외 발생 없이 표준 SME 템플릿으로 안전 복구되는지 검증"""
        mock_getenv.return_value = None  # API 키 없는 환경 모사

        # 어떤 예외도 상위로 전파되지 않고 정상 딕셔너리를 반환해야 함
        result = analyze_company_profile("테스트스타트업", "https://test.com")
        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["domain_bm"], DEFAULT_SME_FALLBACK["domain_bm"])
        self.assertEqual(result["constraints"], DEFAULT_SME_FALLBACK["constraints"])
        self.assertEqual(result["kpi"], DEFAULT_SME_FALLBACK["kpi"])

    def test_detect_ecommerce_platform_smartstore(self):
        """네이버 스마트스토어 감지 및 브랜드명 선택 기입(유/무) 검증"""
        from auth import detect_ecommerce_platform

        # 1. 브랜드명 기입한 경우
        res1 = detect_ecommerce_platform("https://smartstore.naver.com/yogastore", "요가천국")
        self.assertEqual(res1["platform_type"], "NAVER_SMARTSTORE")
        self.assertEqual(res1["brand_name"], "요가천국")
        self.assertTrue(validate_employee_id(res1["user_id"])[0])

        # 2. 브랜드명 비워둔 경우 (URL에서 스토어 ID 자동 추출)
        res2 = detect_ecommerce_platform("https://smartstore.naver.com/yogastore", "")
        self.assertEqual(res2["platform_type"], "NAVER_SMARTSTORE")
        self.assertEqual(res2["brand_name"], "스토어(YOGASTORE)")
        self.assertTrue(validate_employee_id(res2["user_id"])[0])

    def test_detect_ecommerce_platform_coupang(self):
        """쿠팡 마켓플레이스 감지 및 브랜드명 선택 기입(유/무) 검증"""
        from auth import detect_ecommerce_platform

        # 1. 브랜드명 기입한 경우
        res1 = detect_ecommerce_platform("https://www.coupang.com/vp/products/123", "로켓셀러A")
        self.assertEqual(res1["platform_type"], "COUPANG")
        self.assertEqual(res1["brand_name"], "로켓셀러A")
        self.assertTrue(validate_employee_id(res1["user_id"])[0])

        # 2. 브랜드명 비워둔 경우 (안전 폴백 상호 지정)
        res2 = detect_ecommerce_platform("https://www.coupang.com/vp/products/123", "")
        self.assertEqual(res2["platform_type"], "COUPANG")
        self.assertEqual(res2["brand_name"], "쿠팡 파트너몰")
        self.assertTrue(validate_employee_id(res2["user_id"])[0])

    def test_detect_ecommerce_platform_d2c(self):
        """일반 독립 D2C 자사몰 감지 및 도메인 기반 상호 추출 검증"""
        from auth import detect_ecommerce_platform

        # 1. 브랜드명 기입한 경우
        res1 = detect_ecommerce_platform("https://www.xexymix.com", "젝시믹스")
        self.assertEqual(res1["platform_type"], "GENERAL_D2C")
        self.assertEqual(res1["brand_name"], "젝시믹스")
        self.assertTrue(validate_employee_id(res1["user_id"])[0])

        # 2. 브랜드명 비워둔 경우 (도메인 호스트에서 상호 자동 추출)
        res2 = detect_ecommerce_platform("https://www.xexymix.com", "")
        self.assertEqual(res2["platform_type"], "GENERAL_D2C")
        self.assertEqual(res2["brand_name"], "XEXYMIX")
        self.assertTrue(validate_employee_id(res2["user_id"])[0])

    def test_diagnose_ecommerce_report_type(self):
        """이커머스 4대 표준 보고서 자동 진단기 검증 (Sprint 6-2)"""
        from auth import diagnose_ecommerce_report_type

        # 1. CVR 상세페이지 전환율
        r_cvr = diagnose_ecommerce_report_type("레깅스 상세페이지 후기 배치 및 구매 전환율 개선")
        self.assertEqual(r_cvr["type_key"], "CVR")
        self.assertEqual(r_cvr["title"], "상세페이지 구매 전환율(CVR) 극대화 전략 보고서")

        # 2. AOV 객단가 번들 세트
        r_aov = diagnose_ecommerce_report_type("추석 선물세트 묶음 판매 및 객단가 상승 프로모션")
        self.assertEqual(r_aov["type_key"], "AOV")
        self.assertEqual(r_aov["title"], "객단가(AOV) 상승을 위한 번들 및 세트 구성 전략 보고서")

        # 3. ROAS 광고 효율
        r_roas = diagnose_ecommerce_report_type("메타 인스타 피드 광고 소재별 ROAS 성과 분석")
        self.assertEqual(r_roas["type_key"], "ROAS")
        self.assertEqual(r_roas["title"], "소재별 광고 효율(ROAS) 최적화 전략 보고서")

        # 4. CRM 리텐션 재구매
        r_crm = diagnose_ecommerce_report_type("첫구매 유저 카카오 알림톡 발송 및 재구매 쿠폰 설계")
        self.assertEqual(r_crm["type_key"], "CRM")
        self.assertEqual(r_crm["title"], "첫 구매 고객 재구매 유도(CRM/리텐션) 전략 보고서")

        # 5. 폴백 (모호한 지시문)
        r_fallback = diagnose_ecommerce_report_type("요즘 장사가 잘 안 되는데 어쩌지?")
        self.assertEqual(r_fallback["type_key"], "CVR")


if __name__ == "__main__":
    unittest.main()
