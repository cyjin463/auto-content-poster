#!/usr/bin/env python3
"""
AI 학습 커리큘럼 (365개 키워드) 데이터베이스 설정 스크립트
오늘 AI 포스팅 완료, 내일부터 두 번째 키워드부터 1년 동안 자동 포스팅
"""

#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from src.core.config import load_env_file
load_env_file()

# 모듈 import
from src.core.database import Database

# 커리큘럼 데이터
CURRICULUM = {
    "⭐ AI 기초(1~30)": [
        "인공지능(AI)", "머신러닝", "딥러닝", "데이터", "모델(Model)", "알고리즘",
        "훈련(Training)", "테스트(Test)", "검증(Validation)", "오버피팅", "언더피팅",
        "일반화", "피처(Feature)", "라벨(Label)", "데이터셋", "샘플", "편향(Bias)",
        "분산(Variance)", "하이퍼파라미터", "손실함수", "정확도", "정밀도", "재현율",
        "F1 스코어", "혼동행렬", "파라미터", "에폭(Epoch)", "배치(Batch)", "확률", "통계적 추정"
    ],
    "⭐ 머신러닝(31~80)": [
        "지도학습", "비지도학습", "강화학습", "회귀", "분류", "의사결정나무",
        "랜덤포레스트", "부스팅", "그라디언트 부스팅", "XGBoost", "SVM", "KNN",
        "k-means", "PCA", "차원 축소", "군집화", "이상치 탐지", "엔트로피", "지니계수",
        "학습률", "교차검증", "그리드서치", "모델 평가", "피처 엔지니어링", "표준화",
        "정규화", "원-핫 인코딩", "Binning", "샘플링", "언더샘플링", "오버샘플링",
        "SMOTE", "선형회귀", "로지스틱회귀", "ROC 커브", "AUC", "성능 지표",
        "연관 규칙", "Apriori", "시간 시리즈", "예측 모델", "이동평균", "ARIMA",
        "리스크 모델링", "모델 해석성", "SHAP", "LIME", "피처 중요도", "모델 드리프트", "MLOps"
    ],
    "⭐ 딥러닝 기초(81~140)": [
        "뉴런", "퍼셉트론", "활성화 함수", "ReLU", "Sigmoid", "Softmax",
        "신경망(NN)", "딥 뉴럴 네트워크(DNN)", "순전파", "역전파", "손실 감소",
        "경사하강법", "최적화 알고리즘", "Adam", "SGD", "배치 정규화", "드롭아웃",
        "Convolution", "CNN", "Max pooling", "Feature map", "필터", "파라미터 공유",
        "이미지 분류", "Object Detection", "YOLO", "R-CNN", "ResNet", "Skip connection",
        "VGG", "전이학습", "Fine-tuning", "데이터 증강", "Flatten", "Fully Connected Layer",
        "Autoencoder", "VAE", "GAN", "Generator", "Discriminator", "Latent space",
        "Attention", "Encoder", "Decoder", "Transformer", "Self-attention",
        "Positional encoding", "Multi-head attention", "Layer normalization", "BERT",
        "GPT", "Embedding", "Token", "토크나이저", "Masked Language Model",
        "Next Token Prediction", "RNN", "LSTM", "GRU", "Seq2Seq"
    ],
    "⭐ 자연어처리 NLP(141~200)": [
        "텍스트 전처리", "토큰화", "스톱워드", "표제어 추출", "형태소 분석",
        "단어 임베딩", "Word2Vec", "GloVe", "TF-IDF", "문장 임베딩", "Semantic similarity",
        "챗봇", "질의응답(QA)", "요약", "번역 모델", "감성 분석",
        "Named Entity Recognition", "문장 분류", "문맥", "Zero-shot", "Few-shot",
        "Prompt", "Prompt tuning", "Instruction tuning", "Alignment", "RLHF",
        "안전성", "편향 제거", "토큰 제한", "컨텍스트 길이", "RAG", "Vector DB",
        "임베딩 검색", "LLM 파인튜닝", "LoRA", "Quantization", "하이브리드 검색",
        "온톨로지", "지식 그래프", "자연어 생성(NLG)", "문장 재구성", "문맥적 의미",
        "프롬프트 패턴", "체인 오브 쏘트", "소크래틱 프롬프트", "Tool use", "Function calling",
        "멀티모달 모델", "시각-Language 모델(VLM)", "TTS", "STT", "문장 토큰 확률",
        "hallucination", "grounding", "데이터 정합성", "문장 구조", "의미 네트워크",
        "문서 임베딩", "Retrieval", "문서 요약"
    ],
    "⭐ 데이터/엔지니어링(201~260)": [
        "데이터 파이프라인", "ETL", "데이터 전처리", "정제(cleaning)", "이상치 처리",
        "결측치 처리", "데이터 품질", "로그 데이터", "스트리밍 데이터", "빅데이터",
        "Hadoop", "Spark", "데이터 웨어하우스", "데이터 레이크", "파케(parquet)",
        "인덱스", "SQL", "NoSQL", "Redis", "캐싱", "API", "API 호출", "JSON", "CSV",
        "스키마", "데이터 카탈로그", "버전 관리", "Git", "GitHub", "CI/CD",
        "파이프라인 자동화", "Docker", "컨테이너", "Kubernetes", "배포", "추론 서버",
        "서버리스", "GPU", "TPU", "연산 최적화", "메모리 관리", "지연시간 latency",
        "Throughput", "Scale-out", "Scale-up", "로드밸런싱", "캐시 미스", "모델 서빙",
        "A/B 테스트", "Canary 배포", "모델 모니터링", "데이터 드리프트", "로그 분석",
        "백엔드", "프론트엔드", "REST API", "GraphQL", "Node.js", "Python", "Streamlit"
    ],
    "⭐ 비즈니스 & 응용 AI(261~330)": [
        "AI 전략", "AI ROI", "AI 도입 절차", "AI 윤리", "개인정보 보호",
        "데이터 보안", "AI 리스크 관리", "자동화", "RPA", "챗봇 자동화",
        "문서 자동화", "업무 프로세스 분석", "워크플로우", "지식 관리", "디지털 트윈",
        "예측 유지보수", "산업용 AI", "의료 AI", "금융 AI", "리스크 스코어링",
        "추천 시스템", "필터링", "협업 필터링", "콘텐츠 기반 추천", "개인화",
        "고객 세그먼트", "데이터 기반 마케팅", "A/B 실험", "CRM", "광고 타게팅",
        "서치 엔진", "SEO", "대규모 데이터 처리", "Fraud detection", "Price optimization",
        "수요 예측", "공급망 최적화", "물류 최적화", "AI 제품 기획", "PMF", "UX",
        "사용자 연구", "AI 활용도 분석", "KPI 설정", "AI 플랫폼", "LLMOps", "AI Product",
        "Agent", "Multi-agent system", "Tool agent", "Planning", "Reasoning",
        "Chain-of-thought", "Self-reflection", "Debate", "Memory", "Agent 평가",
        "Agent 자동화", "AI 컴패니언", "AI 코치", "AI 튜터", "생산성 향상",
        "업무 자동화 프롬프트", "데이터 활용 전략", "사용자 흐름", "AI 기반 분석",
        "인사이트 도출", "실험 설계", "AI 윤리 가이드", "AI 책임성"
    ],
    "⭐ 고급 개념 & 미래 기술(331~365)": [
        "초거대 모델", "Scaling law", "Sparse attention", "Mixture-of-Experts",
        "Distillation", "Alignment", "오픈웨이트 모델", "프라이버시 강화 학습",
        "차등 프라이버시", "경량화 모델", "지식 증류", "AutoML",
        "Neural Architecture Search", "신경망 압축", "Edge AI", "온디바이스 AI",
        "멀티모달 추론", "World model", "Self-supervised learning",
        "Contrastive learning", "분산 AI", "협업 AI", "시뮬레이션 학습",
        "비선형성", "불확실성 정량화", "베이지안 추론", "의사결정 모델",
        "Explainable AI", "Responsible AI", "AGI", "AI 안전 연구",
        "휴먼 인 더 루프", "모델 감시", "신뢰성", "AI의 미래"
    ]
}

