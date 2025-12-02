# 🤖 Multi-Agent Architecture

## 📋 개요

이 프로젝트는 **Agent-to-Agent (A2A)** 방식의 멀티 에이전트 아키텍처를 사용하여 자동화된 콘텐츠 생성 및 포스팅 시스템을 구현합니다.

각 에이전트는 독립적인 책임을 가지고 있으며, 에이전트 체인을 통해 순차적으로 실행됩니다.

---

## 🔗 에이전트 플로우

```
auto_poster.py (진입점)
    ↓
[1단계] SearchAgent → 웹 검색 수행
    ↓
[2단계] SearchValidationAgent → 검색 결과 품질 검증
    ↓
[2-1단계] FactCheckAgent → 검색 결과 사실 확인
    ↓
[3단계] ContentGenerationAgent → 콘텐츠 생성
    ↓
[4단계] ContentValidationAgent → 콘텐츠 품질 검증
    ↓
[4-1단계] ContentRevisionAgent → 콘텐츠 수정 (문제 발견 시)
    ↓
[5단계] PostingAgent → Notion 포스팅
    ↓
Notion API → 최종 포스팅 완료
```

---

## 🛠️ 에이전트 상세 설명

### 1️⃣ SearchAgent (`agents/search_agent.py`)

**역할**: 키워드 기반 웹 검색 수행

**기능**:
- Google Custom Search API 또는 DuckDuckGo를 통한 웹 검색
- 여러 쿼리 변형으로 검색 시도 (한글, 영문, 최신 정보 등)
- 검색 결과 수집 및 반환

**입력**: `{"keyword": "키워드"}`
**출력**: `{"status": "success", "results": [...], "count": N}`

**특징**:
- Groq API를 사용하지 않음 (외부 검색 API만 사용)
- Rate limit을 피하기 위해 여러 쿼리로 시도

---

### 2️⃣ SearchValidationAgent (`agents/validation_agent.py`)

**역할**: 검색 결과의 품질 및 관련성 검증

**기능**:
- 검색 결과의 키워드 관련성 평가
- 품질 점수 계산 (0-100)
- 불필요하거나 부적절한 결과 필터링

**입력**: SearchAgent의 결과
**출력**: `{"is_valid": True/False, "validated_results": [...], "quality_score": N}`

**특징**:
- Groq API를 사용하여 LLM 기반 검증
- 관련성이 낮은 결과를 자동으로 필터링

---

### 3️⃣ FactCheckAgent (`agents/fact_check_agent.py`)

**역할**: 검색 결과의 사실 정확성 검증

**기능**:
- 통계, 숫자, 정의의 정확성 확인
- 출처의 신뢰성 평가 (공식 문서 > 학술 자료 > 뉴스 > 블로그)
- 정보의 일관성 및 최신성 확인
- 문제가 있는 결과 필터링

**입력**: SearchAgent의 결과
**출력**: `{"status": "validated"/"needs_review", "filtered_results": [...], "issues": [...], "accuracy_score": N}`

**특징**:
- 공식 문서와 논문을 우선 참고
- 문제가 있는 결과는 제거하고 이슈 리스트 반환

---

### 4️⃣ ContentGenerationAgent (`agents/content_agent.py`)

**역할**: 검증된 검색 결과를 기반으로 블로그 콘텐츠 생성

**기능**:
- 이전 포스팅 분석을 통한 자기 학습 (자연스러움 개선)
- 한글 모드: 영문 생성 → 한글 번역 (내용 일치 보장)
- 영문 모드: 영문 직접 생성
- AI 관점에서 키워드 연결
- 형식 검증 (서론/본론/결론 구조)

**입력**: `{"keyword": "키워드", "validated_results": [...], "language": "korean"/"english"}`
**출력**: `{"status": "success", "title": "...", "content": "...", "keywords": [...], "category": "..."}`

**특징**:
- 한글 모드: 영문 생성 후 번역 (안정적인 언어 품질)
- 영문 모드: 영문 직접 생성
- 이전 4개 포스팅과 비교하여 기계적 패턴 피하기
- 형식 자동 재생성 (검증 실패 시)

---

### 5️⃣ ContentValidationAgent (`agents/validation_agent.py`)

**역할**: 생성된 콘텐츠의 품질 및 언어 검증

**기능**:
- 언어 규칙 검증 (한글/영문 순수성)
- 콘텐츠 품질 평가 (가독성, 정확성, 전문성)
- 품질 점수 계산 (0-100)
- 검증 실패 시 이슈 리스트 반환

**입력**: `{"title": "...", "content": "...", "keyword": "...", "language": "korean"/"english"}`
**출력**: `{"is_valid": True/False, "quality_score": N, "issues": [...], "recommendation": "publish"/"reject"/"revise"}`

**특징**:
- 한글 검증: 한글 비율 70% 이상, 외국어 금지
- 영문 검증: 한글/중국어/일본어 등 절대 금지
- 언어별 다른 검증 로직 적용

---

### 6️⃣ ContentRevisionAgent (`agents/fact_check_agent.py`)

**역할**: 검증에서 발견된 문제를 수정

