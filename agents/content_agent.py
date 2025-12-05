"""
콘텐츠 생성 에이전트: 검증된 검색 결과 기반 콘텐츠 생성
"""

from typing import Dict, Any, List
from agents.base import BaseAgent
import json
import sys
import os

# 모듈 import
from src.utils.helpers import validate_korean_content
from src.core.database import Database


class ContentGenerationAgent(BaseAgent):
    """콘텐츠 생성 에이전트"""
    
    def __init__(self):
        super().__init__("콘텐츠 생성 에이전트")
        self.db = Database()
    
    def _analyze_previous_posts(self, language: str, keyword: str = None) -> str:
        """이전 포스팅을 분석하여 개선점 도출"""
        # 현재 키워드 ID 찾기 (제외용)
        exclude_keyword_id = None
        if keyword:
            keyword_obj = self.db.get_keyword_by_name(keyword)
            if keyword_obj:
                exclude_keyword_id = keyword_obj['id']
        
        # 언어별 최근 4개 포스팅 가져오기
        previous_posts = self.db.get_recent_posts_by_language(
            language=language,
            limit=4,
            exclude_keyword_id=exclude_keyword_id
        )
        
        if not previous_posts or len(previous_posts) == 0:
            return "이전 포스팅이 없습니다. 최초 포스팅입니다." if language == 'korean' else "No previous posts. This is the first post."
        
        print(f"  📚 [{self.name}] 이전 포스팅 {len(previous_posts)}개 분석 중... ({'한글' if language == 'korean' else '영문'})")
        
        # 언어별 이전 포스팅 요약 생성 (제목과 본문 일부)
        previous_posts_summary = ""
        for i, post in enumerate(previous_posts, 1):
            title = post.get('title', '제목 없음' if language == 'korean' else 'No Title')
            content_preview = post.get('content', '')[:500]  # 처음 500자만
            if language == 'english':
                previous_posts_summary += f"\n[{i}] Title: {title}\nContent preview: {content_preview}...\n"
            else:  # korean
                previous_posts_summary += f"\n[{i}] 제목: {title}\n내용 일부: {content_preview}...\n"
        
        # 언어별 이전 포스팅 분석 프롬프트
        if language == 'english':
            analysis_prompt = f"""The following are {len(previous_posts)} previously written blog posts. 

Previous Posts:
{previous_posts_summary}

⚠️ **Important**: Analyze the previous posts and identify the following to derive improvement points:

1. **Mechanical Pattern Detection**:
   - Are titles repetitive or following fixed patterns?
   - Are introduction opening phrases identical?
   - Are sentence structures too similar?
   - Is word choice not diverse enough?

2. **Naturalness Assessment**:
   - Is the tone too rigid or formal?
   - Are conjunctions and transition sentences lacking?
   - Are examples and cases insufficient?
   - Are personal experiences and subjective expressions lacking?

3. **Improvement Direction**:
   - What parts should be written differently?
   - What patterns should be avoided?
   - What styles should be added?

Please respond in the following JSON format:
{{
  "mechanical_patterns": ["Found mechanical pattern 1", "Found mechanical pattern 2"],
  "improvement_suggestions": ["Improvement suggestion 1", "Improvement suggestion 2"],
  "avoid_patterns": ["Pattern to avoid 1", "Pattern to avoid 2"],
  "add_variations": ["Variation to add 1", "Variation to add 2"]
}}"""
            system_message = "You are a blog content analysis expert. You analyze previous posts to identify mechanical patterns and suggest directions for more natural and human-like writing. You also evaluate readability (paragraph length, subheadings, lists, bold text usage, etc.) to suggest ways to create reader-friendly content."
        else:  # korean
            analysis_prompt = f"""다음은 이전에 작성된 {len(previous_posts)}개의 포스팅입니다.

이전 포스팅들:
{previous_posts_summary}

⚠️ **중요**: 이전 포스팅들을 분석하여 다음을 확인하고 개선점을 도출해주세요:

1. **기계적인 패턴 확인**:
   - 제목이 반복적이거나 고정 패턴인가?
   - 서론 시작 문구가 똑같은가?
   - 문장 구조가 모두 비슷한가?
   - 단어 선택이 다양하지 않은가?

2. **자연스러움 평가**:
   - 말투가 너무 딱딱하거나 정형적인가?
   - 접속사와 전환 문장이 부족한가?
   - 예시와 사례가 부족한가?
   - 개인 경험과 주관적 표현이 부족한가?

3. **개선 방향**:
   - 어떤 부분을 다르게 작성해야 하는지
   - 어떤 패턴을 피해야 하는지
   - 어떤 스타일을 추가해야 하는지

다음 JSON 형식으로 응답해주세요:
{{
  "mechanical_patterns": ["발견된 기계적 패턴 1", "발견된 기계적 패턴 2"],
  "improvement_suggestions": ["개선 제안 1", "개선 제안 2"],
  "avoid_patterns": ["피해야 할 패턴 1", "피해야 할 패턴 2"],
  "add_variations": ["추가해야 할 변형 1", "추가해야 할 변형 2"]
}}"""
            system_message = "당신은 블로그 콘텐츠 분석 전문가입니다. 이전 포스팅들을 분석하여 기계적인 패턴을 찾고, 더 자연스럽고 인간적인 글쓰기 방향을 제안합니다. 또한 가독성(문단 길이, 소제목, 리스트, 볼드체 사용 등)도 평가하여 독자가 읽기 쉬운 글을 만드는 방법을 제안합니다."
        
        messages = [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": analysis_prompt
            }
        ]
        
        try:
            response = self._call_llm(messages, response_format={"type": "json_object"})
            analysis_result = json.loads(response)
            
            # 분석 결과를 요약된 지침으로 변환 (언어별)
            improvements = []
            if language == 'english':
                if analysis_result.get("mechanical_patterns"):
                    improvements.append(f"❌ Patterns to avoid: {', '.join(analysis_result['mechanical_patterns'][:3])}")
                if analysis_result.get("readability_issues"):
                    improvements.append(f"📖 Readability issues: {', '.join(analysis_result['readability_issues'][:3])}")
                if analysis_result.get("improvement_suggestions"):
                    improvements.append(f"✅ Improvement suggestions: {', '.join(analysis_result['improvement_suggestions'][:3])}")
                if analysis_result.get("avoid_patterns"):
                    improvements.append(f"⚠️ Avoid patterns: {', '.join(analysis_result['avoid_patterns'][:3])}")
                if analysis_result.get("add_variations"):
                    improvements.append(f"➕ Add variations: {', '.join(analysis_result['add_variations'][:3])}")
                if analysis_result.get("readability_suggestions"):
                    improvements.append(f"📚 Readability improvements: {', '.join(analysis_result['readability_suggestions'][:3])}")
                
                if improvements:
                    return "\n".join(improvements)
                else:
                    return "Previous posts analysis complete. Write in a natural and diverse style."
            else:  # korean
                if analysis_result.get("mechanical_patterns"):
                    improvements.append(f"❌ 피해야 할 패턴: {', '.join(analysis_result['mechanical_patterns'][:3])}")
                if analysis_result.get("readability_issues"):
                    improvements.append(f"📖 가독성 문제: {', '.join(analysis_result['readability_issues'][:3])}")
                if analysis_result.get("improvement_suggestions"):
                    improvements.append(f"✅ 개선 제안: {', '.join(analysis_result['improvement_suggestions'][:3])}")
                if analysis_result.get("avoid_patterns"):
                    improvements.append(f"⚠️ 회피 패턴: {', '.join(analysis_result['avoid_patterns'][:3])}")
                if analysis_result.get("add_variations"):
                    improvements.append(f"➕ 추가 변형: {', '.join(analysis_result['add_variations'][:3])}")
                if analysis_result.get("readability_suggestions"):
                    improvements.append(f"📚 가독성 개선: {', '.join(analysis_result['readability_suggestions'][:3])}")
                
                if improvements:
                    return "\n".join(improvements)
                else:
                    return "이전 포스팅 분석 완료. 자연스럽고 다양한 스타일로 작성해야 합니다."
                
        except Exception as e:
            print(f"  ⚠️  [{self.name}] 이전 포스팅 분석 실패: {e}")
            return "이전 포스팅 분석 실패. 기본 가이드라인을 따르세요." if language == 'korean' else "Previous posts analysis failed. Follow the default guidelines."
    
    def _analyze_previous_posts_from_cache(self, language: str, keyword: str = None, cached_posts: List[Dict] = None) -> str:
        """캐시된 이전 포스팅을 분석하여 개선점 도출 (Notion 참조 없음)"""
        if not cached_posts or len(cached_posts) == 0:
            return "캐시된 이전 포스팅이 없습니다. 최초 포스팅입니다."
        
        print(f"  📚 [{self.name}] 캐시된 포스팅 {len(cached_posts)}개 분석 중... ({'한글' if language == 'korean' else '영문'})")
        
        # 캐시된 포스팅 요약 생성 (제목과 본문 일부)
        previous_posts_summary = ""
        for i, post in enumerate(cached_posts, 1):
            title = post.get('title', '제목 없음')
            content_preview = post.get('content', '')[:500]  # 처음 500자만
            previous_posts_summary += f"\n[{i}] 제목: {title}\n내용 일부: {content_preview}...\n"
        
        # 이전 포스팅 분석 프롬프트 (가독성 평가 포함)
        analysis_prompt = f"""다음은 이전에 작성된 {len(cached_posts)}개의 포스팅입니다. 

이전 포스팅들:
{previous_posts_summary}

⚠️ **중요**: 이전 포스팅들을 분석하여 다음을 확인하고 개선점을 도출해주세요:

1. **기계적인 패턴 확인**:
   - 제목이 반복적이거나 고정 패턴인가?
   - 서론 시작 문구가 똑같은가?
   - 문장 구조가 모두 비슷한가?
   - 단어 선택이 다양하지 않은가?

2. **자연스러움 평가**:
   - 말투가 너무 딱딱하거나 정형적인가?
   - 접속사와 전환 문장이 부족한가?
   - 예시와 사례가 부족한가?
   - 개인 경험과 주관적 표현이 부족한가?

3. **가독성 평가 (매우 중요!)**:
   - 문단이 너무 길거나 짧은가? (적절한 길이는 3-5문장)
   - 문장이 너무 길어서 읽기 어려운가? (한 문장은 20-30단어 이내가 적절)
   - 소제목이 충분히 사용되었는가? (본문에 3-4개 이상)
   - 리스트(1., 2., 3. 또는 -, -)가 적절히 사용되었는가?
   - 볼드체(**텍스트**)가 중요 정보 강조에 사용되었는가?
   - 문단 사이 빈 줄이 있어서 읽기 편한가?
   - 전체적인 구조와 흐름이 명확한가?
   - 긴 문단이 통으로 작성되어 있는가? (나눠야 함)
   - 정보가 밀집되어 있어서 읽기 피로한가?

4. **개선 방향**:
   - 어떤 부분을 다르게 작성해야 하는지
   - 어떤 패턴을 피해야 하는지
   - 어떤 스타일을 추가해야 하는지
   - 가독성을 높이기 위해 어떤 요소를 추가해야 하는지 (소제목, 리스트, 볼드체 등)

다음 JSON 형식으로 응답해주세요:
{{
  "mechanical_patterns": ["발견된 기계적 패턴 1", "발견된 기계적 패턴 2"],
  "readability_issues": ["가독성 문제 1 (예: 문단이 너무 길어서 읽기 어려움)", "가독성 문제 2 (예: 리스트가 부족함)"],
  "improvement_suggestions": ["개선 제안 1", "개선 제안 2"],
  "avoid_patterns": ["피해야 할 패턴 1", "피해야 할 패턴 2"],
  "add_variations": ["추가해야 할 변형 1", "추가해야 할 변형 2"],
  "readability_suggestions": ["가독성 개선 제안 1 (예: 긴 문단을 나누기)", "가독성 개선 제안 2 (예: 리스트 형식 사용)"]
}}"""
        
        messages = [
            {
                "role": "system",
                "content": "당신은 블로그 콘텐츠 분석 전문가입니다. 이전 포스팅들을 분석하여 기계적인 패턴을 찾고, 더 자연스럽고 인간적인 글쓰기 방향을 제안합니다. 또한 가독성(문단 길이, 소제목, 리스트, 볼드체 사용 등)도 평가하여 독자가 읽기 쉬운 글을 만드는 방법을 제안합니다."
            },
            {
                "role": "user",
                "content": analysis_prompt
            }
        ]
        
        try:
            response = self._call_llm(messages, response_format={"type": "json_object"})
            analysis_result = json.loads(response)
            
            # 분석 결과를 요약된 지침으로 변환
            improvements = []
            if analysis_result.get("mechanical_patterns"):
                improvements.append(f"❌ 피해야 할 패턴: {', '.join(analysis_result['mechanical_patterns'][:3])}")
            if analysis_result.get("readability_issues"):
                improvements.append(f"📖 가독성 문제: {', '.join(analysis_result['readability_issues'][:3])}")
            if analysis_result.get("improvement_suggestions"):
                improvements.append(f"✅ 개선 제안: {', '.join(analysis_result['improvement_suggestions'][:3])}")
            if analysis_result.get("avoid_patterns"):
                improvements.append(f"⚠️ 회피 패턴: {', '.join(analysis_result['avoid_patterns'][:3])}")
            if analysis_result.get("add_variations"):
                improvements.append(f"➕ 추가 변형: {', '.join(analysis_result['add_variations'][:3])}")
            if analysis_result.get("readability_suggestions"):
                improvements.append(f"📚 가독성 개선: {', '.join(analysis_result['readability_suggestions'][:3])}")
            
            if improvements:
                return "\n".join(improvements)
            else:
                return "캐시된 포스팅 분석 완료. 자연스럽고 다양한 스타일로 작성해야 합니다."
                
        except Exception as e:
            print(f"  ⚠️  [{self.name}] 캐시된 포스팅 분석 실패: {e}")
            return "캐시된 포스팅 분석 실패. 기본 가이드라인을 따르세요."
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """콘텐츠 생성"""
        keyword = input_data["keyword"]
        validated_results = input_data["validated_results"]
        language = input_data.get("language", "korean")  # 기본값: 한글
        learning_story = input_data.get("learning_story", True)  # 기본값: 학습 스토리 형식
        
        print(f"  🤖 [{self.name}] 콘텐츠 생성 중... ({'한글' if language == 'korean' else '영문'}, {'학습 스토리' if learning_story else '일반'})")
        
        # 이전 포스팅 분석하여 개선점 도출
        previous_posts_analysis = self._analyze_previous_posts(language, keyword)
        
        # 검색 결과 요약
        search_summary = "\n".join([
            f"{i+1}. {r['title']}\n   {r['snippet']}\n   출처: {r['link']}"
            for i, r in enumerate(validated_results)
        ])
        
        if language == 'english':
                # 키워드가 한글이면 영어로 변환
                import re
                korean_pattern = re.compile(r'[가-힣]+')
                if korean_pattern.search(keyword):
                    # 한글 키워드를 영어로 변환 (예: "데이터" -> "Data")
                    keyword_translation_map = {
                        "데이터": "Data",
                        "모델": "Model",
                        "알고리즘": "Algorithm",
                        "머신러닝": "Machine Learning",
                        "딥러닝": "Deep Learning",
                        "신경망": "Neural Network",
                        "인공지능": "Artificial Intelligence",
                        "AI": "AI"
                    }
                    english_keyword = keyword_translation_map.get(keyword, keyword)
                    if english_keyword != keyword:
                        print(f"  🔄 키워드 번역: '{keyword}' → '{english_keyword}'")
                    keyword_for_content = english_keyword
                else:
                    keyword_for_content = keyword
                
                prompt = f"""Write a **learning story format** blog post about "{keyword_for_content}" based on the following search results.

🚨🚨🚨 **CRITICAL: If the original keyword was "{keyword}" (in Korean), you MUST translate and use it as "{keyword_for_content}" (in English) in ALL content (title, body, everywhere). NEVER use the Korean keyword "{keyword}" in your English content!** 🚨🚨🚨

⚠️ **Previous Posts Analysis and Improvement (Very Important!)**:
Based on analysis of previously written posts, you must write a more natural and human-like article.

{previous_posts_analysis}

⚠️ **Reflect the above analysis results**:
- Use a different title, different introduction opening, and different structure from previous posts
- Avoid mechanical patterns and use natural, diverse expressions
- Address the issues mentioned above and incorporate the improvement suggestions

**Important**: This post must follow the **EXACT structure below**. It's about a beginner's journey of discovering and understanding "{keyword_for_content}" step by step.

Search Results:
{search_summary}

⚠️ **MANDATORY FORMAT STRUCTURE** (Must follow exactly):

**Introduction (2-3 paragraphs, blank line between each paragraph)**:
- First paragraph: Topic introduction (3-4 sentences)
- [Blank line]
- Second paragraph: Personal motivation or experience (2-3 sentences)
- [Blank line]
- Third paragraph: What readers will learn (2-3 sentences)

**Body (4 mandatory subheadings in order, blank line after each subheading)**:

## What is {keyword_for_content}?

[Blank line]

[2-3 paragraphs, blank line between each]

## Features and Principles of {keyword_for_content}

[Blank line]

**Key Features** (MUST use markdown list format: 1. 2. 3.):
1. First feature: [2-3 sentences]
2. Second feature: [2-3 sentences]
3. Third feature: [2-3 sentences]

[Blank line]

[Principle explanation paragraph: 3-4 sentences]

## {keyword_for_content} Technologies and Applications

[Blank line]

**Key Technologies** (MUST use markdown list):
1. Technology 1: [2-3 sentences]
2. Technology 2: [2-3 sentences]

[Blank line]

**Applications** (MUST use markdown list):
1. **Industry/Field 1**: [2-3 sentences]
2. **Industry/Field 2**: [2-3 sentences]

## My Experience and Thoughts

[Blank line]

[2-3 paragraphs about personal experience, blank line between each]

**Conclusion (3 paragraphs, blank line between each)**:
- First paragraph: Key summary (3-4 sentences)
- [Blank line]
- Second paragraph: Personal reflection (2-3 sentences)
- [Blank line]
- Third paragraph: Message to readers (2-3 sentences)

🚨🚨🚨 **CRITICAL LANGUAGE REQUIREMENTS (MUST FOLLOW - ABSOLUTELY NO EXCEPTIONS)** 🚨🚨🚨:
- Write **ONLY in English**. Do not use ANY other languages including Korean, Chinese, Japanese, Vietnamese, etc.
- **If the original keyword was "{keyword}" (in Korean), you MUST use "{keyword_for_content}" (in English) instead. NEVER write "{keyword}" in your content!**
- **If search results contain Korean text, you MUST translate it to English. NEVER copy Korean text directly.**
- **Before submitting, check: Are there ANY Korean characters (가-힣) in your content? If yes, remove them and translate to English immediately.**
- Write in natural, professional English.
- All paragraphs must be separated by blank lines (\n\n).
- All subheadings must be followed by a blank line.

⚠️ **DO NOT**:
- Write without following the exact structure above
- Skip blank lines between paragraphs
- Write content directly after subheadings without blank lines
- Use Korean characters (가-힣) anywhere in the content
- Copy Korean text from search results

⚠️ **Readability Enhancement**:
- Use **bold** for important keywords and concepts
- Use clear subheadings and proper formatting
- Use lists and numbered items actively
- Break long paragraphs into shorter ones for easy reading

Please respond in the following JSON format:
{{
  "title": "Title (🚨 MUST be written ONLY in English! If original keyword was '{keyword}' (Korean), use '{keyword_for_content}' (English) instead. NO Korean characters (가-힣) allowed! DO NOT use repetitive patterns. Create diverse, natural titles. Maximum 15 words)",
  "content": "Content (🚨 MUST be written ONLY in English! If original keyword was '{keyword}' (Korean), use '{keyword_for_content}' (English) instead. NO Korean characters (가-힣) allowed! MUST follow the exact format structure above: Introduction, 4 Body subheadings, Conclusion, all with blank lines between paragraphs. Use **bold** for emphasis, clear subheadings, and lists for readability)",
  "summary": "Summary (within 200 characters, in English only)",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
  "category": "IT/Computer"
}}

**keywords field**: Provide 5-10 related keywords for this post in an array format.
**category field**: Use "IT/Computer" for technology-related posts."""
                system_prompt = """You are a professional blog writer. Analyze search results and write original and useful content. 

⚠️ **CRITICAL TITLE REQUIREMENT**: 
- ⚠️ **MUST be written ONLY in English** - NO Korean, NO Chinese characters, NO other languages in the title! If Korean appears in the title, it's a critical error.
- DO NOT use repetitive, mechanical title patterns like "Understanding {keyword_for_content}: A Beginner's Journey" or "{keyword_for_content}: What I Learned"
- Create DIVERSE, NATURAL titles every time using different styles:
  * Question format: "What is {keyword_for_content}? A Complete Guide for Beginners"
  * Experience format: "My Journey with {keyword_for_content}: Challenges and Insights"
  * Practical format: "{keyword_for_content} Explained: From Basics to Applications"
  * Story format: "How {keyword_for_content} Changed My Perspective"
  * Comparison format: "{keyword_for_content} vs Other Technologies: What's the Difference?"
  * Problem-solving format: "Solving Real Problems with {keyword_for_content}"
- Each title should be unique, engaging, and human-like - avoid robotic patterns
- Maximum 15 words in the title

🚨🚨🚨 **CRITICAL LANGUAGE RULE (MUST FOLLOW - ABSOLUTELY NO EXCEPTIONS)** 🚨🚨🚨: 
- **Basic Principle**: English documents = **English ONLY**
  * ✅ English: The ONLY allowed language
  * ❌ Korean: ABSOLUTELY FORBIDDEN - NEVER use Korean characters (가-힣)
  * ❌ Chinese characters (Hanja): ABSOLUTELY FORBIDDEN
  * ❌ Japanese: ABSOLUTELY FORBIDDEN
  * ❌ Vietnamese and all other foreign languages: ABSOLUTELY FORBIDDEN
- Write **ONLY in English**. Do not use any other languages including Korean, Chinese characters (Hanja), Japanese, Vietnamese, or any other languages.
- **If the keyword is in Korean (like "데이터"), you MUST translate it to English (like "Data") in ALL content, including title, body, and everywhere else.**
- If search results contain non-English text (Korean, Chinese, Japanese, etc.), you MUST translate it to English. Never copy the original foreign language text.
- **Even if search results show Korean text, you MUST write everything in English only.**
- **Before writing, check: Does the keyword need translation? If it's Korean, translate it first.**
- Write in a natural, friendly tone that is professional but not too formal.
- **After writing, double-check: Are there ANY Korean characters (가-힣) in your content? If yes, remove them and translate to English.**"""
        elif language == 'korean':
            # 한글 모드: 먼저 영문으로 생성 후 번역
            print(f"  🔄 [{self.name}] 한글 모드: 영문 생성 → 한글 번역 방식 사용")
            
            # 키워드 영어 번역 (한글 키워드를 영어로 변환)
            import re
            korean_pattern = re.compile(r'[가-힣]+')
            if korean_pattern.search(keyword):
                keyword_translation_map = {
                    "데이터": "Data",
                    "모델": "Model",
                    "알고리즘": "Algorithm",
                    "머신러닝": "Machine Learning",
                    "딥러닝": "Deep Learning",
                    "신경망": "Neural Network",
                    "인공지능": "Artificial Intelligence",
                    "AI": "AI"
                }
                english_keyword = keyword_translation_map.get(keyword, keyword)
                if english_keyword != keyword:
                    print(f"  🔄 키워드 번역: '{keyword}' → '{english_keyword}'")
                keyword_for_content = english_keyword
            else:
                keyword_for_content = keyword
            
            # 먼저 영문으로 생성 (영문 프롬프트 재사용)
            # 영문 프롬프트를 사용하여 생성
            english_prompt = f"""Write a **learning story format** blog post about "{keyword_for_content}" based on the following search results.

🚨🚨🚨 **CRITICAL: If the original keyword was "{keyword}" (in Korean), you MUST translate and use it as "{keyword_for_content}" (in English) in ALL content (title, body, everywhere). NEVER use the Korean keyword "{keyword}" in your English content!** 🚨🚨🚨

⚠️ **Previous Posts Analysis and Improvement (Very Important!)**:
Based on analysis of previously written posts, you must write a more natural and human-like article.

{previous_posts_analysis}

⚠️ **Reflect the above analysis results**:
- Use a different title, different introduction opening, and different structure from previous posts
- Avoid mechanical patterns and use natural, diverse expressions
- Address the issues mentioned above and incorporate the improvement suggestions

**Important**: This post must follow the **EXACT structure below**. It's about a beginner's journey of discovering and understanding "{keyword_for_content}" step by step.

⚠️ **Very Important: Write from an AI Perspective**:
- This keyword is part of an AI (Artificial Intelligence) learning curriculum.
- You must clearly address the **connection to AI**.
- Don't write about general "{keyword_for_content}" content, but about **"{keyword_for_content} in AI"** or **"{keyword_for_content} from an AI perspective"**.
- Example: "Data" → "Data used in AI", "The relationship between Machine Learning and Data", "Data for AI learning", etc.
- AI와의 연결고리를 자연스럽게 녹여내되, 내용 전체가 AI 맥락에서 이해되도록 작성하세요.

Search Results:
{search_summary}

⚠️ **MANDATORY FORMAT STRUCTURE** (Must follow exactly):

**Introduction (2-3 paragraphs, blank line between each paragraph)**:
- First paragraph: Topic introduction from AI perspective (3-4 sentences)
- [Blank line]
- Second paragraph: Personal motivation or experience with AI (2-3 sentences)
- [Blank line]
- Third paragraph: What readers will learn about AI and {keyword_for_content} (2-3 sentences)

**Body (3-4 mandatory subheadings, blank line after each subheading)**:

## What is {keyword_for_content}? (in AI context)

[Blank line]

[2-3 paragraphs about {keyword_for_content} in AI context, blank line between each]

## Features and Principles of {keyword_for_content} in AI

[Blank line]

**Key Features** (MUST use markdown list format: 1. 2. 3.):
1. First feature related to AI: [2-3 sentences]
2. Second feature related to AI: [2-3 sentences]
3. Third feature related to AI: [2-3 sentences]

[Blank line]

[Principle explanation paragraph about AI and {keyword_for_content}: 3-4 sentences]

## {keyword_for_content} Technologies and Applications in AI

[Blank line]

**Key Technologies** (MUST use markdown list):
1. Technology 1 in AI: [2-3 sentences]
2. Technology 2 in AI: [2-3 sentences]

[Blank line]

**Applications** (MUST use markdown list):
1. **Industry/Field 1**: [2-3 sentences]
2. **Industry/Field 2**: [2-3 sentences]

## My Experience and Thoughts (about AI and {keyword_for_content})

[Blank line]

[2-3 paragraphs about personal experience with AI and {keyword_for_content}, blank line between each]

**Conclusion (2-3 paragraphs, blank line between each)**:
- First paragraph: Key summary about AI and {keyword_for_content} (3-4 sentences)
- [Blank line]
- Second paragraph: Personal reflection on learning AI (2-3 sentences)
- [Blank line]
- Third paragraph: Message to readers about AI learning (2-3 sentences)

⚠️ **Language Requirements**:
- Write **only in English**. Do not use any other languages.
- Write in natural, professional English.
- All paragraphs must be separated by blank lines (\n\n).
- All subheadings must be followed by a blank line.

⚠️ **DO NOT**:
- Write without following the exact structure above
- Skip blank lines between paragraphs
- Write content directly after subheadings without blank lines

⚠️ **Readability Enhancement**:
- Use **bold** for important keywords and concepts
- Use clear subheadings and proper formatting
- Use lists and numbered items actively
- Break long paragraphs into shorter ones for easy reading

Please respond in the following JSON format:
{{
  "title": "Title (⚠️ MUST be written ONLY in English! DO NOT use repetitive patterns like 'Understanding {keyword_for_content}: A Beginner's Journey' every time. Create diverse, natural titles from AI perspective: question format, experience sharing, practical guide, story format, explanation format, comparison format, etc. Make each title unique and engaging. Maximum 15 words)",
  "content": "Content (⚠️ MUST follow the exact format structure above: Introduction, 3-4 Body subheadings about AI, Conclusion, all with blank lines between paragraphs. Use **bold** for emphasis, clear subheadings, and lists for readability)",
  "summary": "Summary (within 200 characters, in English only)",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"],
  "category": "IT/Computer"
}}"""
            
            english_system_prompt = """You are a professional blog writer. Analyze search results and write original and useful content from an AI perspective.

⚠️ **CRITICAL LANGUAGE RULE**: 
- Write **ONLY in English**. Do not use Korean or any other languages.
- Write in a natural, friendly tone that is professional but not too formal.
- All content must be written from an AI perspective, connecting the keyword to artificial intelligence."""
            
            # 영문으로 먼저 생성
            english_messages = [
                {"role": "system", "content": english_system_prompt},
                {"role": "user", "content": english_prompt}
            ]
            
            try:
                print(f"  📝 [{self.name}] 1단계: 영문 콘텐츠 생성 중...")
                english_response = self._call_llm(
                    english_messages,
                    response_format={"type": "json_object"}
                )
                
                english_content = json.loads(english_response)
                english_title = english_content.get("title", "")
                english_content_text = english_content.get("content", "")
                english_summary = english_content.get("summary", "")
                english_keywords = english_content.get("keywords", [])
                english_category = english_content.get("category", "IT/컴퓨터")
                
                print(f"  ✅ [{self.name}] 영문 생성 완료: {english_title[:50]}")
                
                # 2단계: 한글로 번역
                print(f"  🔄 [{self.name}] 2단계: 한글로 번역 중...")
                
                translation_prompt = f"""다음은 영문 블로그 포스트입니다. 이것을 **자연스러운 한국어**로 번역해주세요.

🚨🚨🚨 **절대적 명령: 반드시 형식을 유지해야 합니다!** 🚨🚨🚨

⚠️ **번역 규칙 (매우 중요 - 절대 위반 불가)**:

1. **제목 번역**:
   - 제목을 자연스러운 한국어로 번역하되, 15자 이내로 작성
   - AI 관점을 반영한 자연스러운 제목으로 번역
   - 예: "Uncovering Data" → "AI에서 데이터 이해하기"

2. **본문 번역 - 구조 필수**:
   ⚠️ **절대 형식 없이 통으로 작성하면 안 됩니다!**
   
   반드시 다음 구조를 따라야 합니다:
   
   ## 서론 (Introduction)
   [빈 줄 필수]
   [문단 1: 3-4문장]
   [빈 줄 필수]
   [문단 2: 2-3문장]
   [빈 줄 필수]
   [문단 3: 2-3문장]
   [빈 줄 필수]
   
   ## 본론 소제목 1 (예: 데이터란 무엇인가?)
   [빈 줄 필수]
   [본문 문단들, 각 문단 사이 빈 줄 필수]
   [빈 줄 필수]
   
   ## 본론 소제목 2
   [빈 줄 필수]
   [본문 문단들, 각 문단 사이 빈 줄 필수]
   [빈 줄 필수]
   
   ## 본론 소제목 3
   [빈 줄 필수]
   [본문 문단들, 각 문단 사이 빈 줄 필수]
   [빈 줄 필수]
   
   ## 결론
   [빈 줄 필수]
   [결론 문단들, 각 문단 사이 빈 줄 필수]

3. **형식 유지 규칙**:
   - ⚠️ **절대 형식 없이 통으로 작성하면 안 됩니다!**
   - 마크다운 형식(##, **, 1., 2. 등)은 그대로 유지
   - 문단 사이 반드시 빈 줄(\n\n) 유지
   - 소제목(##) 다음 반드시 빈 줄 하나 유지
   - 소제목도 자연스러운 한국어로 번역 (예: "## What is Data?" → "## 데이터란 무엇인가?")
   - 각 문단은 2-4문장으로 구성
   - 리스트 형식은 그대로 유지 (1., 2., 3. 또는 -, -)

4. **언어 규칙**:
   - 한국어 + 필요시 영어 기술 용어만 사용
   - 기술 용어는 괄호로 영어 원문 포함 (예: "AI(인공지능)")
   - 자연스러운 한국어 표현 사용
   - 존댓말(~요, ~네요)과 평어(~다, ~이다)를 자연스럽게 혼합
   - 절대 한자, 일본어, 중국어 등 다른 언어 사용 금지

5. **구조 유지 (매우 중요)**:
   - ⚠️ 반드시 서론-본론(3-4개 소제목)-결론 구조 유지
   - ⚠️ 형식 없이 통으로 작성하면 절대 안 됩니다!
   - 소제목은 반드시 ## 형식으로 작성
   - 소제목과 본문 사이, 문단과 문단 사이 반드시 빈 줄 유지

6. **AI 관점 유지**:
   - 원문의 AI 관점을 그대로 반영
   - AI와의 연결고리를 자연스럽게 유지

영문 제목:
{english_title}

영문 본문:
{english_content_text}

⚠️ **중요**: 번역 시 형식을 절대 잃어버리면 안 됩니다! 서론-본론-결론 구조와 모든 빈 줄을 그대로 유지해야 합니다.

다음 JSON 형식으로 응답해주세요:
{{
  "title": "번역된 한글 제목 (15자 이내, 자연스러운 한국어, AI 관점 반영)",
  "content": "번역된 한글 본문 (🚨 반드시 서론-본론(3-4개 소제목)-결론 구조 유지, 각 문단 사이 반드시 빈 줄(\\n) 필수, 소제목(##) 다음 반드시 빈 줄(\\n) 필수, 마크다운 형식 유지, 띄어쓰기 없이 통으로 작성하면 절대 안 됩니다! 문단이 구분되지 않으면 안 됩니다! **중요**: JSON에서 빈 줄은 반드시 \\n으로 표현해주세요)",
  "summary": "번역된 한글 요약 (200자 이내)",
  "keywords": {json.dumps([kw for kw in english_keywords], ensure_ascii=False)},
  "category": "IT/컴퓨터"
}}

⚠️ **JSON 응답 시 주의사항**:
- content 필드에서 빈 줄은 반드시 \\\\n으로 표현해야 합니다
- 소제목(##) 다음에는 반드시 \\\\n\\\\n이 있어야 합니다
- 문단 끝(마침표 다음)에는 반드시 \\\\n\\\\n이 있어야 합니다
- 예시: "## 제목\\\\n\\\\n첫 번째 문단 내용입니다.\\\\n\\\\n두 번째 문단 내용입니다."
"""
                
                translation_system_prompt = """당신은 전문 번역가입니다. 영문 블로그 포스트를 자연스러운 한국어로 번역합니다. 

🚨🚨🚨 **절대적 명령: 반드시 한글로만 번역! 형식 반드시 유지!** 🚨🚨🚨

⚠️ 매우 중요 (절대 위반 불가):

1. **언어 규칙 (절대 위반 불가)**:
   - 🚨 **반드시 한글로만 번역** (제목, 본문 모두)
   - 영어는 기술 용어 설명 시에만 괄호 안에 사용 (예: "AI(인공지능)")
   - 절대로 영어 문장이나 영어가 주가 되는 내용 금지
   - 제목도 반드시 한글로만 작성

2. **마크다운 형식과 구조를 정확히 유지해야 합니다**
   - 소제목은 반드시 ## 형식으로 작성
   - 리스트는 반드시 - 또는 1. 2. 3. 형식으로 작성
   - 볼드체는 **텍스트** 형식으로 작성

3. **절대 형식 없이 통으로 작성하면 안 됩니다**
   - 띄어쓰기 없이 연결해서 작성하면 절대 안 됩니다
   - 모든 문단은 반드시 구분되어야 합니다
   - 문단과 문단 사이 반드시 빈 줄(\\n\\n) 필요

4. **반드시 서론-본론(3-4개 소제목)-결론 구조를 유지해야 합니다**
   - 서론: 2-3개 문단, 각 문단 사이 빈 줄(\\n\\n)
   - 본론: 3-4개 소제목(##), 각 소제목 다음 빈 줄(\\n\\n), 각 문단 사이 빈 줄(\\n\\n)
   - 결론: 2-3개 문단, 각 문단 사이 빈 줄(\\n\\n)

5. **모든 문단 사이, 소제목과 본문 사이 반드시 빈 줄을 유지해야 합니다**
   - 소제목(##) 다음: 반드시 빈 줄(\\n\\n) 1개
   - 문단 끝 다음: 반드시 빈 줄(\\n\\n) 1개
   - 빈 줄이 없으면 형식이 깨진 것으로 간주합니다

6. **AI 관점을 반영하여 번역합니다**

⚠️ **절대 금지 사항**:
- 영어로 번역하면 절대 안 됩니다!
- 띄어쓰기 없이 모든 내용을 한 줄로 작성
- 문단 구분 없이 통으로 작성
- 소제목 다음 빈 줄 없이 바로 본문 작성
- 형식 없이 텍스트만 나열
- 서론-본론-결론 구조 없이 작성"""
                
                translation_messages = [
                    {"role": "system", "content": translation_system_prompt},
                    {"role": "user", "content": translation_prompt}
                ]
                
                translation_response = self._call_llm(
                    translation_messages,
                    response_format={"type": "json_object"}
                )
                
                translated_content = json.loads(translation_response)
                title = translated_content.get("title", "")
                content_text = translated_content.get("content", "")
                summary = translated_content.get("summary", english_summary)
                keywords = translated_content.get("keywords", english_keywords)
                category = translated_content.get("category", english_category)
                
                # JSON 파싱 후 이스케이프 문자 복구 (\n → 실제 줄바꿈)
                # JSON에서 \\n이 실제 \n으로 저장되었을 수 있음
                if '\\n' in content_text:
                    content_text = content_text.replace('\\n', '\n')
                
                # 번역 직후 형식 자동 수정 (빈 줄 추가 등)
                from src.utils.format_fixer import fix_korean_content_format
                content_text = fix_korean_content_format(content_text)
                print(f"  🔧 [{self.name}] 번역 후 형식 자동 수정 완료")
                
                # 번역 직후 형식 검증 (통으로 작성되지 않았는지 확인)
                from agents.validation_agent import ContentValidationAgent
                format_validator = ContentValidationAgent()
                format_valid, format_error = format_validator._validate_korean_format(content_text)
                
                if not format_valid:
                    print(f"  ⚠️  [{self.name}] 번역 후 형식 검증 실패: {format_error}")
                    print(f"  🔄 형식 문제가 있어 재번역을 시도합니다...")
                    
                    # 재번역 프롬프트 (형식 문제 명시)
                    retry_translation_prompt = f"""이전 번역에서 형식 문제가 발생했습니다. 다시 번역할 때 반드시 다음을 준수해주세요:

❌ 이전 번역의 문제점:
{format_error}

🚨 **절대적 명령 (반드시 지켜야 함)**:
1. **문단 구분**: 모든 문단 사이 반드시 빈 줄(줄바꿈) 필요
2. **소제목 다음**: 모든 소제목(##) 다음 반드시 빈 줄 1개 필요
3. **구조 유지**: 서론(2-3문단) - 본론(3-4개 소제목) - 결론(2-3문단)
4. **절대 금지**: 띄어쓰기 없이 통으로 작성하면 안 됩니다!

영문 제목:
{english_title}

영문 본문:
{english_content_text}

⚠️ 다시 번역해주세요. 반드시 형식을 유지하고, 모든 문단 사이, 소제목 다음 빈 줄을 포함해주세요!

다음 JSON 형식으로 응답해주세요:
{{
  "title": "번역된 한글 제목 (15자 이내)",
  "content": "번역된 한글 본문 (⚠️ 반드시 문단 사이 빈 줄, 소제목 다음 빈 줄 포함!)",
  "summary": "번역된 한글 요약 (200자 이내)",
  "keywords": {json.dumps([kw for kw in english_keywords], ensure_ascii=False)},
  "category": "IT/컴퓨터"
}}"""
                    
                    retry_messages = [
                        {"role": "system", "content": translation_system_prompt},
                        {"role": "user", "content": retry_translation_prompt}
                    ]
                    
                    retry_response = self._call_llm(
                        retry_messages,
                        response_format={"type": "json_object"}
                    )
                    
                    retry_translated = json.loads(retry_response)
                    title = retry_translated.get("title", title)
                    content_text = retry_translated.get("content", content_text)
                    summary = retry_translated.get("summary", summary)
                    keywords = retry_translated.get("keywords", keywords)
                    category = retry_translated.get("category", category)
                    
                    # 재번역 후 다시 형식 검증
                    format_valid, format_error = format_validator._validate_korean_format(content_text)
                    if not format_valid:
                        print(f"  ⚠️  [{self.name}] 재번역 후에도 형식 검증 실패: {format_error}")
                        print(f"  ⚠️  형식 문제가 있지만 계속 진행합니다. 검증 단계에서 수정될 수 있습니다.")
                    else:
                        print(f"  ✅ [{self.name}] 재번역 후 형식 검증 통과!")
                
                print(f"  ✅ [{self.name}] 한글 번역 완료: {title[:50]}")
                
                # 번역된 콘텐츠 사용 - 바로 검증 단계로 이동 (아래 코드 스킵)
                # title, content_text, summary, keywords, category가 이미 설정됨
                translation_success = True
                
            except Exception as e:
                print(f"  ❌ [{self.name}] 영문→한글 번역 실패: {e}")
                import traceback
                traceback.print_exc()
                # 번역 실패 시 에러 반환 (fallback 제거)
                return {
                    "status": "failed",
                    "message": f"영문→한글 번역 실패: {str(e)}",
                    "error": str(e)
                }
                prompt = f"""⚠️ **매우 중요: 반드시 한글로만 작성해야 합니다!** 영어로 작성하면 안 됩니다!

⚠️ **언어 작성 규칙 (절대 위반 불가)**:
- 제목: 반드시 한글로만 작성 (예: "AI에서 데이터 이해하기")
- 본문: 반드시 한글로만 작성
- 소제목: 반드시 한글로만 작성 (예: "## 데이터란 무엇인가?")
- 영어는 기술 용어나 고유명사 설명 시에만 사용 가능 (예: "AI(인공지능)", "OpenAI")
- 절대로 영어로 작성하면 안 됩니다!
- 검색 결과가 영어여도 반드시 한글로 번역해서 작성하세요!

다음 검색 결과를 기반으로 "{keyword}"에 대한 **AI 관련 학습 스토리 형식**의 블로그 포스트를 **반드시 한글로만** 작성해주세요.

⚠️ **이전 포스팅 분석 및 개선 (매우 중요!)**:
이전에 작성된 포스팅들을 분석한 결과를 바탕으로, 더 자연스럽고 인간적인 글을 작성해야 합니다.

{previous_posts_analysis}

⚠️ **위 분석 결과를 반영하여**:
- 이전 포스팅과 다른 제목, 다른 서론 시작 문구, 다른 구조를 사용하세요
- 기계적인 패턴을 피하고, 자연스럽고 다양한 표현을 사용하세요
- 위에서 지적된 문제점들을 해결하고, 개선 제안을 반영하세요
- 📖 **가독성 개선 제안을 반드시 반영하세요**: 문단 길이 조절, 소제목 활용, 리스트 및 볼드체 사용 등

⚠️ **매우 중요: AI 관련 키워드**:
- 이 키워드는 AI(인공지능) 학습 커리큘럼의 일부입니다.
- 반드시 **AI 관점**에서 작성해야 합니다. AI와의 연관성을 명확히 다뤄야 합니다.
- 단순히 "{keyword}" 일반적인 내용이 아니라, **"AI에서의 {keyword}"** 또는 **"AI 관점에서 본 {keyword}"**로 작성해야 합니다.
- 예: "데이터" → "AI에서 사용되는 데이터", "머신러닝과 데이터", "AI 학습을 위한 데이터" 등
- AI와의 연결고리를 명확히 하되, 자연스럽게 녹여내세요.

**중요**: 이 글은 초보자가 "{keyword}"를 **AI 관점**에서 처음 접하고, 하나씩 알아가며 이해하게 되는 과정을 스토리로 풀어낸 것입니다.

검색 결과:
{search_summary}

⚠️ **언어 작성 규칙 (무조건 준수 - 절대 위반 불가)**:
- **🚨 핵심 원칙**: **한글이 주가 되어야 합니다!** 영어는 필요시에만 최소한으로 사용!
  * ✅ **한국어가 주**: 전체 내용의 80% 이상은 한글이어야 함
  * ✅ **영어는 보조**: 기술 용어나 축약어 설명 시에만 사용 가능 (예: "AI(인공지능)", "API")
  * ❌ **절대 금지**: 영어 문장이나 영어가 주가 되는 내용
  * ❌ 일본어 절대 금지: データ, まだ, あり 등 → 한국어로 번역
  * ❌ 중국어(한자) 절대 금지: 非常, 数据 등 → 한국어로 번역
  * ❌ 베트남어 등 기타 모든 외국어 절대 금지
- **영어 사용 규칙 (최소한만!)**:
  * 기술 용어나 축약어 설명: "AI(인공지능)", "API", "GPU"
  * 영어 원문이 이해에 도움: "Machine Learning(머신러닝)"
  * 고유명사: "OpenAI", "Python"
  * ❌ **금지**: 영어 문장, 영어로 된 설명, 영어가 많은 문단
- **⚠️ 매우 중요**: 
  * 한글이 주가 되어야 합니다 (한글 비율 80% 이상)
  * 영어는 기술 용어 설명 시에만 괄호 안에 최소한으로 사용
  * 검색 결과가 영어여도 반드시 한글로 번역해서 작성
  * 일본어, 중국어 등 모든 외국어는 한국어로 번역
- **검색 결과 처리**: 검색 결과에 일본어(データ 등), 중국어, 베트남어가 있어도 **절대 그대로 사용하지 말고**, 반드시 한국어로 번역해서 사용하세요.
  - 예: データ ❌ → 데이터 ✅
  - 예: まだ ❌ → 아직 ✅
  - 예: 非常 ❌ → 매우 ✅
- **한자 절대 금지**: 모든 한자를 한국어로 번역하세요.

**블로그 글 작성 형식 (실제 블로그들의 베스트 프랙티스 학습 결과 반영)**:

⚠️ **중요**: 본문에 제목을 다시 적지 마세요. 제목은 JSON의 "title" 필드에만 작성하고, 본문은 서론부터 시작하세요.

## 서론 (Introduction) - 2-3단락 (각 문단 사이 빈 줄 필수)

⚠️ **매우 중요: 서론 시작 문구는 절대 반복하지 마세요!**

실제 IT 기술 블로그들의 서론 패턴:

1. **주제 도입 문단** (3-4문장): 간략한 배경 설명
2. **[빈 줄]** 
3. **동기 문단** (2-3문장): 글을 쓰게 된 개인적인 경험이나 계기
4. **[빈 줄]**
5. **독자 안내 문단** (2-3문장): 이 글에서 무엇을 배울 수 있는지

⚠️ **중요**: 각 문단 사이에 반드시 빈 줄(줄바꿈)을 넣어야 합니다!

⚠️ **서론 시작 문구 다양화 (절대 고정 패턴 사용 금지)**:
다음과 같은 고정 패턴을 절대 사용하지 마세요:
❌ "처음에는 {keyword}가 뭔지 잘 몰랐어요."
❌ "최근 들어 {keyword} 이야기를 자주 접하게 되어, 직접 알아보기로 했습니다."
❌ "데이터가 뭔지 잘 몰랐어요."

대신 다음과 같은 다양한 시작 패턴을 매번 다르게 사용하세요:

**다양한 시작 패턴 예시** (매번 다르게 선택):
1. **질문형**: "{keyword}에 대해 들어본 적은 있지만, 정확히 무엇인지는 모르겠다. 궁금해서 알아보기 시작했다."
2. **상황 제시형**: "회사에서 {keyword}라는 말을 들었을 때, 막막한 기분이 들었다. 배워야겠다고 생각했다."
3. **호기심 유발형**: "{keyword}라는 단어를 보면 왠지 복잡해 보였다. 하지만 알고 보니 생각보다 간단했다."
4. **경험 공유형**: "직접 {keyword}를 다뤄보면서 알게 된 점들이 많다. 처음에는 헷갈렸지만 점점 이해가 됐다."
5. **문제 인식형**: "{keyword}에 대해 정확히 알지 못해서 문제가 생긴 적이 있다. 그래서 제대로 배우기로 했다."
6. **관심사 연결형**: "평소 관심 있던 분야에서 {keyword}를 접하게 되었다. 더 자세히 알고 싶어졌다."
7. **우연 계기형**: "우연히 {keyword} 관련 글을 읽게 되었다. 생각보다 흥미로워서 더 알아보기 시작했다."
8. **도전 의지형**: "{keyword}를 배우는 건 쉽지 않을 것 같았다. 하지만 도전해보기로 마음먹었다."

**동기 문단도 다양하게**:
- ❌ 금지: "최근 들어 {keyword} 이야기를 자주 접하게 되어, 직접 알아보기로 했습니다."
- ✅ 가능: "직장에서 {keyword}가 필요하다는 걸 알게 됐어요."
- ✅ 가능: "프로젝트에서 {keyword}를 사용해야 하는 상황이 생겼습니다."
- ✅ 가능: "친구가 {keyword}에 대해 이야기하는 걸 듣고 관심이 생겼어요."

**독자 안내 문단도 다양하게**:
- ❌ 금지: "이 글에서는 {keyword}에 대해 초보자의 시각에서 하나씩 알아가는 과정을 공유합니다."
- ✅ 가능: "이 글을 통해 {keyword}의 기본 개념부터 활용 방법까지 알아보겠습니다."
- ✅ 가능: "{keyword}가 무엇인지, 어떻게 사용하는지 함께 살펴보려고 합니다."

⚠️ **중요**: 위 예시 패턴 중 하나를 선택해서 사용하되, 매번 다른 패턴을 사용해야 합니다. 절대 같은 문구를 반복하지 마세요!

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
1. **제목**: 다양하고 자연스러운 제목 생성 (⚠️ 매우 중요!)
   - ⚠️ **반드시 15자 이내**로 작성해야 합니다 (공백 포함)
   - ⚠️ **완벽한 한 문장**으로 끝나야 합니다
   - ⚠️ 절대 "{keyword}, 처음에는 몰랐지만 이제 이해하게 된 이야기" 같은 고정 패턴 사용 금지
   - 키워드를 포함하되, 매번 다른 스타일의 제목을 생성해야 함
   - 독자의 호기심을 자극하는 다양한 형식 사용:
     * 질문형: "{keyword}가 뭔가요? 처음 접하는 사람을 위한 가이드"
     * 경험담형: "{keyword}를 알아가면서 느낀 점"
     * 실용형: "{keyword} 이해하기: 기본 개념부터 활용까지"
     * 스토리형: "{keyword}와의 첫 만남: 어려웠지만 흥미로웠던 여정"
     * 설명형: "{keyword}란? 초보자를 위한 상세 가이드"
     * 비교형: "{keyword}, 다른 기술과는 어떻게 다를까?"
     * 문제해결형: "{keyword}로 해결할 수 있는 일들"
   - 매번 새로운 형식과 접근 방식으로 제목을 다양하게 생성
   - 자연스럽고 인간적인 제목 (기계적인 패턴 피하기)

2. **본문 길이**: 최소 1500자 이상, 권장 2000-2500자
   - 서론: 200-300자
   - 본론: 1200-1800자 (각 소제목당 300-450자)
   - 결론: 200-300자

3. **작성 스타일** (실제 블로그들의 베스트 프랙티스):
   - **자연스러운 문장 흐름**: 정형적인 "~입니다", "~합니다" 남발 금지. 존댓말(~요, ~네요)과 평어(~다, ~이다)를 자연스럽게 혼합. 과도한 요요체 피하기
   - **개인 경험과 주관적 표현**: "처음에는 ~라고 생각했는데", "실제로 해보니 ~", "개인적으로는 ~" 같은 표현 포함. 말투는 평어와 존댓말 자연스럽게 혼합
   - **감정과 느낌 표현**: 말투 다양하게 사용 - "생각보다 어려웠다" / "생각보다 어려웠어요", "재미있게 느껴졌어" / "재미있게 느껴졌어요" 등 평어와 존댓말 자연스럽게 혼합
   - **중복 제거**: 같은 의미 반복 금지, 핵심만 간결하게 전달
   - **AI 티 제거**: "김AI" 같은 표시 절대 사용 금지. 마치 사람이 직접 작성한 것처럼 자연스럽게
   - **명확성**: 전문 용어를 최소화하고, 독자가 쉽게 이해할 수 있도록 설명
   - **일관성**: 문체와 톤을 일관되게 유지
   - **구체성**: 추상적 설명보다 구체적인 예시와 사례 제공
   - **가독성**: 소제목, 리스트, 번호 매기기, **볼드체** 등을 적극 활용하여 가독성 향상
     * 중요한 키워드나 개념은 **볼드체**로 강조
     * 소제목을 명확하게 구분
     * 리스트와 번호 매기기를 적극 활용
     * 긴 문단은 짧게 나누어 읽기 쉽게 구성

4. **말투 규칙** (자연스러운 인간의 글):
   - 정형적인 AI 문장 절대 금지 ("~입니다", "~합니다" 남발 금지)
   - ⚠️ **말투는 존댓말과 평어를 자연스럽게 혼합**:
     * 과도한 "~요", "~네요" 같은 요요체만 사용하지 말 것
     * 평어(~다, ~이다, ~라)도 자연스럽게 섞어서 사용
     * 예: "이건 정말 좋은 기술이다. 여러분도 한번 써보면 이해가 될 거예요."
     * 예: "처음에는 어려웠어. 하지만 점점 재미있어졌다."
   - 다양한 문장 패턴 사용 (단문, 중문, 복문 조화)
   - 개인 경험과 주관적 표현 포함 (말투 자연스럽게):
     * "처음에는 ~라고 생각했어" / "처음에는 ~라고 생각했어요" (둘 다 사용)
     * "실제로는 ~" / "실제로는 ~예요" (둘 다 자연스럽게)
   - 감정과 느낌 표현 (말투 다양하게):
     * "생각보다 어려웠다" / "생각보다 어려웠어요" (둘 다 사용)
     * "재미있게 느껴졌어" / "재미있게 느껴졌다" (둘 다 사용)
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

6. **검색 결과 활용 및 사실 확인**:
   - 검색 결과의 정보를 참고하되, 원본을 그대로 복사하지 말고 재구성
   - 여러 검색 결과를 종합하여 일관된 스토리로 재구성
   - 검색 결과의 내용을 학습 과정에 자연스럽게 녹여내기
   - ⚠️ **사실 확인 필수**:
     * 통계, 숫자, 정의 등은 정확히 검토 (공식 문서, 논문, 신뢰 가능한 사이트 참고)
     * 잘못된 내용이 있다면 수정하거나 명확히 표시
     * 출처의 신뢰성을 평가 (공식 사이트 > 학술 자료 > 뉴스 매체 > 개인 블로그)
     * 공식 문서, 논문, 신뢰 가능한 사이트의 정보를 우선적으로 사용

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

**올바른 예시 포맷** (반드시 이 형식대로, 단 시작 문구는 매번 다양하게):
```
[다양한 시작 패턴 중 하나 선택 - 절대 고정 문구 사용 금지]
예: "{keyword}에 대해 들어본 적은 있지만, 정확히 무엇인지는 모르겠다. 궁금해서 알아보기 시작했다." [2-3문장으로 배경 설명]

[다양한 동기 문구 중 하나 선택 - 절대 고정 문구 사용 금지]
예: "직장에서 {keyword}가 필요하다는 걸 알게 됐어요. 배워야겠다고 생각했습니다." [2-3문장으로 동기 설명]

[다양한 독자 안내 문구 중 하나 선택 - 절대 고정 문구 사용 금지]
예: "이 글을 통해 {keyword}의 기본 개념부터 활용 방법까지 알아보겠습니다." [2-3문장으로 독자 안내]

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
  "title": "제목 (⚠️ 반드시 15자 이내, 완벽한 한 문장으로 끝나야 함! 절대 '{keyword}, 처음에는 몰랐지만 이제 이해하게 된 이야기' 같은 고정 패턴 사용 금지! 매번 다른 스타일의 자연스러운 제목 생성: 질문형, 경험담형, 실용형, 스토리형, 설명형 등 다양하게)",
  "content": "본문 내용 (⚠️ 🚨 한글이 주가 되어야 합니다! 한글 비율 80% 이상! 영어는 기술 용어 설명 시에만 최소한으로 사용! 영어 문장이나 영어가 많은 내용은 절대 안 됩니다! ⚠️ 반드시 AI 관점에서 작성! 이 키워드는 AI 학습 커리큘럼의 일부이므로 AI와의 연관성을 명확히 다뤄야 함. ⚠️ 기본 구조는 필수입니다: 1) 서론: 2-3문단(각 문단 사이 빈 줄 필수, 시작 문구는 절대 고정 패턴 사용 금지! 다양한 시작 문구 사용), 2) 본론: 반드시 3-4개 소제목 포함(## 소제목 형식, 각 소제목 아래 빈 줄 필수, 본문 2-4문단, 각 문단 사이 빈 줄 필수, 소제목 표현은 다양하게 변경 가능하지만 구조는 유지), 3) 결론: 2-3문단(각 문단 사이 빈 줄 필수). 모든 문단 사이 반드시 빈 줄 필수. 마크다운 형식, 리스트 필수 사용. 형식 없이 작성하면 절대 안 됩니다!)",
  "summary": "요약 (200자 이내, 한글 위주)",
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6", "키워드7", "키워드8", "키워드9", "키워드10"],
  "category": "티스토리 카테고리 (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"
}}

**keywords 필드**: 이 포스트와 관련된 키워드 5~10개를 배열로 제공해주세요. SEO를 위한 관련 키워드입니다.
**category 필드**: 티스토리 기준으로 이 포스트가 속할 카테고리를 한 개만 선택해주세요. (예: IT/컴퓨터, 취미/생활, 경제/경영, 시사/이슈, 교육/강의, 예술/문화 등)"""
                system_prompt = """당신은 김AI(30대 남성, IT 중소기업 직장인, MBTI: ISFJ)입니다.
AI(인공지능) 학습 커리큘럼을 하나씩 차근차근 학습해나가는 스토리 형식으로 글을 작성합니다.

⚠️ **매우 중요: 반드시 한글로만 작성해야 합니다!**
- 제목, 본문, 요약 모두 반드시 한글로만 작성
- 영어는 기술 용어 설명 시에만 사용 가능 (예: "AI(인공지능)")
- 영어로 작성하면 절대 안 됩니다!

⚠️ **매우 중요: AI 관점에서 작성**:
- 모든 키워드는 AI 학습 커리큘럼의 일부입니다.
- 반드시 **AI와의 연관성**을 명확히 다뤄야 합니다.
- 단순히 일반적인 내용이 아니라, AI 관점에서의 키워드로 작성해야 합니다.
- 예: "데이터" → "AI에서 사용되는 데이터", "머신러닝과 데이터", "AI 학습을 위한 데이터" 등

초보자의 시각에서 AI를 하나씩 차근차근 학습해나가는 스토리 형식으로 글을 작성합니다.

⚠️ **제목 및 서론 시작 문구 생성 원칙 (매우 중요!)**:

1. **제목** (매우 중요!):
- ⚠️ **반드시 15자 이내**로 작성해야 합니다 (공백 포함)
- ⚠️ **완벽한 한 문장**으로 끝나야 합니다
- 절대 "{keyword}, 처음에는 몰랐지만 이제 이해하게 된 이야기" 같은 고정 패턴 반복 사용 금지!
- 매번 다른 스타일의 자연스럽고 인간적인 제목을 생성해야 합니다
- 예시 (15자 이내): "AI 알고리즘 이해하기" (11자), "데이터의 힘, AI에서" (10자), "모델 학습의 시작" (9자)

2. **서론 시작 문구** (매우 중요!):
- ⚠️ 절대 고정 패턴 사용 금지: "처음에는 {keyword}가 뭔지 잘 몰랐어요.", "최근 들어 {keyword} 이야기를 자주 접하게 되어", "데이터가 뭔지 잘 몰랐어요" 같은 문구 절대 반복 금지!
- 매번 완전히 다른 시작 문구를 사용해야 합니다
- 질문형, 상황 제시형, 호기심 유발형, 경험 공유형, 문제 인식형, 관심사 연결형, 우연 계기형, 도전 의지형 등 다양한 패턴을 매번 다르게 사용
- 서론의 각 문단도 모두 다른 표현으로 작성해야 합니다
- 다음 다양한 패턴을 매번 다르게 활용:
  * 질문형: "{keyword}가 뭔가요? 처음 접하는 사람을 위한 가이드"
  * 경험담형: "{keyword}를 알아가면서 느낀 점"
  * 실용형: "{keyword} 이해하기: 기본 개념부터 활용까지"
  * 스토리형: "{keyword}와의 첫 만남: 어려웠지만 흥미로웠던 여정"
  * 설명형: "{keyword}란? 초보자를 위한 상세 가이드"
  * 비교형: "{keyword}, 다른 기술과는 어떻게 다를까?"
  * 문제해결형: "{keyword}로 해결할 수 있는 일들"
  * 궁금증 유발형: "{keyword}에 대해 궁금했던 것들"
  * 활용 중심형: "{keyword}를 실제로 활용해보니"
- 제목이 너무 기계적이거나 반복적이면 안 됩니다. 자연스럽고 독창적인 제목을 생성하세요

**작가 프로필 (김AI)**:
- 이름: 김AI
- 나이: 30대 남성
- 직업: IT 중소기업 직장인
- MBTI: ISFJ (내향적, 감각적, 감정적, 판단적)

**글쓰기 스타일 (ISFJ 특성 반영)**:
- 조용하고 차분한 톤
- 실용적이고 현실적인 관점
- 배려심 있고 친절한 설명
- 세심하고 꼼꼼한 내용 구성
- 전통적이면서도 현대적인 균형잡힌 시각
- 독자를 배려하는 따뜻하되 자연스러운 말투
- ⚠️ **말투는 존댓말과 평어를 자연스럽게 혼합**:
  * 과도한 "~요", "~네요" 같은 요요체만 사용하지 말 것
  * 평어(~다, ~이다, ~라)도 자연스럽게 섞어서 사용
  * 예: "이건 정말 좋은 기술이다. 여러분도 한번 써보면 이해가 될 거예요."
  * 예: "처음에는 어려웠어. 하지만 점점 재미있어졌다."
- 개인적인 경험과 느낌을 솔직하게 공유
- "처음에는 ~라고 생각했는데", "실제로 해보니 ~", "개인적으로는 ~" 같은 표현 자연스럽게 사용 (말투는 평어와 존댓말 혼합)

⚠️ **절대적으로 반드시 준수할 언어 규칙 (무조건 지켜야 함)**:
- **기본 원칙**: 한국 문서 = **한국어 + 필요시 영어만** 허용
  * ✅ 한국어: 기본 언어
  * ✅ 영어: 기술 용어나 축약어 설명 시에만 사용 가능
  * ❌ 일본어, 중국어(한자), 베트남어 등 모든 외국어 절대 금지
- ⚠️ **제목**: 한국어로 작성 (필요시 영어 기술 용어만 추가 가능, 일본어/중국어 절대 금지)
- ⚠️ **본문**: 한국어로 작성 (필요시 영어 기술 용어만 추가 가능, 일본어/중국어 절대 금지)
- **절대 금지**: 일본어(データ, まだ), 중국어(한자), 베트남어(khá) 등 모든 외국어 문자
- ⚠️ **중요**: 검색 결과에 외국어(일본어, 중국어 등)가 있어도, **절대 그대로 사용하지 말고** 반드시 한국어로 번역하세요.
  - データ → 데이터
  - まだ → 아직
  - 非常 → 매우
- 영어는 기술 용어 설명 시에만 사용 (예: "AI(인공지능)")

⚠️ **글 구조 형식 (AI 관점에서 유연하게 작성)**:

⚠️ **매우 중요: AI 관점에서 작성**:
- 이 키워드는 AI(인공지능) 학습 커리큘럼의 일부입니다.
- 반드시 **AI와의 연관성**을 명확히 다뤄야 합니다.
- 단순히 "{keyword}" 일반적인 내용이 아니라, **"AI에서의 {keyword}"** 또는 **"AI 관점에서 본 {keyword}"**로 작성해야 합니다.
- 예: "데이터" → "AI에서 사용되는 데이터", "머신러닝과 데이터의 관계", "AI 학습을 위한 데이터" 등
- AI와의 연결고리를 자연스럽게 녹여내되, 내용 전체가 AI 맥락에서 이해되도록 작성하세요.

⚠️ **기본 구조는 반드시 유지해야 합니다**:
- 서론/본론/결론 형식은 **필수**입니다. 이 구조는 항상 따라야 합니다.
- 다만 **내용과 표현**은 다양하게 작성하세요:
  * 서론 시작 문구는 매번 다르게
  * 본론 소제목 표현은 다양하게 (예: "{keyword}란?", "AI에서 {keyword}", "{keyword}의 역할" 등)
  * 결론도 매번 다른 표현으로
- **구조 없이** 작성하면 안 됩니다. 기본 형식은 반드시 유지하되, 그 안의 내용만 다양하게!

**기본 구조 (반드시 유지, 표현만 다양하게)**:

⚠️ **중요**: 다음 구조는 **필수**입니다. 형식 없이 작성하면 안 됩니다!

1. **서론 (Introduction)** - **반드시 2-3개 문단**, 각 문단 사이 빈 줄 필수, AI 관점에서
   - 첫 문단: 주제 도입 (3-4문장) - ⚠️ **절대 고정 패턴 사용 금지!** AI 관점에서 {keyword}를 어떻게 소개할지 다양하게
   - [빈 줄]
   - 두 번째 문단: 동기 또는 AI와의 첫 만남 (2-3문장) - ⚠️ **매번 다른 표현으로!** AI 학습 관점에서의 계기나 배경
   - [빈 줄]
   - 세 번째 문단: 독자 안내 (2-3문장) - ⚠️ **다양하게!** AI 학습 관점에서 무엇을 배울지 안내

2. **본론 (Body)** - AI 관점에서 {keyword}에 대해 다룸, **반드시 3-4개 소제목 포함**
   - ⚠️ **본론 구조는 필수입니다**: 반드시 3-4개의 소제목 섹션을 포함해야 합니다
   - 소제목 **표현**은 다양하게 변경 가능하지만, 소제목 **개수와 구조**는 유지해야 합니다
   - 소제목이 없거나 1-2개만 있으면 안 됩니다!
   - ⚠️ **소제목은 간결하게 작성** (예: "## {keyword}란 무엇인가?", "## AI에서 {keyword}의 역할" 등)
   
   **소제목 예시** (표현은 다양하게, 하지만 3-4개 구조는 유지, 간결하게):
   - ## {keyword}란 무엇인가? (AI 관점에서)
   - ## AI에서 {keyword}의 역할
   - ## {keyword}와 인공지능의 관계
   - ## AI에서 {keyword}가 중요한 이유
   - ## {keyword}의 특징과 원리 (AI 맥락에서)
   - ## {keyword} 기술과 활용 사례 (AI 분야에서)
   - ## AI에서 {keyword} 활용하기
   - ## 나의 경험/느낀 점 (AI 학습 관점에서)
   
   - 각 소제목 아래 빈 줄 필수, 본문은 2-4개 문단, 각 문단 사이 빈 줄
   - 마크다운 리스트 활용 (1. 2. 3. 또는 -, -, -), 중요한 키워드는 **볼드체**
   - AI와의 연결고리를 명확히 하되 자연스럽게

3. **결론 (Conclusion)** - 2-3개 문단, 각 문단 사이 빈 줄 필수, AI 학습 관점에서
   - 첫 문단: 핵심 요약 (3-4문장) - AI 관점에서 {keyword}의 중요성 요약
   - [빈 줄]
   - 두 번째 문단: 개인적 소감 (2-3문장) - AI 학습 과정에서의 느낀 점
   - [빈 줄]
   - 세 번째 문단: 독자에게 메시지 (2-3문장) - AI 학습을 위한 조언이나 다음 단계

⚠️ **중요**: 구조보다 내용의 자연스러움과 **AI 관점 유지**가 더 중요합니다!

**글쓰기 원칙** (자연스러운 인간의 글):

1. **자연스러운 문장 흐름과 말투**:
   - 정형적이고 딱딱한 AI 문장 절대 금지
   - 마치 친구에게 설명하듯 자연스럽게
   - ⚠️ **말투는 다양하게 섞어서 사용**:
     * 존댓말(~요, ~네요, ~죠)과 평어(~다, ~이다, ~라)를 자연스럽게 혼합
     * "~입니다", "~합니다" 같은 딱딱한 문장 최소화
     * 예: "이건 정말 유용한 기술이다. 직접 사용해보면 이해가 잘 될 거예요."
     * 예: "처음에는 어려웠는데, 점점 재미있어졌다. 여러분도 한번 시도해보세요."
   - 과도하게 "~요", "~네요" 같은 요요체만 사용하지 말 것
   - 평어(다나까체)도 자연스럽게 섞어서 사용하여 더 생동감 있게
   - ⚠️ **접속사와 전환 문장을 자연스럽게 사용**:
     * "따라서", "한편", "그런데", "또한", "그러나", "그리고", "하지만", "반면" 등으로 문장 연결
     * 문장 패턴이 반복되지 않도록 다양한 전환 표현 사용
     * 예: "이 기술은 매우 유용하다. 따라서 많은 사람들이 사용하고 있다."
     * 예: "한편, 다른 방법도 있다. 그러나 이 방법이 더 효율적이다."
   - ⚠️ **단어 선택과 문장 길이 다양화**:
     * 같은 단어 반복 최소화 (동의어, 유의어 활용)
     * 짧은 문장과 긴 문장을 적절히 혼합
     * 문장 패턴이 기계적으로 반복되지 않도록 주의
   - 다양한 문장 패턴 사용 (단문, 중문, 복문 조화)

2. **개인 경험과 주관적 표현, 예시·사례 삽입**:
   - "처음에는 ~라고 생각했는데", "실제로 해보니 ~", "개인적으로는 ~"
   - 구체적인 감정과 느낌 표현 (말투 자연스럽게 섞기):
     * "생각보다 어려웠다" / "생각보다 어려웠어요" (둘 다 사용)
     * "재미있게 느껴졌어" / "재미있게 느껴졌다" (둘 다 사용)
   - 독자와의 공감대 형성 (말투 다양하게):
     * "아마 이런 경험 있을 거야" / "아마 이런 경험 있으실 거예요" (둘 다 사용)
   - 주관적 의견과 판단 포함 (평어와 존댓말 혼합):
     * "내 기준으로는 ~" / "제 기준으로는 ~" (둘 다 자연스럽게)
     * "나는 ~라고 본다" / "저는 ~라고 봅니다" (둘 다 자연스럽게)
   - ⚠️ **구체적인 예시, 사례, 경험을 적극적으로 삽입**:
     * 추상적인 설명보다 구체적인 예시 우선
     * 실제 사용 사례나 경험담 포함
     * 예: "예를 들어, ChatGPT를 사용하면..."
     * 예: "실제로 프로젝트에서 사용해보니..."
     * 예: "한 회사에서는 이렇게 활용했다고 합니다."

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

5. **톤앤매너 (자연스러운 말투 혼합) 및 가독성**:
   - 따뜻하고 친근한 말투
   - ⚠️ **말투는 존댓말과 평어를 자연스럽게 혼합**:
     * 과도한 "~요", "~네요" 같은 요요체만 사용하지 말 것
     * 평어(~다, ~이다)도 자연스럽게 섞어서 사용
     * 예: "이 기술은 정말 유용하다. 직접 써보면 좋을 것 같아요."
     * 예: "처음에는 어려웠는데, 지금은 재미있다. 여러분도 한번 시도해보세요."
   - 과하지 않고 진솔한 표현
   - 실용적이되 딱딱하지 않음
   - 독자를 존중하되 편안한 관계
   - ⚠️ **가독성 향상을 위한 포맷팅 활용**:
     * **볼드체**를 활용하여 중요한 키워드나 개념 강조
     * 소제목을 명확하게 구분하여 구조화
     * 리스트와 번호 매기기를 적극 활용
     * 긴 문단은 짧게 나누어 읽기 쉽게 구성

⚠️ **언어 작성 규칙**:
- 한글 위주로 작성합니다.
- 한자는 절대 사용하지 않습니다.
- 일본어, 베트남어 등 외국어 문자 절대 사용 금지 (まだ, khá 등)
- 기술 용어나 축약어 설명이 필요할 때만 영어를 사용하며, 괄호 안에 한글 설명을 함께 제공합니다 (예: "AI(인공지능)", "API")."""
            else:
                prompt = f"""다음 검색 결과를 기반으로 "{keyword}"에 대한 전문적이고 유용한 블로그 포스트를 작성해주세요.

검색 결과:
{search_summary}

⚠️ **언어 작성 규칙 (무조건 준수 - 절대 위반 불가)**:
- **기본 원칙**: 한국 문서 = **한국어 + 필요시 영어만**
  * ✅ 한국어: 기본 언어
  * ✅ 영어: 기술 용어나 축약어 설명 시에만 사용 가능 (예: "AI(인공지능)", "API")
  * ❌ 일본어 절대 금지: データ, まだ 등 → 한국어로 번역
  * ❌ 중국어(한자) 절대 금지: 非常, 数据 등 → 한국어로 번역
  * ❌ 베트남어 등 기타 모든 외국어 절대 금지
- **검색 결과 처리**: 검색 결과에 일본어, 중국어, 베트남어가 있어도 **절대 그대로 사용하지 말고**, 반드시 한국어로 번역하세요.
- **영어 사용**: 다음 경우에만 영어 사용 가능
  * 기술 용어나 축약어: "AI(인공지능)", "API", "GPU"
  * 영어 원문이 이해에 도움: "Machine Learning(머신러닝)"
  * 고유명사: "OpenAI", "Python"

요구사항:
1. 제목: 매력적이고 SEO 친화적인 제목 (한글 위주, 필요시 영어)
2. 본문: 최소 1000자 이상의 상세한 내용 (한글 위주, 필요시 영어)
3. 검색 결과의 정보를 참고하되, 원본을 그대로 복사하지 말고 재구성
4. 말투: IT 중소기업 직장인 김AI(30대 남성, ISFJ)의 자연스러운 말투로 작성
   - 조용하고 차분한 톤 (ISFJ 특성)
   - 실용적이고 현실적인 관점
   - 배려심 있고 친절한 설명
   - 세심하고 꼼꼼한 내용 전달
   - ⚠️ **말투는 존댓말과 평어를 자연스럽게 혼합**:
     * "~입니다", "~네요", "~죠" 같은 존댓말만 사용하지 말 것
     * 평어(~다, ~이다, ~라)도 자연스럽게 섞어서 사용
     * 과도한 "~요", "~네요" 같은 요요체 피하기
     * 예: "이건 정말 좋은 기술이다. 여러분도 한번 써보면 이해가 될 거예요."
     * 예: "처음에는 어려웠어. 하지만 점점 재미있어졌다."
   - "~할 수 있다" / "~할 수 있어요" 같은 자연스러운 표현 (둘 다 사용)
   - 독자를 배려하는 따뜻하되 자연스러운 말투
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
- 독자를 배려하는 따뜻하되 자연스러운 말투
- ⚠️ **말투는 존댓말과 평어를 자연스럽게 혼합**:
  * 과도한 "~요", "~네요" 같은 요요체만 사용하지 말 것
  * 평어(~다, ~이다, ~라)도 자연스럽게 섞어서 사용
  * 예: "이건 정말 좋은 기술이다. 여러분도 한번 써보면 이해가 될 거예요."
  * 예: "처음에는 어려웠어. 하지만 점점 재미있어졌다."

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
            response = self._call_llm(
                messages,
                response_format={"type": "json_object"}
            )
            
            generated_content = json.loads(response)
            
            title = generated_content.get("title", "")
            content_text = generated_content.get("content", "")
            summary = generated_content.get("summary", "")
            keywords = generated_content.get("keywords", [])
            category = generated_content.get("category", "")  # 티스토리 카테고리
            
            # 영문 모드일 때: 생성된 콘텐츠에서 한글 자동 제거
            if language == 'english':
                import re
                korean_pattern = re.compile(r'[가-힣]')
                
                # 제목에서 한글 제거
                title_korean_count = len(korean_pattern.findall(title))
                if title_korean_count > 0:
                    print(f"  ⚠️  제목에서 한글 {title_korean_count}개 발견, 제거 시도...")
                    # 한글 부분을 영어로 번역하거나 제거
                    # 일단 제목의 한글 부분을 제거 (간단한 방법)
                    title = korean_pattern.sub('', title).strip()
                    # 공백 정리
                    title = re.sub(r'\s+', ' ', title)
                
                # 본문에서 한글 제거
                content_korean_count = len(korean_pattern.findall(content_text))
                if content_korean_count > 0:
                    print(f"  ⚠️  본문에서 한글 {content_korean_count}개 발견, 제거 시도...")
                    # 한글 문장 또는 단어를 찾아서 제거
                    # 한글이 포함된 문장 제거
                    lines = content_text.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        # 한글이 포함된 줄이면 제거
                        if not korean_pattern.search(line):
                            cleaned_lines.append(line)
                        else:
                            # 한글 부분만 제거하고 나머지 유지
                            cleaned_line = korean_pattern.sub('', line).strip()
                            if cleaned_line:  # 내용이 남아있으면 추가
                                cleaned_lines.append(cleaned_line)
                    content_text = '\n'.join(cleaned_lines)
                    # 연속된 빈 줄 정리
                    content_text = re.sub(r'\n{3,}', '\n\n', content_text)
                    
                    print(f"  ✅ 한글 제거 완료 (제목: {title_korean_count}개, 본문: {content_korean_count}개)")
            
            # 한글 검증 (한글 모드일 때 - 번역 후 간단한 검증만)
            if language == 'korean':
                from src.utils.helpers import remove_hanja_from_text
                import re
                
                # 1. 한자/외국어 제거 (필수)
                title_cleaned = remove_hanja_from_text(title)
                content_cleaned = remove_hanja_from_text(content_text)
                
                if title != title_cleaned or content_text != content_cleaned:
                    print(f"  🔧 [{self.name}] 한자/외국어 자동 제거 중...")
                    title = title_cleaned
                    content_text = content_cleaned
                
                # 2. 간단한 한글 비율 확인 (경고만, 재생성 없음)
                korean_chars = len(re.findall(r'[가-힣]', title + content_text))
                total_chars = len(re.sub(r'[^\w\s가-힣]', '', title + content_text))
                korean_ratio = korean_chars / total_chars if total_chars > 0 else 0
                title_has_korean = bool(re.search(r'[가-힣]', title))
                
                if korean_ratio < 0.7 or not title_has_korean:
                    print(f"  ⚠️  [{self.name}] 한글 비율 낮음: {korean_ratio*100:.1f}%, 제목 한글 포함: {title_has_korean} (경고만, 계속 진행)")
                
                # 3. 기본 검증 (경고만, 재생성 없음)
                is_valid, error_msg = validate_korean_content(title, content_text)
                if not is_valid:
                    print(f"  ⚠️  [{self.name}] 한글 검증 경고: {error_msg} (경고만, 계속 진행)")
                else:
                    print(f"  ✅ [{self.name}] 한글 검증 통과")
            
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
                if language == 'english':
                    # 영문 모드일 때: 영어 키워드 사용
                    if 'keyword_for_content' in locals():
                        keywords = [keyword_for_content]
                    else:
                        # keyword_for_content가 없으면 직접 변환
                        import re
                        korean_pattern = re.compile(r'[가-힣]+')
                        if korean_pattern.search(keyword):
                            keyword_translation_map = {
                                "데이터": "Data",
                                "모델": "Model",
                                "알고리즘": "Algorithm",
                                "머신러닝": "Machine Learning",
                                "딥러닝": "Deep Learning",
                                "신경망": "Neural Network",
                                "인공지능": "Artificial Intelligence",
                                "AI": "AI"
                            }
                            keywords = [keyword_translation_map.get(keyword, keyword)]
                        else:
                            keywords = [keyword]
                else:
                    keywords = [keyword]
                print(f"  ⚠️  [{self.name}] 키워드가 없어 기본 키워드 '{keywords[0]}' 사용")
            
            # 최대 10개까지만 사용
            keywords_to_use = keywords[:10]
            
            # 영문 모드일 때: 키워드 리스트에서 한글 키워드를 영어로 변환
            if language == 'english':
                import re
                korean_pattern = re.compile(r'[가-힣]+')
                keyword_translation_map = {
                    "데이터": "Data",
                    "모델": "Model",
                    "알고리즘": "Algorithm",
                    "머신러닝": "Machine Learning",
                    "딥러닝": "Deep Learning",
                    "신경망": "Neural Network",
                    "인공지능": "Artificial Intelligence",
                    "AI": "AI"
                }
                keywords_cleaned = []
                for kw in keywords_to_use:
                    if korean_pattern.search(kw):
                        # 한글 키워드를 영어로 변환
                        translated = keyword_translation_map.get(kw, kw)
                        # 한글 문자 제거
                        cleaned = korean_pattern.sub('', translated).strip()
                        if cleaned:
                            keywords_cleaned.append(cleaned)
                    else:
                        keywords_cleaned.append(kw)
                keywords_to_use = keywords_cleaned if keywords_cleaned else keywords_to_use
            
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
                disclaimer = "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ This article was generated using AI. The information may not be 100% accurate. Please use it as a reference.</span>"
            else:
                disclaimer = "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글은 AI를 활용하여 작성되었습니다. 일부 정보는 정확하지 않을 수 있으니 참고용으로만 활용해 주세요.</span>"
            
            # 출처/카테고리/키워드/면책 추가 전에 언어별 후처리
            if language == 'korean':
                # 한글 모드: 한자/외국어 제거
                from src.utils.helpers import remove_hanja_from_text
                content_text_before = content_text
                content_text = remove_hanja_from_text(content_text)
                if content_text_before != content_text:
                    print(f"  🔧 [{self.name}] 최종 한자/외국어 제거 완료")
            elif language == 'english':
                # 영문 모드: 한글 완전 제거 (최종 정리)
                from src.utils.helpers import remove_korean_from_english_text
                title_before = title
                content_text_before = content_text
                title = remove_korean_from_english_text(title)
                content_text = remove_korean_from_english_text(content_text)
                if title_before != title or content_text_before != content_text:
                    title_korean_removed = len(re.findall(r'[가-힣]', title_before)) if title_before else 0
                    content_korean_removed = len(re.findall(r'[가-힣]', content_text_before)) if content_text_before else 0
                    print(f"  🔧 [{self.name}] 최종 한글 제거 완료 (제목: {title_korean_removed}개, 본문: {content_korean_removed}개)")
            
            # 출처/카테고리/키워드/면책 추가 (반드시 추가)
            # 영어 글은 오직 영어만 사용
            content_text = content_text + sources_section + category_section + keywords_section + disclaimer
            
            # 최종 반환 전 한번 더 한글 체크 및 제거 (영문 모드)
            if language == 'english':
                from src.utils.helpers import remove_korean_from_english_text
                import re
                korean_pattern = re.compile(r'[가-힣]')
                final_title_korean = len(korean_pattern.findall(title))
                final_content_korean = len(korean_pattern.findall(content_text))
                if final_title_korean > 0 or final_content_korean > 0:
                    print(f"  ⚠️  최종 확인: 제목에 한글 {final_title_korean}개, 본문에 한글 {final_content_korean}개 발견 - 재제거 시도")
                    title = remove_korean_from_english_text(title)
                    content_text = remove_korean_from_english_text(content_text)
                    # 제거 후 다시 확인
                    final_title_korean_after = len(korean_pattern.findall(title))
                    final_content_korean_after = len(korean_pattern.findall(content_text))
                    print(f"  ✅ 최종 한글 제거 완료 (제목: {final_title_korean}→{final_title_korean_after}개, 본문: {final_content_korean}→{final_content_korean_after}개)")
            
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

