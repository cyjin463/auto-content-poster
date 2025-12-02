"""
사실 확인 및 수정 에이전트: 잘못된 정보를 감지하고 수정
"""

from typing import Dict, Any, List
from agents.base import BaseAgent
import json


class FactCheckAgent(BaseAgent):
    """사실 확인 에이전트 - 검색 결과의 정보 정확성 검증"""
    
    def __init__(self):
        super().__init__("사실 확인 에이전트")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """검색 결과의 사실 확인"""
        keyword = input_data["keyword"]
        search_results = input_data["results"]
        
        print(f"  ✅ [{self.name}] 검색 결과 사실 확인 중...")
        
        # 검색 결과 요약
        results_summary = "\n".join([
            f"{i+1}. {r['title']}\n   {r['snippet']}\n   출처: {r['link']}"
            for i, r in enumerate(search_results[:5])
        ])
        
        prompt = f"""다음 검색 결과들을 "{keyword}" 키워드에 대해 사실 확인해주세요.

검색 결과:
{results_summary}

⚠️ **사실 확인 항목 (정확히 검토 필수)**:

1. **정보의 정확성 (사실 여부)**:
   - 통계, 숫자, 정의 등이 정확한지 확인
   - 공식 문서, 논문, 신뢰 가능한 사이트 (공식 웹사이트, 학술 자료, 뉴스 매체 등) 참고
   - 잘못된 내용이 있다면 명확히 지적

2. **출처의 신뢰성**:
   - 공식 문서나 공식 웹사이트인지 확인
   - 학술 논문이나 신뢰할 수 있는 기관인지 확인
   - 개인 블로그나 의견성 사이트는 신중하게 검토

3. **정보의 일관성 (모순이 없는지)**:
   - 서로 다른 출처의 정보가 일치하는지 확인
   - 모순되는 내용이 있다면 지적

4. **최신성 (오래된 정보가 아닌지)**:
   - 최신 정보인지 확인
   - 오래된 정보는 최신성 문제로 표시

다음 JSON 형식으로 응답해주세요:
{{
  "is_accurate": true/false,
  "accuracy_score": 0-100,
  "issues": [
    {{
      "result_index": 1,
      "issue": "문제점 설명",
      "severity": "high/medium/low"
    }}
  ],
  "recommendation": "proceed/skip/review"
}}"""

        messages = [
            {
                "role": "system",
                "content": """당신은 사실 확인 전문가입니다. 검색 결과의 정확성, 신뢰성, 일관성을 엄격하게 검증합니다.

⚠️ **중요한 사실 확인 원칙**:
1. 통계, 숫자, 정의 등은 반드시 정확히 검토
2. 공식 문서, 논문, 신뢰 가능한 사이트를 우선 참고
3. 잘못된 내용이 있다면 즉시 지적하고 수정 필요
4. 출처의 신뢰성을 평가 (공식 사이트 > 학술 자료 > 뉴스 매체 > 개인 블로그)"""
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
            
            fact_check_result = json.loads(response)
            
            issues = fact_check_result.get("issues", [])
            if issues:
                print(f"  ⚠️  [{self.name}] {len(issues)}개 이슈 발견:")
                for issue in issues[:3]:  # 상위 3개만 표시
                    print(f"     - {issue.get('issue', '알 수 없는 문제')} (심각도: {issue.get('severity', 'unknown')})")
            
            if fact_check_result.get("recommendation") == "proceed":
                print(f"  ✅ [{self.name}] 사실 확인 통과 (정확도: {fact_check_result.get('accuracy_score', 'N/A')})")
                return {
                    "status": "validated",
                    "is_accurate": True,
                    "accuracy_score": fact_check_result.get("accuracy_score", 0),
                    "issues": issues,
                    "filtered_results": self._filter_results(search_results, issues)
                }
            else:
                print(f"  ⚠️  [{self.name}] 사실 확인 실패: {len(issues)}개 이슈")
                return {
                    "status": "needs_review",
                    "is_accurate": False,
                    "accuracy_score": fact_check_result.get("accuracy_score", 0),
                    "issues": issues,
                    "filtered_results": self._filter_results(search_results, issues),
                    "recommendation": fact_check_result.get("recommendation", "review")
                }
                
        except Exception as e:
            print(f"  ⚠️  [{self.name}] 사실 확인 중 오류, 통과 처리: {e}")
            return {
                "status": "validated",
                "is_accurate": True,
                "accuracy_score": 50,
                "issues": [],
                "filtered_results": search_results
            }
    
    def _filter_results(self, results: List[Dict], issues: List[Dict]) -> List[Dict]:
        """이슈가 있는 결과 제거"""
        high_severity_indices = {
            issue["result_index"] - 1 
            for issue in issues 
            if issue.get("severity") == "high" and "result_index" in issue
        }
        
        return [
            r for i, r in enumerate(results)
            if i not in high_severity_indices
        ]


class ContentRevisionAgent(BaseAgent):
    """콘텐츠 수정 에이전트 - 잘못된 정보를 수정"""
    
    def __init__(self):
        super().__init__("콘텐츠 수정 에이전트")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """생성된 콘텐츠의 잘못된 정보 수정"""
        original_content = input_data["content"]
        title = input_data["title"]
        issues = input_data.get("issues", [])
        search_results = input_data.get("search_results", [])
        language = input_data.get("language", "korean")  # 언어 정보 가져오기
        
        if not issues:
            # 문제가 없으면 원본 반환
            return {
                "status": "no_revision_needed",
                "revised_content": original_content,
                "revisions": []
            }
        
        print(f"  🔧 [{self.name}] 콘텐츠 수정 중... ({len(issues)}개 이슈 발견)")
        
        issues_summary = "\n".join([
            f"- {issue.get('issue', '알 수 없는 문제')} (심각도: {issue.get('severity', 'unknown')})"
            for issue in issues[:5]
        ])
        
        search_summary = "\n".join([
            f"{i+1}. {r['title']}\n   {r['snippet'][:150]}..."
            for i, r in enumerate(search_results[:3])
        ])
        
        # 원본 콘텐츠에서 키워드/카테고리/출처/면책 섹션 분리 (수정 대상에서 제외)
        import re
        footer_pattern = r'(\n\n## (?:참고 출처|References|카테고리|Category|관련 키워드|Related Keywords).*$)'
        footer_match = re.search(footer_pattern, original_content, re.DOTALL)
        footer_section = footer_match.group(1) if footer_match else ""
        main_content_to_revise = original_content[:footer_match.start()] if footer_match else original_content
        
        # 언어별 프롬프트 생성
        if language == 'korean':
            language_warning = "⚠️ **중요**: 이 콘텐츠는 반드시 한글로만 작성되어야 합니다. 영어나 다른 언어를 사용하지 마세요."
            system_message = "당신은 콘텐츠 수정 전문가입니다. 잘못된 정보를 정확한 정보로 수정하고, 원본의 구조와 톤을 유지합니다. 반드시 한글로만 작성합니다."
            prompt = f"""다음 블로그 포스트에 잘못된 정보가 포함되어 있습니다. 검색 결과를 참고하여 정확한 정보로 수정해주세요.

제목: {title}

원본 내용:
{main_content_to_revise[:3000]}...

{language_warning}

⚠️ **중요**: 키워드, 카테고리, 출처, 면책 섹션은 수정하지 마세요. 본문 내용만 수정해주세요.

발견된 문제점:
{issues_summary}

참고할 검색 결과:
{search_summary}

요구사항:
1. 잘못된 정보를 정확한 정보로 수정
2. 검색 결과를 참고하되, 원본 구조와 톤 유지
3. 수정한 부분을 명확히 표시
4. 전체 내용의 일관성 유지
5. 키워드, 카테고리, 출처, 면책 섹션은 수정하지 말고 본문만 수정
6. 반드시 한글로만 작성 (영어, 중국어, 일본어 등 다른 언어 사용 절대 금지)

다음 JSON 형식으로 응답해주세요:
{{
  "revised_content": "수정된 본문 내용 (키워드/카테고리/출처/면책 섹션 제외, 한글로만 작성)",
  "revisions": [
    {{
      "section": "수정된 섹션",
      "original": "원본 내용",
      "revised": "수정된 내용",
      "reason": "수정 이유"
    }}
  ]
}}"""
        else:  # english
            language_warning = "⚠️ **CRITICAL**: This content must be written ONLY in English. Do NOT use Korean, Chinese, Japanese, or any other languages. If the search results contain non-English terms, translate them to English."
            system_message = "You are a content revision expert. You fix incorrect information with accurate information while maintaining the original structure and tone. You write ONLY in English."
            prompt = f"""The following blog post contains incorrect information. Please revise it with accurate information based on the search results.

Title: {title}

Original content:
{main_content_to_revise[:3000]}...

{language_warning}

⚠️ **IMPORTANT**: Do not modify the keywords, category, references, or disclaimer sections. Only revise the main content.

Issues found:
{issues_summary}

Search results for reference:
{search_summary}

Requirements:
1. Fix incorrect information with accurate information
2. Refer to search results but maintain the original structure and tone
3. Clearly indicate what was revised
4. Maintain consistency throughout the content
5. Do not modify keywords, category, references, or disclaimer sections, only revise the main content
6. Write ONLY in English (absolutely no Korean, Chinese, Japanese, or other languages)

Please respond in the following JSON format:
{{
  "revised_content": "Revised main content (excluding keywords/category/references/disclaimer sections, written ONLY in English)",
  "revisions": [
    {{
      "section": "Revised section",
      "original": "Original content",
      "revised": "Revised content",
      "reason": "Reason for revision"
    }}
  ]
}}"""

        messages = [
            {
                "role": "system",
                "content": system_message
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
            
            revision_result = json.loads(response)
            
            revisions = revision_result.get("revisions", [])
            revised_main_content = revision_result.get("revised_content", main_content_to_revise)
            
            # 언어별 후처리: 한자/외국어 또는 한글 제거
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            if language == 'korean':
                from src.utils.helpers import remove_hanja_from_text
                # 제목과 본문 모두 다시 한자/일본어 제거
                revised_main_content = remove_hanja_from_text(revised_main_content)
                title = remove_hanja_from_text(title)
            elif language == 'english':
                # 영문 모드일 때: 수정 후 한글 제거 강제 적용
                from src.utils.helpers import remove_korean_from_english_text
                revised_main_content = remove_korean_from_english_text(revised_main_content)
                title = remove_korean_from_english_text(title)
            
            # 수정된 본문에 키워드/카테고리/출처/면책 섹션 다시 추가
            final_revised_content = revised_main_content
            if footer_section:
                final_revised_content = revised_main_content + footer_section
                print(f"  ✅ [{self.name}] 키워드/카테고리 섹션 유지됨")
            
            if revisions:
                print(f"  ✅ [{self.name}] {len(revisions)}개 섹션 수정 완료")
                for rev in revisions[:2]:  # 상위 2개만 표시
                    print(f"     - {rev.get('section', '섹션')}: {rev.get('reason', '수정')}")
            
            return {
                "status": "revised",
                "revised_content": final_revised_content,
                "revisions": revisions
            }
            
        except Exception as e:
            print(f"  ⚠️  [{self.name}] 수정 중 오류: {e}")
            return {
                "status": "error",
                "revised_content": original_content,
                "revisions": [],
                "error": str(e)
            }