# 카테고리 매핑
CATEGORY_MAP = {
    "⭐ AI 기초(1~30)": "IT/컴퓨터",
    "⭐ 머신러닝(31~80)": "IT/컴퓨터",
    "⭐ 딥러닝 기초(81~140)": "IT/컴퓨터",
    "⭐ 자연어처리 NLP(141~200)": "IT/컴퓨터",
    "⭐ 데이터/엔지니어링(201~260)": "IT/컴퓨터",
    "⭐ 비즈니스 & 응용 AI(261~330)": "IT/컴퓨터",
    "⭐ 고급 개념 & 미래 기술(331~365)": "IT/컴퓨터"
}


def setup_curriculum():
    """커리큘럼을 데이터베이스에 추가"""
    db = Database()
    
    # 데이터베이스에 순서 번호 컬럼 추가
    print("📝 데이터베이스 구조 확인 및 업데이트 중...")
    conn = db._get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE keywords ADD COLUMN sequence_number INTEGER")
        print("  ✅ sequence_number 컬럼 추가됨")
    except sqlite3.OperationalError:
        print("  ℹ️  sequence_number 컬럼 이미 존재함")
    
    conn.commit()
    conn.close()
    
    # 순서대로 키워드 추가
    all_keywords = []
    sequence = 1
    
    for category_name, keywords in CURRICULUM.items():
        category = CATEGORY_MAP.get(category_name, "IT/컴퓨터")
        for keyword in keywords:
            all_keywords.append({
                "keyword": keyword,
                "category": category,
                "sequence": sequence,
                "category_name": category_name
            })
            sequence += 1
    
    print(f"\n📚 총 {len(all_keywords)}개의 키워드를 발견했습니다.")
    print(f"   (AI는 이미 포스팅되었으므로 제외)\n")
    
    # 기존 키워드 확인 (AI는 이미 있음)
    existing_ai = db.get_keyword_by_name("인공지능(AI)")
    if not existing_ai:
        existing_ai = db.get_keyword_by_name("AI")
    
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔧 키워드 추가 중...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for kw_data in all_keywords:
        keyword = kw_data["keyword"]
        category = kw_data["category"]
        sequence = kw_data["sequence"]
        
        # AI는 이미 포스팅되었으므로 sequence만 업데이트
        if keyword in ["인공지능(AI)", "AI"]:
            existing = db.get_keyword_by_name(keyword)
            if existing:
                # sequence_number 업데이트
                conn = db._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE keywords SET sequence_number = ? WHERE id = ?",
                    (sequence, existing['id'])
                )
                conn.commit()
                conn.close()
                print(f"  ✅ [{sequence:3d}] {keyword} (기존 키워드, 순서 번호만 업데이트)")
                updated_count += 1
                skipped_count += 1
            continue
        
        # 기존 키워드 확인
        existing = db.get_keyword_by_name(keyword)
        
        if existing:
            # 기존 키워드가 있으면 순서 번호만 업데이트
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE keywords SET sequence_number = ? WHERE id = ?",
                (sequence, existing['id'])
            )
            conn.commit()
            conn.close()
            print(f"  ✅ [{sequence:3d}] {keyword} (기존, 순서만 업데이트)")
            updated_count += 1
        else:
            # 새 키워드 추가 (비활성 상태로)
            keyword_id = db.add_keyword(
                keyword=keyword,
                category=category,
                is_active=False,
                sequence_number=sequence
            )
            
            print(f"  ➕ [{sequence:3d}] {keyword} (추가됨)")
            added_count += 1
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 커리큘럼 설정 완료!")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  ➕ 새로 추가: {added_count}개")
    print(f"  🔄 기존 키워드 업데이트: {updated_count}개")
    print(f"  ⏭️  건너뜀 (AI): {skipped_count}개")
    print(f"  📊 총 키워드: {len(all_keywords)}개")
    print(f"\n💡 다음 단계:")
    print(f"   1. 두 번째 키워드 '머신러닝'을 활성화합니다.")
    print(f"   2. 매일 자동으로 다음 키워드를 활성화하는 스케줄러를 설정합니다.")
    print()


