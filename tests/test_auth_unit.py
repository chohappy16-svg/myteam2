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


if __name__ == "__main__":
    unittest.main()
