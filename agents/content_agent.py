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

⚠️ **언어 작성 규칙**:
- **한글 위주로 작성**: 본문은 한글로 작성합니다.
- **한자 절대 사용 금지**: 한자는 전혀 사용하지 마세요.
- **영어 사용**: 다음 경우에만 영어 사용 가능
  * 기술 용어나 축약어를 설명할 때: 예) "AI(인공지능)", "API", "GPU"
  * 영어 원문을 그대로 사용하는 것이 더 이해하기 쉬울 때: 예) "Machine Learning(머신러닝)"
  * 축약어나 고유명사를 사용할 때: 예) "OpenAI", "Python"
- **설명 필요시**: 영어 사용 시 괄호 안에 한글 설명을 함께 제공하세요.

**학습 스토리 형식 요구사항**:
1. **서두**: 처음에는 "{keyword}"에 대해 모르거나 궁금했던 점
   - 예: "처음에는 AI가 뭔지 잘 몰랐어요. 뉴스에서 자주 들었지만..."
   - "처음 접했을 때는 복잡해 보였는데..."
   
2. **본문**: 하나씩 알아가며 이해하게 되는 과정
   - "그런데 이제 이해하기 시작했어요..."
   - "이것을 알게 되니 다음이 궁금해졌습니다..."
   - "자세히 알아보니..."
   - "하나씩 배워가면서..."
   
3. **마무리**: 이제 이해하게 된 것과 다음에 더 알아보고 싶은 점
   - "이제 {keyword}에 대해 이해하게 되었고..."
   - "다음에는 더 깊이 있게..."
   - "이제 조금 알 것 같아요..."

**기타 요구사항**:
1. 제목: 학습 스토리 형식의 매력적인 제목 (예: "{keyword}, 처음에는 몰랐지만 이제 이해하게 된 이야기")
2. 본문: 최소 1500자 이상의 상세한 내용 (한글 위주, 필요시 영어)
3. 검색 결과의 정보를 참고하되, 원본을 그대로 복사하지 말고 재구성
4. 말투: 30대 초반 평범한 남성의 말투로 작성
   - 자연스럽고 친근한 말투
   - 과하지 않고 차분한 톤
   - 전문적이되 딱딱하지 않음
   - "~입니다", "~네요", "~죠" 같은 평범한 존댓말 사용
   - "처음에는...", "그런데...", "이제...", "다음에는..." 같은 학습 진행 표현
5. 적절한 소제목과 문단 구분
6. 기술 용어는 한글 번역을 우선 사용하되, 필요시 영어 표기를 함께 제공

다음 JSON 형식으로 응답해주세요:
{{
  "title": "제목 (한글 위주, 학습 스토리 형식)",
  "content": "본문 내용 (마크다운 형식 가능, 한글 위주, 필요시 영어, 학습 스토리 형식)",
  "summary": "요약 (200자 이내, 한글 위주)",
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6", "키워드7", "키워드8", "키워드9", "키워드10"],
  "category": "티스토리 카테고리 (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"
}}

**keywords 필드**: 이 포스트와 관련된 키워드 5~10개를 배열로 제공해주세요. SEO를 위한 관련 키워드입니다.
**category 필드**: 티스토리 기준으로 이 포스트가 속할 카테고리를 한 개만 선택해주세요. (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"""
                system_prompt = """당신은 30대 초반 평범한 남성 블로그 작가입니다. 
초보자의 시각에서 하나씩 차근차근 학습해나가는 스토리 형식으로 글을 작성합니다.
처음에는 모르고 있었지만, 검색하고 배우면서 이해하게 되는 과정을 자연스럽게 서술합니다.

⚠️ **언어 작성 규칙**:
- 한글 위주로 작성합니다.
- 한자는 절대 사용하지 않습니다.
- 기술 용어나 축약어 설명이 필요할 때만 영어를 사용하며, 괄호 안에 한글 설명을 함께 제공합니다 (예: "AI(인공지능)", "API").

자연스럽고 친근한 말투를 사용하며, 과하지 않고 차분한 톤으로 작성합니다."""
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
4. 말투: 30대 초반 평범한 남성의 말투로 작성
   - 자연스럽고 친근한 말투
   - 과하지 않고 차분한 톤
   - 전문적이되 딱딱하지 않음
   - "~입니다", "~네요", "~죠" 같은 평범한 존댓말 사용
   - "~할 수 있습니다", "~가 좋을 것 같아요" 같은 자연스러운 표현
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
                system_prompt = """당신은 30대 초반 평범한 남성 블로그 작가입니다. 검색 결과를 분석하고 독창적이고 유용한 콘텐츠를 작성합니다.

⚠️ **언어 작성 규칙**:
- 한글 위주로 작성합니다.
- 한자는 절대 사용하지 않습니다.
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
            
            # 한글 검증 (한글 모드일 때만)
            if language == 'korean':
                is_valid, error_msg = validate_korean_content(title, content_text)
                if not is_valid and ("한자" in error_msg or "베트남어" in error_msg or "외국어" in error_msg):
                    # 한자/외국어가 포함된 경우 자동 제거 시도
                    from utils import remove_hanja_from_text
                    print(f"  🔧 [{self.name}] 한자/외국어 자동 제거 중...")
                    title_cleaned = remove_hanja_from_text(title)
                    content_cleaned = remove_hanja_from_text(content_text)
                    
                    # 제거 후 재검증
                    is_valid_cleaned, _ = validate_korean_content(title_cleaned, content_cleaned)
                    if is_valid_cleaned:
                        print(f"  🔧 [{self.name}] 한자/외국어 자동 제거 성공")
                        title = title_cleaned
                        content_text = content_cleaned
                        is_valid = True
                
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
                            keywords = retry_content.get("keywords", keywords)
                            category = retry_content.get("category", category)
                            
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
                                    # 최종 재시도 실패 시 한자 제거 후처리 적용
                                    from utils import remove_hanja_from_text
                                    print(f"  ⚠️  [{self.name}] 재생성 최종 실패 (3회 시도): {retry_error_msg}")
                                    print(f"  🔧 [{self.name}] 한자 제거 후처리 적용 중...")
                                    title = remove_hanja_from_text(title)
                                    content_text = remove_hanja_from_text(content_text)
                                    
                                    # 후처리 후 재검증
                                    is_valid_cleaned, _ = validate_korean_content(title, content_text)
                                    if is_valid_cleaned:
                                        print(f"  ✅ [{self.name}] 한자 제거 후처리 성공")
                                    else:
                                        print(f"  ⚠️  한자 제거 후처리 후에도 검증 실패, 원본 콘텐츠 사용")
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
            
            # 티스토리 카테고리 섹션 추가
            if category:
                if language == 'english':
                    category_section = f"\n\n## Category\n\n`{category}`\n"
                else:
                    category_section = f"\n\n## 카테고리\n\n`{category}`\n"
            else:
                category_section = ""
            
            # 관련 키워드 섹션 추가 (5~10개)
            if keywords and len(keywords) > 0:
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
            else:
                keywords_section = ""
            
            # 면책 문구 추가 (언어에 따라, 티스토리 호환 형식, 필수)
            if language == 'english':
                disclaimer = "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ The information in this article may not be 100% accurate. Please use it as a reference.</span>"
            else:
                disclaimer = "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글의 정보는 100% 정확하지 않을 수 있습니다. 참고 자료로 활용하시기 바랍니다.</span>"
            
            content_text = content_text + sources_section + category_section + keywords_section + disclaimer
            
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