def activate_next_keyword():
    """다음 순서의 키워드를 활성화 (현재 활성 키워드 비활성화)"""
    db = Database()
    
    # 현재 활성 키워드 찾기
    active_keywords = db.get_active_keywords()
    
    if not active_keywords:
        print("⚠️  활성 키워드가 없습니다.")
        return None
    
    current_keyword = active_keywords[0]
    current_seq = None
    
    # 현재 키워드의 sequence_number 확인
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sequence_number FROM keywords WHERE id = ?",
        (current_keyword['id'],)
    )
    row = cursor.fetchone()
    if row:
        current_seq = row['sequence_number']
    conn.close()
    
    if current_seq is None:
        print(f"⚠️  '{current_keyword['keyword']}' 키워드에 순서 번호가 없습니다.")
        return None
    
    # 다음 순서 키워드 찾기
    next_seq = current_seq + 1
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, keyword FROM keywords WHERE sequence_number = ?",
        (next_seq,)
    )
    next_row = cursor.fetchone()
    conn.close()
    
    if not next_row:
        print(f"✅ 모든 키워드를 완료했습니다! (현재: {current_keyword['keyword']}, 순서: {current_seq})")
        return None
    
    next_keyword_id = next_row['id']
    next_keyword_name = next_row['keyword']
    
    # 현재 키워드 비활성화
    db.toggle_keyword(current_keyword['keyword'])
    
    # 다음 키워드 활성화
    db.toggle_keyword(next_keyword_name)
    
    print(f"🔄 키워드 전환 완료!")
    print(f"   이전: {current_keyword['keyword']} (순서: {current_seq})")
    print(f"   다음: {next_keyword_name} (순서: {next_seq})")
    
    return next_keyword_name


if __name__ == '__main__':
    import sqlite3
    
    if len(sys.argv) > 1 and sys.argv[1] == 'activate_next':
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🔄 다음 키워드 활성화")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        activate_next_keyword()
    else:
        setup_curriculum()
        
        # 두 번째 키워드 활성화
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🔄 두 번째 키워드 활성화")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        # AI 키워드 비활성화하고 머신러닝 활성화
        db = Database()
        ai_keyword = db.get_keyword_by_name("인공지능(AI)")
        if not ai_keyword:
            ai_keyword = db.get_keyword_by_name("AI")
        
        if ai_keyword:
            db.toggle_keyword(ai_keyword['keyword'])  # 비활성화
        
        # 머신러닝 활성화
        ml_keyword = db.get_keyword_by_name("머신러닝")
        if ml_keyword:
            if not ml_keyword['is_active']:
                db.toggle_keyword("머신러닝")
            print(f"✅ '{ml_keyword['keyword']}' 활성화 완료!")
        else:
            print("⚠️  '머신러닝' 키워드를 찾을 수 없습니다.")

