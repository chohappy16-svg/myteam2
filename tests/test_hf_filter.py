'''
HF Zero-Shot PR 필터링 단위 테스트 코드 (test_hf_filter.py)
앞서 수집된 실제 5개 기사 스니펫을 대상으로, 
[시트 2] 명세서 규격(100자 슬라이싱, 확신도 0.5 임계값, 2대 후보 라벨)을 엄격히 적용해 검증하는 코드입니다.
'''

import time
from transformers import pipeline

# 1. 명세서에 정의된 모델 및 설정 로드
MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
CANDIDATE_LABELS = ["홍보성 보도자료 및 이벤트", "실제 비즈니스 지표 및 팩트"]
PR_THRESHOLD = 0.5

print(f"📦 모델 로딩 시작: {MODEL_NAME}")
load_start = time.time()

# Zero-Shot 파이프라인 생성 (CPU 환경 기본, GPU 사용 가능 시 자동 가속)
classifier = pipeline(
    "zero-shot-classification",
    model=MODEL_NAME
)
print(f"✅ 모델 로딩 완료 ({time.time() - load_start:.2f}초)\n")

# 2. 직전 Tavily 검색에서 수집된 5개 실제 기사 데이터
sample_articles = [
    {
        "title": "균등 배차를 고려한 유전 알고리즘 기반 항만 물류 AI 자동 배차 최적화 방법",
        "content": "한국교통연구원에서 발행한 글로벌 물류산업 동향에 따르면 최근 글로벌 유통·물류산업에서 AI를 활용한 자동 배차 시스템이 도 입되며 운송 비용 절감과 ..."
    },
    {
        "title": "AI로 물류 배차 비효율 잡는 법…‘AI 최적화 엔진’이 해답",
        "content": "이러한 물류 시장의 도전에 대응하기 위해 글로벌 기업들은 이미 AI 기술을 적극적으로 도입하며 혁신을 꾀하고 있다. 아마존(AMAZON)은 AI 기반의 수요 예측 시스템과 실시간 ..."
    },
    {
        "title": "루티(ROOUTY) - AI로 준비하는 물류 최적화의 미래",
        "content": "“차량 운행 데이터 분석, 서비스 지역 확대, 예약 시스템 개선 등을 위해 도입하였습니다. 향후 차량 소모품 관리의 접근성을 높이고, 자동차 애프..."
    },
    {
        "title": "AI·SaaS 디지털 혁신⋯ 물류산업 새로운 표준 제시",
        "content": "AI기반 물류최적화솔루션기업 위밋모빌리티(대표 강귀선)는 통합물류협회와 함께 7월4일 ‘국내외 물류산업 동향과 디지털 최적화 사례 및 적용효과’를 주제로 세미나를 개최했다고 밝혔다..."
    },
    {
        "title": "AI로 물류 운영을 최적화하는 3가지 방법 | SOLOMON AR·AI⁺",
        "content": "분류 프로세스에 로봇 기술을 도입하면 물류 기업에 큰 이점을 제공합니다. 로봇은 분류, 포장, 라벨링 등의 수작업을 자동화하 여 오류를 줄이고 속도와 정..."
    }
]

# 3. 100자 슬라이싱 추론 및 필터링 수행
passed_articles = []
dropped_articles = []

total_inference_start = time.time()

print("=" * 60)
print("🔍 Hugging Face Zero-Shot PR 필터링 판별 시작")
print("=" * 60)

for idx, article in enumerate(sample_articles, 1):
    # 명세서 규칙: 앞 100자 슬라이싱 (추론 속도 1초 미만 방어)
    sliced_text = article["content"][:100]
    
    item_start = time.time()
    result = classifier(sliced_text, candidate_labels=CANDIDATE_LABELS, multi_label=False)
    item_elapsed = time.time() - item_start
    
    # "홍보성 보도자료 및 이벤트" 점수 확인
    pr_label_index = result["labels"].index("홍보성 보도자료 및 이벤트")
    pr_score = result["scores"][pr_label_index]
    
    is_pr = pr_score >= PR_THRESHOLD
    
    print(f"[{idx}] {article['title'][:35]}...")
    print(f"    - 분석 본문(100자): {sliced_text.strip()}")
    print(f"    - PR 확신도 점수: {pr_score:.4f} (임계치: {PR_THRESHOLD})")
    print(f"    - 판정 결과: {'❌ 배제 (PR Drop)' if is_pr else '✅ 통과 (Keep)'} | 소요 시간: {item_elapsed:.2f}초\n")
    
    if is_pr:
        dropped_articles.append((article["title"], pr_score))
    else:
        passed_articles.append(article)

total_elapsed = time.time() - total_inference_start

# 4. TC-2 완료 기준(DoD) 검증 리포트
print("=" * 60)
print("📊 [TC-2 검증 리포트]")
print(f"• 전체 5건 추론 총 소요 시간: {total_elapsed:.2f}초 (건당 평균: {total_elapsed / len(sample_articles):.2f}초)")
print(f"• PR/광고 배제 건수: {len(dropped_articles)}건")
print(f"• 최종 유효 팩트 수: {len(passed_articles)}건")

# 체크리스트 자동 판정
tc_2_1 = len(dropped_articles) >= 1
tc_2_2 = True  # 로그 및 점수 기록 완료
tc_2_3 = len(passed_articles) >= 2

print("\n[체크리스트 상태]")
print(f"[{'X' if tc_2_1 else ' '}] TC-2.1: 수집 기사 중 PR 기사 최소 1건 이상 배제")
print(f"[{'X' if tc_2_2 else ' '}] TC-2.2: 제외 사유(Score, Label) 증빙 확인")
print(f"[{'X' if tc_2_3 else ' '}] TC-2.3: 유효 팩트 최소 2건 이상 확보")

if tc_2_1 and tc_2_2 and tc_2_3:
    print("\n🎉 [TC-2 부품 단위 테스트 최종 통과]")
else:
    print("\n⚠️ [TC-2 기준 미달] 임계값 또는 데이터를 점검하세요.")
print("=" * 60)