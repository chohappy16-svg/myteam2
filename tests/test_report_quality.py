"""
Sprint 6-4 검증 스크립트 (test_report_quality.py)
- 고밀도 1장 전략 브리프 출력 품질 및 형식 검증
1. 변명성 문장("인력 부족", "외부 솔루션 의존" 등) 0건 검증
2. 타사 벤치마크 마크다운 비교 표(| ... |) 규격 검증
3. 4단 구조(💡 결론 -> [1] 병목 -> [2] 벤치마크 표 -> [3] 액션 플랜) 준수 검증
4. Dual-Rendering 무결성(순수 마크다운에 HTML 태그 미오염) 검증
"""
import unittest
from core.nodes import draft_report_node


class TestReportQualitySprint6_4(unittest.TestCase):
    def test_draft_report_quality_and_structure(self):
        """Node 4의 최종 보고서가 고밀도 1장 규격 및 비교 표를 충족하는지 검증"""
        sample_state = {
            "anchors": {
                "kpi": "상세페이지 구매 전환율(CVR) 극대화 및 광고 ROAS 개선",
                "stakeholder": "수치와 즉각적 매출 전환을 최우선하는 대표",
                "constraints": "단기 1~2주 내 즉각 실행 가능한 자사몰 CVR 최적화 및 프로모션 중심",
                "angle": "상세페이지 CVR 전환 중심"
            },
            "hypothesis": "경쟁사 벤치마크 분석 결과, 후기 최상단 재배치와 묶음 할인 옵션을 도입하면 상세페이지 CVR을 30% 이상 개선할 수 있다.",
            "outline": [
                "여성 레깅스 상세페이지 이탈 원인 및 리뷰 가시성 부재 분석",
                "안다르 및 젝시믹스 등 타사 CVR 최적화 및 리뷰 프로모션 사례",
                "자사몰 즉시 적용 3대 액션 플랜 및 주간 실행 일정"
            ],
            "filtered_articles": [
                {
                    "title": "젝시믹스, 자사몰 리뷰 개편으로 CVR 35% 급증",
                    "url": "https://example.com/xexymix-cvr",
                    "content": "애슬레저 브랜드 젝시믹스는 상세페이지 첫 화면에 실착 포토리뷰를 배치하고 1+1 번들 할인을 제공하여 구매 전환율(CVR)을 35% 상승시켰다."
                },
                {
                    "title": "D2C 패션몰 상세페이지 CVR 최적화 성공 공식",
                    "url": "https://example.com/d2c-cvr",
                    "content": "상세페이지 상단 3초 이내에 핵심 소구점과 누적 판매량 배지를 노출한 브랜드들의 평균 이탈률이 40% 감소했다."
                }
            ]
        }

        result = draft_report_node(sample_state)
        report = result.get("final_report", "")

        # 1. 보고서 길이 및 생성 여부 확인
        self.assertTrue(len(report) > 300, "보고서가 너무 짧거나 생성되지 않았습니다.")

        # 2. 4단 구조 키워드 포함 확인
        self.assertIn("핵심 결론", report, "핵심 결론(Hypothesis) 섹션이 누락되었습니다.")
        self.assertIn("[1]", report, "[1] 병목/현상황 섹션이 누락되었습니다.")
        self.assertIn("[2]", report, "[2] 타사 벤치마크 섹션이 누락되었습니다.")
        self.assertIn("[3]", report, "[3] 즉시 실행 권고안(Action Plan) 섹션이 누락되었습니다.")

        # 3. 마크다운 비교 표 검증 (파이프 '|' 구분자 및 표 헤더)
        self.assertIn("|", report, "타사 벤치마크 비교 표가 마크다운 테이블 형태로 생성되지 않았습니다.")
        self.assertTrue(
            "구분" in report or "브랜드" in report or "전략" in report or "성과" in report,
            "마크다운 비교 표 헤더가 누락되었습니다."
        )

        # 4. 변명성/패배주의 문장 절대 금지 검증
        banned_phrases = ["인력 부족", "개발 인력", "외부 솔루션 의존", "인프라 한계로", "어쩔 수 없"]
        for phrase in banned_phrases:
            self.assertNotIn(phrase, report, f"금지된 변명성 문장 '{phrase}'이 보고서에 포함되었습니다!")

        # 5. Dual-Rendering 원칙: 원본 마크다운에 Streamlit/HTML 태그 미오염 확인
        self.assertNotIn("<div", report, "Notion 전송용 원본 마크다운에 HTML 태그(<div>)가 오염되었습니다.")
        self.assertNotIn("<style", report, "Notion 전송용 원본 마크다운에 <style> 태그가 오염되었습니다.")


if __name__ == "__main__":
    unittest.main()