**기능**:
- 잘못된 정보 수정
- 언어 규칙 위반 수정 (외국어 제거 등)
- 구조 및 형식 문제 수정
- 검색 결과를 참고하여 정확한 정보로 교체

**입력**: `{"content": "...", "title": "...", "issues": [...], "search_results": [...], "language": "korean"/"english"}`
**출력**: `{"status": "revised", "revised_content": "...", "revisions": [...]}`

**특징**:
- 키워드/카테고리/출처 섹션은 유지하고 본문만 수정
- 언어별 수정 프롬프트 사용 (한글/영문)
- 수정 이력 추적

---

### 7️⃣ PostingAgent (`agents/posting_agent.py`)

**역할**: 검증된 콘텐츠를 Notion에 포스팅

**기능**:
- Notion API를 통한 페이지 생성
- 마크다운을 Notion 블록으로 변환
- 포스팅 결과 반환 (페이지 ID, URL)

**입력**: `{"title": "...", "content": "...", "parent_page_id": "...", "database_id": "..."}`
**출력**: `{"status": "success", "page_id": "...", "page_url": "..."}`

**특징**:
- Groq API를 사용하지 않음 (Notion API만 사용)
- 포스팅 실패 시 MCP 도구 사용 안내

---

### 8️⃣ KeywordInferenceAgent (`agents/keyword_inference_agent.py`)

**역할**: 이전 포스팅 기반 다음 키워드 추론

**기능**:
- 이전 학습 경로 분석
- 자연스러운 다음 학습 주제 추론
- 학습 단계 평가 (beginner/intermediate/advanced)

**입력**: `{"keyword": "현재 키워드", "previous_posts": [...], "learning_path": [...]}`
**출력**: `{"status": "success", "next_keyword": "...", "reason": "...", "learning_level": "..."}`

**특징**:
- 현재는 사용되지 않음 (커리큘럼 순서 사용)
- 향후 자동 학습 경로 생성 시 활용 가능

---

## 🔄 전체 플로우 상세

### Step-by-Step 실행 과정

```
1. auto_poster.py 시작
   ├─ 오늘 포스팅 여부 확인 (KST 7시 기준)
   ├─ 주말 체크 (토/일 포스팅 건너뛰기)
   └─ 활성 키워드 조회

2. 한글 콘텐츠 생성
   ├─ [1단계] SearchAgent
   │   └─ Google Custom Search API / DuckDuckGo 검색
   │
   ├─ [2단계] SearchValidationAgent
   │   └─ 검색 결과 품질 검증 (LLM)
   │
   ├─ [2-1단계] FactCheckAgent
   │   └─ 사실 확인 및 필터링 (LLM)
   │
   ├─ [3단계] ContentGenerationAgent
   │   ├─ 이전 포스팅 분석 (자기 학습)
   │   ├─ 영문 콘텐츠 생성 (LLM)
   │   └─ 한글 번역 (LLM)
   │
   ├─ [4단계] ContentValidationAgent
   │   └─ 콘텐츠 품질 검증 (LLM)
   │
   ├─ [4-1단계] ContentRevisionAgent (문제 발견 시)
   │   └─ 콘텐츠 수정 (LLM)
   │
   └─ Notion 포스팅 (auto_poster.py에서 직접)

3. 영문 콘텐츠 생성 (동일한 플로우)

4. 다음 키워드 활성화 (커리큘럼 순서)
```

---

## 🏗️ 아키텍처 특징

### 1. **A2A (Agent-to-Agent) 패턴**
- 각 에이전트가 독립적으로 실행
- 이전 에이전트의 출력을 다음 에이전트의 입력으로 전달
- 명확한 책임 분리

### 2. **자기 학습 (Self-learning)**
- 이전 포스팅 분석을 통한 패턴 개선
- 기계적인 반복 방지
- 자연스러운 글쓰기 스타일 유지

### 3. **다중 검증 계층**
- 검색 결과 검증 → 사실 확인 → 콘텐츠 검증
- 각 단계에서 품질 점수 계산
- 문제 발견 시 자동 수정

### 4. **언어 안정성**
- 한글 모드: 영문 생성 → 번역 (내용 일치)
- 언어 규칙 엄격 검증
- 외국어 자동 제거

### 5. **API Key 순환**
- 3개의 Groq API 키 순환 사용
- Rate limit 회피
- 자동 키 전환

---

## 📊 품질 점수 시스템

각 검증 단계에서 품질 점수를 계산합니다:

- **SearchQuality**: 검색 결과의 관련성 (0-100)
- **FactAccuracy**: 사실 정확성 (0-100)
- **ContentQuality**: 콘텐츠 품질 (0-100)

최종 결과에 모든 점수가 포함됩니다.

---

## 🎯 에이전트 통신 인터페이스

모든 에이전트는 다음 형식으로 통신합니다:

**입력**: `Dict[str, Any]` (Python 딕셔너리)
**출력**: `Dict[str, Any]` (status, result 등 포함)

표준 출력 형식:
```python
{
    "status": "success" | "failed" | "error",
    "message": "...",  # 선택적
    "result": {...},   # 에이전트별 결과
    ...
}
```

