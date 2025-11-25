"""
콘텐츠 생성 에이전트: 검증된 검색 결과 기반 콘텐츠 생성
"""

from typing import Dict, Any
from agents.base import BaseAgent
import json
import sys
import os

# utils 모듈 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import validate_korean_content


class ContentGenerationAgent(BaseAgent):
    """콘텐츠 생성 에이전트"""
    
    def __init__(self):
        super().__init__("콘텐츠 생성 에이전트")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """콘텐츠 생성"""
        keyword = input_data["keyword"]
        validated_results = input_data["validated_results"]
        language = input_data.get("language", "korean")  # 기본값: 한글
        learning_story = input_data.get("learning_story", True)  # 기본값: 학습 스토리 형식
        
        print(f"  🤖 [{self.name}] 콘텐츠 생성 중... ({'한글' if language == 'korean' else '영문'}, {'학습 스토리' if learning_story else '일반'})")
        
        # 검색 결과 요약
        search_summary = "\n".join([
            f"{i+1}. {r['title']}\n   {r['snippet']}\n   출처: {r['link']}"
            for i, r in enumerate(validated_results)
        ])
        
        if language == 'english':
                prompt = f"""Write a professional and useful blog post about "{keyword}" based on the following search results.

Search Results:
{search_summary}

⚠️ **Language Requirements**:
- Write **only in English**. Do not use any other languages.
- Do not use Chinese characters (Hanja) or any non-English scripts.
- Write in natural, professional English only.

Requirements:
1. Title: Attractive and SEO-friendly title (in English only)
2. Content: Detailed content of at least 1000 characters (in English only)
3. Use the search results as reference, but don't copy them directly - reorganize
4. Write in natural, professional English
5. Use appropriate subheadings and paragraph breaks
6. Technical terms should be clearly explained

Please respond in the following JSON format:
{{
  "title": "Title (in English only)",
  "content": "Content (markdown format, in English only)",
  "summary": "Summary (within 200 characters, in English only)",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
  "category": "Tistory category (e.g., IT/Computer, Hobby/Life, Economy/Business, Current Events, Education, Arts/Culture, etc.)"
}}

**keywords field**: Provide 5-10 related keywords for this post in an array format. These are SEO-related keywords.
**category field**: Select one Tistory category that this post belongs to. (e.g., IT/Computer, Hobby/Life, Economy/Business, Current Events, Education, Arts/Culture, etc.)"""
                system_prompt = "You are a professional blog writer. Analyze search results and write original and useful content. ⚠️ Write **only in English**. Do not use any other languages including Chinese characters (Hanja) or Korean. Write in a natural, friendly tone that is professional but not too formal."
        else:
            # 학습 스토리 형식 여부에 따라 프롬프트 분기
            if learning_story:
                prompt = f"""다음 검색 결과를 기반으로 "{keyword}"에 대한 **학습 스토리 형식**의 블로그 포스트를 작성해주세요.

**중요**: 이 글은 초보자가 "{keyword}"에 대해 처음 접하고, 하나씩 알아가며 이해하게 되는 과정을 스토리로 풀어낸 것입니다.

검색 결과:
{search_summary}

⚠️ **언어 작성 규칙 (엄격히 준수)**:
- **한글 위주로 작성**: 본문은 한글로 작성합니다.
- **한자 절대 사용 금지**: 한자는 전혀 사용하지 마세요. (예: 非常 ❌ → 매우 ✅)
- **일본어, 베트남어 등 외국어 문자 절대 사용 금지**: まだ, khá 같은 외국어 문자 사용 금지
- **영어 사용**: 다음 경우에만 영어 사용 가능
  * 기술 용어나 축약어를 설명할 때: 예) "AI(인공지능)", "API", "GPU"
  * 영어 원문을 그대로 사용하는 것이 더 이해하기 쉬울 때: 예) "Machine Learning(머신러닝)"
  * 축약어나 고유명사를 사용할 때: 예) "OpenAI", "Python"
- **설명 필요시**: 영어 사용 시 괄호 안에 한글 설명을 함께 제공하세요.

**블로그 글 작성 형식 (실제 블로그들의 베스트 프랙티스 학습 결과 반영)**:

⚠️ **중요**: 본문에 제목을 다시 적지 마세요. 제목은 JSON의 "title" 필드에만 작성하고, 본문은 서론부터 시작하세요.

## 서론 (Introduction) - 2-3단락 (각 문단 사이 빈 줄 필수)

실제 IT 기술 블로그들의 서론 패턴:

1. **주제 도입 문단** (3-4문장): 간략한 배경 설명
2. **[빈 줄]** 
3. **동기 문단** (2-3문장): 글을 쓰게 된 개인적인 경험이나 계기
4. **[빈 줄]**
5. **독자 안내 문단** (2-3문장): 이 글에서 무엇을 배울 수 있는지

⚠️ **중요**: 각 문단 사이에 반드시 빈 줄(줄바꿈)을 넣어야 합니다!

예시 구조:
```
처음에는 {keyword}가 뭔지 잘 몰랐어요. [배경 설명 2-3문장으로 구성]

최근 들어 {keyword} 이야기를 자주 접하게 되어, 직접 알아보기로 했습니다. [동기 설명 2-3문장]

이 글에서는 {keyword}에 대해 초보자의 시각에서 하나씩 알아가는 과정을 공유합니다. [독자 안내 2-3문장]
```

## 본론 (Body) - 체계적인 목차와 단계별 설명
실제 블로그들의 본론 구성 패턴:
- **명확한 목차 구조**: 소제목으로 섹션을 명확히 구분
- **단계별 설명**: 복잡한 내용을 쉽게 이해할 수 있도록 단계별로 설명
- **구체적인 예시**: 추상적인 설명보다는 실제 사례나 예시 제공
- **시각적 요소 고려**: 리스트, 번호 매기기 등을 활용하여 가독성 향상

본론 소제목 구조 (순서대로, 각 섹션 사이 빈 줄 필수):

### 1. {keyword}란 무엇인가?

[소제목 다음 반드시 빈 줄 하나]

**문단 1** (3-4문장): 정의와 핵심 개념 설명

[빈 줄]

**문단 2** (3-4문장): 독자가 이해하기 쉽도록 간단한 예시 제공

[빈 줄]

**문단 3** (2-3문장): 개인적인 깨달음이나 감상

[빈 줄]

### 2. {keyword}의 특징과 원리

[소제목 다음 반드시 빈 줄 하나]

**핵심 특징** (마크다운 리스트 필수):
1. 첫 번째 특징 설명 (2-3문장)
2. 두 번째 특징 설명 (2-3문장)
3. 세 번째 특징 설명 (2-3문장)
4. 네 번째 특징 설명 (2-3문장)

[빈 줄]

**원리 설명 문단** (3-4문장): 왜 중요한지, 어떤 의미가 있는지, 실제 작동 원리를 쉽게 설명

[빈 줄]

### 3. {keyword} 기술과 활용 사례

[소제목 다음 반드시 빈 줄 하나]

**핵심 기술** (마크다운 리스트 필수):
1. 첫 번째 기술: 설명 (2-3문장)
2. 두 번째 기술: 설명 (2-3문장)
3. 세 번째 기술: 설명 (2-3문장)

[빈 줄]

**활용 사례** (마크다운 리스트 필수):
1. **의료 분야**: 사례 설명 (2-3문장)
2. **금융 분야**: 사례 설명 (2-3문장)
3. **제조 분야**: 사례 설명 (2-3문장)

[빈 줄]

### 4. 나의 경험/느낀 점

[소제목 다음 반드시 빈 줄 하나]

**문단 1** (3-4문장): 공부하면서 느낀 점, 깨달은 점

[빈 줄]

**문단 2** (2-3문장): 독자에게 공감대를 줄 수 있는 이야기

[빈 줄]

**문단 3** (2-3문장): 앞으로 더 배우고 싶은 방향

⚠️ **작성 원칙** (가독성 최우선):
- **문단 구분**: 각 문단은 3-4문장으로 구성하고, 문단 사이에 빈 줄(줄바꿈) 필수
- **소제목 아래**: 소제목 다음에는 반드시 빈 줄 하나 추가 후 본문 시작
- **리스트 활용**: 특징, 사례, 원리 등은 반드시 마크다운 리스트(1., 2., 3. 또는 -, -, -) 형식 사용
- **줄바꿈**: 긴 문장은 적절히 줄바꿈하여 읽기 쉽게 구성
- **구체적 예시**: 추상적 설명보다 구체적인 예시를 리스트나 별도 문단으로 제시
- **티스토리 최적화**: 티스토리에 올릴 예정이므로 마크다운 포맷팅을 명확히 적용

⚠️ **마크다운 포맷팅 규칙** (티스토리 호환):
- 소제목: `## 제목` 다음에 반드시 빈 줄
- 문단 구분: 문단 사이마다 빈 줄 하나씩 추가
- 리스트: `1.` 또는 `-` 다음 한 칸 띄우고 내용 작성
- 강조: 중요한 키워드는 `**굵게**` 처리
- 줄바꿈: 문장이 길면 2-3문장마다 줄바꿈 고려

## 결론 (Conclusion) - 핵심 요약과 메시지 (각 문단 사이 빈 줄 필수)

실제 블로그들의 결론 패턴:

**문단 1** (3-4문장): 핵심 요약 - 글에서 다룬 주요 내용을 요약

[빈 줄]

**문단 2** (2-3문장): 개인적 소감 - 배운 점이나 느낀 점

[빈 줄]

**문단 3** (2-3문장): 독자에게 전하는 메시지 - 앞으로의 계획이나 독자에게 권하는 내용

⚠️ **중요**: 결론도 각 문단 사이에 반드시 빈 줄을 넣어야 합니다!

**기타 요구사항** (실제 블로그들의 베스트 프랙티스 학습 결과 반영):
1. **제목**: 학습 스토리 형식의 매력적인 제목
   - 독자의 호기심을 자극하는 질문형이나 경험담형
   - 예: "{keyword}, 처음에는 몰랐지만 이제 이해하게 된 이야기"

2. **본문 길이**: 최소 1500자 이상, 권장 2000-2500자
   - 서론: 200-300자
   - 본론: 1200-1800자 (각 소제목당 300-450자)
   - 결론: 200-300자

3. **작성 스타일** (실제 블로그들의 베스트 프랙티스):
   - **자연스러운 문장 흐름**: 정형적인 "~입니다", "~합니다" 남발 금지. 다양한 문장 패턴 사용 (단문, 중문, 복문 조화)
   - **개인 경험과 주관적 표현**: "처음에는 ~라고 생각했는데", "실제로 해보니 ~", "개인적으로는 ~" 같은 표현 포함
   - **감정과 느낌 표현**: "생각보다 어려웠어요", "재미있게 느껴졌어요", "이해가 안 갔어요" 등 구체적 감정 표현
   - **중복 제거**: 같은 의미 반복 금지, 핵심만 간결하게 전달
   - **AI 티 제거**: "김AI" 같은 표시 절대 사용 금지. 마치 사람이 직접 작성한 것처럼 자연스럽게
   - **명확성**: 전문 용어를 최소화하고, 독자가 쉽게 이해할 수 있도록 설명
   - **일관성**: 문체와 톤을 일관되게 유지
   - **구체성**: 추상적 설명보다 구체적인 예시와 사례 제공
   - **가독성**: 리스트, 번호 매기기, 적절한 문단 구분 활용

4. **말투 규칙** (자연스러운 인간의 글):
   - 정형적인 AI 문장 절대 금지 ("~입니다", "~합니다" 남발 금지)
   - 다양한 문장 패턴 사용 (단문, 중문, 복문 조화)
   - 개인 경험과 주관적 표현 포함 ("처음에는 ~라고 생각했는데", "실제로는 ~")
   - 감정과 느낌 표현 ("생각보다 어려웠어요", "재미있게 느껴졌어요")
   - 중복 및 불필요한 문장 제거 (핵심만 간결하게)
   - "김AI" 같은 표시 절대 사용 금지 (자연스럽게 읽히도록)

5. **작성 형식 체크리스트** (티스토리 가독성 필수):
   - ✅ 서론: 배경 → 동기 → 독자 안내 (2-3단락, 각 문단 사이 빈 줄 필수)
   - ✅ 본론: 4개 소제목 순서대로 (정의 → 특징 → 활용 → 경험)
   - ✅ 결론: 요약 → 소감 → 메시지 (각 문단 사이 빈 줄 필수)
   - ✅ 본문에 제목 포함하지 않기
   - ✅ 각 소제목마다 2-4문단, 각 문단 3-4문장
   - ✅ **모든 문단 사이 빈 줄(줄바꿈) 필수** - 뭉텅이로 작성하지 않기
   - ✅ 리스트는 반드시 마크다운 형식(`1.`, `-`) 사용
   - ✅ 구체적인 예시와 사례 포함
   - ✅ 중복 문장 제거 (같은 의미 반복 금지)
   - ✅ 불필요한 수식어 최소화 (핵심만 전달)

6. **검색 결과 활용**:
   - 검색 결과의 정보를 참고하되, 원본을 그대로 복사하지 말고 재구성
   - 여러 검색 결과를 종합하여 일관된 스토리로 재구성
   - 검색 결과의 내용을 학습 과정에 자연스럽게 녹여내기

⚠️ **마크다운 포맷팅 필수 사항** (티스토리 가독성 최우선, 반드시 준수):

**절대 하지 말 것**:
- ❌ 문단을 뭉텅이로 연속해서 작성하지 마세요
- ❌ 소제목 다음 바로 본문을 쓰지 마세요 (반드시 빈 줄)
- ❌ 모든 내용을 한 문단에 넣지 마세요

**반드시 해야 할 것**:
1. **문단 구분**: 모든 문단 사이에 반드시 빈 줄(줄바꿈 2개: `\n\n`)을 넣어주세요
2. **소제목**: `## 소제목` 다음에는 반드시 빈 줄 하나 추가 후 본문 시작
3. **리스트**: 특징, 사례, 원리는 반드시 마크다운 리스트(`1.`, `2.`, `-`) 형식으로 작성
4. **문단 길이**: 각 문단은 최대 3-4문장으로 제한하고, 그 다음에는 반드시 빈 줄

**올바른 예시 포맷** (반드시 이 형식대로):
```
처음에는 {keyword}가 뭔지 잘 몰랐어요. [2-3문장으로 배경 설명]

최근 들어 {keyword} 이야기를 자주 접하게 되어, 직접 알아보기로 했습니다. [2-3문장으로 동기 설명]

이 글에서는 {keyword}에 대해 초보자의 시각에서 하나씩 알아가는 과정을 공유합니다. [2-3문장으로 독자 안내]

## {keyword}란 무엇인가?

{keyword}는 [정의 설명 3-4문장으로 구성]

예를 들어, [구체적인 예시 2-3문장으로 설명]

## {keyword}의 특징과 원리

{keyword}의 핵심 특징은 다음과 같습니다:

1. 첫 번째 특징: [설명 2-3문장]

2. 두 번째 특징: [설명 2-3문장]

3. 세 번째 특징: [설명 2-3문장]
```

**잘못된 예시** (절대 이렇게 하지 마세요):
```
처음에는 {keyword}가 뭔지 잘 몰랐어요. [모든 내용이 한 문단에...] ## 소제목
[소제목 다음 바로 본문...]
```

다음 JSON 형식으로 응답해주세요:
{{
  "title": "제목 (한글 위주, 학습 스토리 형식)",
  "content": "본문 내용 (마크다운 형식, 문단 구분과 줄바꿈 필수, 자연스러운 문장 흐름, 개인 경험/주관적 표현 포함, 중복 제거, AI 티 없이 인간적 글쓰기, 티스토리 가독성 최우선, 위의 4단계 형식 준수: 서론, 본론(소제목), 결론)",
  "summary": "요약 (200자 이내, 한글 위주)",
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6", "키워드7", "키워드8", "키워드9", "키워드10"],
  "category": "티스토리 카테고리 (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"
}}

**keywords 필드**: 이 포스트와 관련된 키워드 5~10개를 배열로 제공해주세요. SEO를 위한 관련 키워드입니다.
**category 필드**: 티스토리 기준으로 이 포스트가 속할 카테고리를 한 개만 선택해주세요. (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"""
                system_prompt = """당신은 IT 분야에 관심이 있는 30대 직장인입니다. 
초보자의 시각에서 하나씩 차근차근 학습해나가는 스토리 형식으로 글을 작성합니다.

**글쓰기 원칙** (자연스러운 인간의 글):

1. **자연스러운 문장 흐름**:
   - 정형적이고 딱딱한 AI 문장 절대 금지
   - 마치 친구에게 설명하듯 자연스럽게
   - "~입니다", "~합니다" 같은 정형화된 문장 최소화
   - 다양한 문장 패턴 사용 (단문, 중문, 복문 조화)

2. **개인 경험과 주관적 표현**:
   - "처음에는 ~라고 생각했는데", "실제로 해보니 ~", "개인적으로는 ~"
   - 구체적인 감정과 느낌 표현 ("생각보다 어려웠어요", "재미있게 느껴졌어요")
   - 독자와의 공감대 형성 ("아마 이런 경험 있으실 거예요")
   - 주관적 의견과 판단 포함 ("제 기준으로는 ~", "저는 ~라고 봅니다")

3. **중복 및 불필요한 문장 제거**:
   - 같은 의미를 반복하지 않기
   - 핵심만 간결하게 전달
   - 수식어 과다 사용 지양
   - "~는 ~이다" 같은 딱딱한 정의문 피하기

4. **AI 느낌 완전 제거**:
   - "김AI가 작성한 글" 같은 표시 절대 사용 금지
   - 마치 사람이 직접 작성한 것처럼 자연스럽게
   - 기계적인 나열이나 목록식 설명 피하기
   - 감정과 개성 있는 표현 사용

5. **톤앤매너**:
   - 따뜻하고 친근한 말투
   - 과하지 않고 진솔한 표현
   - 실용적이되 딱딱하지 않음
   - 독자를 존중하되 편안한 관계

⚠️ **언어 작성 규칙**:
- 한글 위주로 작성합니다.
- 한자는 절대 사용하지 않습니다.
- 일본어, 베트남어 등 외국어 문자 절대 사용 금지 (まだ, khá 등)
- 기술 용어나 축약어 설명이 필요할 때만 영어를 사용하며, 괄호 안에 한글 설명을 함께 제공합니다 (예: "AI(인공지능)", "API")."""
            else:
                prompt = f"""다음 검색 결과를 기반으로 "{keyword}"에 대한 전문적이고 유용한 블로그 포스트를 작성해주세요.

검색 결과:
{search_summary}

⚠️ **언어 작성 규칙**:
- **한글 위주로 작성**: 본문은 한글로 작성합니다.
- **한자 절대 사용 금지**: 한자는 전혀 사용하지 마세요.
- **영어 사용**: 다음 경우에만 영어 사용 가능
  * 기술 용어나 축약어를 설명할 때: 예) "AI(인공지능)", "API", "GPU"
  * 영어 원문을 그대로 사용하는 것이 더 이해하기 쉬울 때: 예) "Machine Learning(머신러닝)"
  * 축약어나 고유명사를 사용할 때: 예) "OpenAI", "Python"
- **설명 필요시**: 영어 사용 시 괄호 안에 한글 설명을 함께 제공하세요.

요구사항:
1. 제목: 매력적이고 SEO 친화적인 제목 (한글 위주, 필요시 영어)
2. 본문: 최소 1000자 이상의 상세한 내용 (한글 위주, 필요시 영어)
3. 검색 결과의 정보를 참고하되, 원본을 그대로 복사하지 말고 재구성
4. 말투: IT 중소기업 직장인 김AI(30대 남성, ISFJ)의 말투로 작성
   - 조용하고 차분한 톤 (ISFJ 특성)
   - 실용적이고 현실적인 관점
   - 배려심 있고 친절한 설명
   - 세심하고 꼼꼼한 내용 전달
   - "~입니다", "~네요", "~죠" 같은 친근한 존댓말 사용
   - "~할 수 있습니다", "~가 좋을 것 같아요" 같은 자연스러운 표현
   - 독자를 배려하는 따뜻한 말투
5. 적절한 소제목과 문단 구분
6. 기술 용어는 한글 번역을 우선 사용하되, 필요시 영어 표기를 함께 제공

다음 JSON 형식으로 응답해주세요:
{{
  "title": "제목 (한글 위주, 필요시 영어)",
  "content": "본문 내용 (마크다운 형식 가능, 한글 위주, 필요시 영어)",
  "summary": "요약 (200자 이내, 한글 위주)",
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6", "키워드7", "키워드8", "키워드9", "키워드10"],
  "category": "티스토리 카테고리 (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"
}}

**keywords 필드**: 이 포스트와 관련된 키워드 5~10개를 배열로 제공해주세요. SEO를 위한 관련 키워드입니다.
**category 필드**: 티스토리 기준으로 이 포스트가 속할 카테고리를 한 개만 선택해주세요. (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"""
                system_prompt = """당신은 IT 중소기업에서 일하는 30대 남성 블로그 작가 '김AI'입니다.
MBTI는 ISFJ로, 조용하고 배려심이 많으며, 실용적이고 세심한 성격입니다.
검색 결과를 분석하고 독창적이고 유용한 콘텐츠를 작성합니다.

**작가 프로필**:
- 이름: 김AI
- 나이: 30대 남성
- 직업: IT 중소기업 직장인
- MBTI: ISFJ

**글쓰기 스타일 (ISFJ 특성 반영)**:
- 조용하고 차분한 톤
- 실용적이고 현실적인 관점
- 배려심 있고 친절한 설명
- 세심하고 꼼꼼한 내용 구성
- 전통적이면서도 현대적인 균형잡힌 시각
- 독자를 배려하는 따뜻한 말투

⚠️ **언어 작성 규칙**:
- 한글 위주로 작성합니다.
- 한자는 절대 사용하지 않습니다.
- 일본어, 베트남어 등 외국어 문자 절대 사용 금지 (まだ, khá 등)
- 기술 용어나 축약어 설명이 필요할 때만 영어를 사용하며, 괄호 안에 한글 설명을 함께 제공합니다 (예: "AI(인공지능)", "API").

자연스럽고 친근한 말투를 사용하며, 과하지 않고 차분한 톤으로 작성합니다."""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self._call_groq(
                messages,
                response_format={"type": "json_object"}
            )
            
            generated_content = json.loads(response)
            
            title = generated_content.get("title", "")
            content_text = generated_content.get("content", "")
            summary = generated_content.get("summary", "")
            keywords = generated_content.get("keywords", [])
            category = generated_content.get("category", "")  # 티스토리 카테고리
            
            # 한글 검증 및 한자/외국어 강제 제거 (한글 모드일 때만)
            if language == 'korean':
                from utils import remove_hanja_from_text
                
                # 항상 한자/외국어 제거 후처리 강제 적용
                title_cleaned = remove_hanja_from_text(title)
                content_cleaned = remove_hanja_from_text(content_text)
                
                # 제거 전후 비교
                if title != title_cleaned or content_text != content_cleaned:
                    print(f"  🔧 [{self.name}] 한자/외국어 자동 제거 중...")
                    title = title_cleaned
                    content_text = content_cleaned
                
                # 제거 후 검증
                is_valid, error_msg = validate_korean_content(title, content_text)
                
                if not is_valid:
                    print(f"  ⚠️  [{self.name}] 한글 검증 실패: {error_msg}")
                    print(f"  🔄 [{self.name}] 한글로 재생성 시도... (최대 3회)")
                    
                    # 최대 3회 재생성 시도
                    max_retries = 3
                    for retry_count in range(max_retries):
                        retry_messages = [
                            {
                                "role": "system",
                                "content": """당신은 30대 초반 평범한 남성 블로그 작가입니다.

⚠️ **언어 작성 규칙 (엄격히 준수 필수)**:
- 한글 위주로 작성합니다.
- 한자는 절대 사용하지 않습니다. (예: 非常 ❌ → 매우 ✅)
- 베트남어, 중국어 등 외국어 특수 문자를 사용하지 않습니다. (예: khá ❌ → 꽤 ✅)
- 기술 용어나 축약어 설명이 필요할 때만 영어를 사용하며, 괄호 안에 한글 설명을 함께 제공합니다 (예: "AI(인공지능)", "API").

자연스럽고 친근한 말투를 사용하며, 과하지 않고 차분한 톤으로 작성합니다."""
                            },
                            {
                                "role": "user",
                                "content": f"""{prompt}

🚨 **중요**: 이전 응답에 다음 문제가 있었습니다:
{error_msg}

다음 규칙을 엄격히 준수하여 다시 작성해주세요:
1. 한글 위주로 작성 (한자 절대 사용 금지: 非常 ❌ → 매우 ✅)
2. 베트남어, 중국어 등 외국어 특수 문자 사용 금지 (khá ❌ → 꽤 ✅)
3. 필요시에만 영어 사용하며 한글 설명을 함께 제공 (예: "AI(인공지능)")
4. 오직 한글과 필요한 경우에만 영어를 사용하세요.

재시도 횟수: {retry_count + 1}/{max_retries}"""
                            }
                        ]
                        
                        try:
                            retry_response = self._call_groq(
                                retry_messages,
                                response_format={"type": "json_object"}
                            )
                            
                            retry_content = json.loads(retry_response)
                            title = retry_content.get("title", title)
                            content_text = retry_content.get("content", content_text)
                            summary = retry_content.get("summary", summary)
                            # keywords와 category도 업데이트 (없으면 기존 값 유지)
                            retry_keywords = retry_content.get("keywords", [])
                            retry_category = retry_content.get("category", "")
                            if retry_keywords:
                                keywords = retry_keywords
                            if retry_category:
                                category = retry_category
                            
                            # 재생성된 콘텐츠에도 한자/외국어 제거 강제 적용
                            title = remove_hanja_from_text(title)
                            content_text = remove_hanja_from_text(content_text)
                            
                            # 재검증
                            is_valid_retry, retry_error_msg = validate_korean_content(title, content_text)
                            if is_valid_retry:
                                print(f"  ✅ [{self.name}] 한글 재생성 성공 (재시도 {retry_count + 1}회)")
                                break
                            else:
                                if retry_count < max_retries - 1:
                                    print(f"  ⚠️  [{self.name}] 재생성 실패: {retry_error_msg}, 다시 시도...")
                                    error_msg = retry_error_msg
                                else:
                                    print(f"  ⚠️  [{self.name}] 재생성 최종 실패 (3회 시도): {retry_error_msg}")
                                    print(f"  ⚠️  한자/외국어 제거 후처리 적용했으나 검증 실패, 원본 콘텐츠 사용")
                        except Exception as e:
                            if retry_count < max_retries - 1:
                                print(f"  ⚠️  [{self.name}] 재생성 오류: {e}, 다시 시도...")
                            else:
                                print(f"  ⚠️  [{self.name}] 재생성 최종 실패: {e}, 원본 사용")
            
            # 검색 결과 가져오기 (출처용)
            validated_results = input_data.get("validated_results", [])
            
            # 출처 추가 (언어에 따라, 필수)
            if language == 'english':
                sources_section = "\n\n## References\n\n"
                sources_empty_msg = "This article was written based on search results.\n"
            else:
                sources_section = "\n\n## 참고 출처\n\n"
                sources_empty_msg = "검색 결과를 기반으로 작성되었습니다.\n"
            
            sources_list = []
            
            # 검색 결과에서 출처 추출 (중복 제거, 필수)
            seen_links = set()
            for result in validated_results[:10]:  # 최대 10개 출처
                link = result.get('link', '')
                title_link = result.get('title', '')
                
                if link and link not in seen_links and link.startswith('http'):
                    seen_links.add(link)
                    sources_list.append(f"- [{title_link}]({link})")
            
            # 출처가 반드시 있어야 함 (없으면 검색 결과에서 강제 추가)
            if not sources_list:
                print(f"  ⚠️  [{self.name}] 출처가 없어 검색 결과를 출처로 추가합니다.")
                for i, result in enumerate(validated_results[:5], 1):
                    link = result.get('link', '')
                    title = result.get('title', '검색 결과')
                    if link:
                        sources_list.append(f"- [{title}]({link})")
            
            if sources_list:
                sources_section += "\n".join(sources_list)
                sources_section += "\n"
            else:
                sources_section += sources_empty_msg
            
            # 티스토리 카테고리 섹션 추가 (필수)
            if not category or not category.strip():
                # 카테고리가 없으면 기본값 설정
                category = "IT/컴퓨터" if language == 'korean' else "IT/Computer"
                print(f"  ⚠️  [{self.name}] 카테고리가 없어 기본값 '{category}' 사용")
            
            if language == 'english':
                category_section = f"\n\n## Category\n\n`{category}`\n"
            else:
                category_section = f"\n\n## 카테고리\n\n`{category}`\n"
            
            # 관련 키워드 섹션 추가 (5~10개, 필수)
            if not keywords or len(keywords) == 0:
                # 키워드가 없으면 기본 키워드 사용
                keywords = [keyword]
                print(f"  ⚠️  [{self.name}] 키워드가 없어 기본 키워드 '{keyword}' 사용")
            
            # 최대 10개까지만 사용
            keywords_to_use = keywords[:10]
            if language == 'english':
                keywords_section = "\n\n## Related Keywords\n\n"
                keywords_section += ", ".join([f"`{kw}`" for kw in keywords_to_use])
                keywords_section += "\n"
            else:
                keywords_section = "\n\n## 관련 키워드\n\n"
                keywords_section += ", ".join([f"`{kw}`" for kw in keywords_to_use])
                keywords_section += "\n"
            
            # 면책 문구 추가 (언어에 따라, 티스토리 호환 형식, 필수)
            if language == 'english':
                disclaimer = "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ The information in this article may not be 100% accurate. Please use it as a reference.</span>"
            else:
                disclaimer = "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글의 정보는 100% 정확하지 않을 수 있습니다. 참고 자료로 활용하시기 바랍니다.</span>"
            
            # 출처/카테고리/키워드/면책 추가 전에 한자/외국어 제거 (한글 모드일 때만)
            if language == 'korean':
                from utils import remove_hanja_from_text
                content_text_before = content_text
                content_text = remove_hanja_from_text(content_text)
                if content_text_before != content_text:
                    print(f"  🔧 [{self.name}] 최종 한자/외국어 제거 완료")
            
            # 출처/카테고리/키워드/면책 추가 (반드시 추가)
            content_text = content_text + sources_section + category_section + keywords_section + disclaimer
            
            # 키워드/카테고리 추가 확인
            if category_section:
                print(f"  ✅ [{self.name}] 카테고리 추가: {category.strip() if category else '기본값'}")
            else:
                print(f"  ⚠️  [{self.name}] 카테고리 섹션 없음!")
                
            if keywords_section:
                print(f"  ✅ [{self.name}] 키워드 추가: {len(keywords_to_use) if keywords else 0}개")
            else:
                print(f"  ⚠️  [{self.name}] 키워드 섹션 없음!")
            
            print(f"  ✅ [{self.name}] 콘텐츠 생성 완료: {title}")
            if sources_list:
                print(f"  📚 출처 {len(sources_list)}개 추가됨")
            
            return {
                "status": "success",
                "title": title,
                "content": content_text,
                "summary": summary,
                "keywords": keywords,
                "category": category
            }
            
        except Exception as e:
            raise Exception(f"콘텐츠 생성 실패: {e}")

