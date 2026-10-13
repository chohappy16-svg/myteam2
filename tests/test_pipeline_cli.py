"""LangGraph E2E 통합 테스트 스크립트 (test_pipeline_cli.py - TC-3, TC-4)
전체 LangGraph 워크플로우를 CLI 환경에서 모의 실행 및 단계별 검증
"""

import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리를 sys.path에 추가 (core 모듈 import 지원)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def run_pipeline_test():
    print("=" * 60)
    print("🚀 So-What Agent CLI 파이프라인 E2E 검증 시작")
    print("=" * 60)
    # TODO: E2E 파이프라인 호출 및 검증 로직 연결 (TC-3, TC-4)
    print("준비 완료: core 파이프라인 연동 대기 중")


if __name__ == "__main__":
    run_pipeline_test()
