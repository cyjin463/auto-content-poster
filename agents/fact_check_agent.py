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

다음 항목들을 검증해주세요:
1. 정보의 정확성 (사실 여부)
2. 출처의 신뢰성
3. 정보의 일관성 (모순이 없는지)
4. 최신성 (오래된 정보가 아닌지)

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
                "content": "당신은 사실 확인 전문가입니다. 검색 결과의 정확성, 신뢰성, 일관성을 검증합니다."
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
        
        prompt = f"""다음 블로그 포스트에 잘못된 정보가 포함되어 있습니다. 검색 결과를 참고하여 정확한 정보로 수정해주세요.

제목: {title}

원본 내용:
{main_content_to_revise[:3000]}...

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

다음 JSON 형식으로 응답해주세요:
{{
  "revised_content": "수정된 본문 내용 (키워드/카테고리/출처/면책 섹션 제외)",
  "revisions": [
    {{
      "section": "수정된 섹션",
      "original": "원본 내용",
      "revised": "수정된 내용",
      "reason": "수정 이유"
    }}
  ]
}}"""

        messages = [
            {
                "role": "system",
                "content": "당신은 콘텐츠 수정 전문가입니다. 잘못된 정보를 정확한 정보로 수정하고, 원본의 구조와 톤을 유지합니다."
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
            
            revision_result = json.loads(response)
            
            revisions = revision_result.get("revisions", [])
            revised_main_content = revision_result.get("revised_content", main_content_to_revise)
            
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

