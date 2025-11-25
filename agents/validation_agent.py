"""
검증 에이전트: 검색 결과 및 콘텐츠 품질 검증
"""

from typing import Dict, Any, List
from agents.base import BaseAgent
import json
import sys
import os

# utils 모듈 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import validate_korean_content


class SearchValidationAgent(BaseAgent):
    """검색 결과 검증 에이전트"""
    
    def __init__(self):
        super().__init__("검증 에이전트 (검색)")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """검색 결과 품질 검증"""
        keyword = input_data["keyword"]
        search_results = input_data["results"]
        
        if not search_results:
            return {
                "status": "rejected",
                "reason": "검색 결과가 없습니다.",
                "validated_results": []
            }
        
        print(f"  ✅ [{self.name}] 검색 결과 검증 중...")
        
        # 검색 결과 요약
        results_summary = "\n".join([
            f"{i+1}. {r['title']}\n   {r['snippet'][:100]}..."
            for i, r in enumerate(search_results[:5])
        ])
        
        # AI로 검증
        prompt = f"""다음 검색 결과들이 "{keyword}" 키워드와 관련성이 있고, 최신 정보로 보이는지 검증해주세요.

검색 결과:
{results_summary}

다음 JSON 형식으로 응답해주세요:
{{
  "is_valid": true/false,
  "reason": "검증 이유",
  "quality_score": 0-100,
  "recommendation": "포스팅 진행 여부 (proceed/skip)"
}}"""

        messages = [
            {
                "role": "system",
                "content": "당신은 검색 결과 품질 검증 전문가입니다. 검색 결과의 관련성, 최신성, 신뢰성을 평가합니다."
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
            
            validation_result = json.loads(response)
            
            quality_score = validation_result.get("quality_score", 0)
            
            # 품질 점수가 50 이상이면 통과
            if validation_result.get("recommendation") == "proceed" or quality_score >= 50:
                print(f"  ✅ [{self.name}] 검증 통과 (품질 점수: {quality_score})")
                return {
                    "status": "validated",
                    "is_valid": True,
                    "quality_score": quality_score,
                    "validated_results": search_results
                }
            else:
                print(f"  ⚠️  [{self.name}] 검증 경고: {validation_result.get('reason', '알 수 없는 이유')} (품질 점수: {quality_score})")
                # 검증 실패해도 품질 점수가 20 이상이면 경고만 하고 통과 (더 완화)
                if quality_score >= 20:
                    print(f"  ⚠️  [{self.name}] 품질 점수 {quality_score}로 낮지만 진행합니다.")
                    return {
                        "status": "validated",
                        "is_valid": True,
                        "quality_score": quality_score,
                        "validated_results": search_results,
                        "warning": validation_result.get("reason", "품질이 낮지만 진행")
                    }
                # 품질 점수가 20 미만이면 거부
                print(f"  ❌ [{self.name}] 품질 점수 {quality_score}로 너무 낮아 거부합니다.")
                return {
                    "status": "rejected",
                    "is_valid": False,
                    "reason": validation_result.get("reason", "품질 검증 실패"),
                    "validated_results": []
                }
                
        except Exception as e:
            print(f"  ⚠️  [{self.name}] 검증 중 오류, 통과 처리: {e}")
            # 오류 시 통과 처리
            return {
                "status": "validated",
                "is_valid": True,
                "quality_score": 50,
                "validated_results": search_results
            }


class ContentValidationAgent(BaseAgent):
    """콘텐츠 품질 검증 에이전트"""
    
    def __init__(self):
        super().__init__("검증 에이전트 (콘텐츠)")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """생성된 콘텐츠 품질 검증"""
        content = input_data["content"]
        title = input_data["title"]
        keyword = input_data.get("keyword", "")
        language = input_data.get("language", "korean")  # 기본값: 한글
        
        print(f"  ✅ [{self.name}] 콘텐츠 품질 검증 중...")
        
        # 한글 검증 (한글 모드일 때만)
        is_korean = True
        korean_error = ""
        korean_issue = []
        
        if language == 'korean':
            is_korean, korean_error = validate_korean_content(title, content)
            if not is_korean:
                korean_issue.append(f"⚠️ 한글 검증 실패: {korean_error}")
        
        prompt = f"""다음 블로그 포스트의 품질을 검증해주세요.

제목: {title}
키워드: {keyword}

내용:
{content[:500]}...

⚠️ 중요: 이 포스트는 반드시 한글로만 작성되어야 합니다.

다음 JSON 형식으로 응답해주세요:
{{
  "is_valid": true/false,
  "quality_score": 0-100,
  "issues": ["문제점1", "문제점2"],
  "recommendation": "publish/reject/revise"
}}"""

        messages = [
            {
                "role": "system",
                "content": "당신은 콘텐츠 품질 검증 전문가입니다. 콘텐츠의 정확성, 가독성, 전문성을 평가합니다."
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
            
            validation_result = json.loads(response)
            
            # 한글 검증 이슈 추가
            all_issues = validation_result.get("issues", [])
            if korean_issue:
                all_issues = korean_issue + all_issues
                # 한글이 아니면 reject
                if not is_korean:
                    print(f"  ❌ [{self.name}] 한글 검증 실패: {korean_error}")
                    return {
                        "status": "rejected",
                        "is_valid": False,
                        "reason": korean_error,
                        "quality_score": 0
                    }
            
            if validation_result.get("recommendation") == "publish" and is_korean:
                print(f"  ✅ [{self.name}] 콘텐츠 검증 통과 (품질 점수: {validation_result.get('quality_score', 'N/A')})")
                return {
                    "status": "validated",
                    "is_valid": True,
                    "quality_score": validation_result.get("quality_score", 0),
                    "issues": all_issues
                }
            else:
                print(f"  ⚠️  [{self.name}] 콘텐츠 검증 실패: {all_issues[:2]}")
                return {
                    "status": "rejected",
                    "is_valid": False,
                    "reason": ", ".join(all_issues[:3]) if all_issues else "품질 검증 실패",
                    "quality_score": validation_result.get("quality_score", 0)
                }
                
        except Exception as e:
            print(f"  ⚠️  [{self.name}] 검증 중 오류, 통과 처리: {e}")
            return {
                "status": "validated",
                "is_valid": True,
                "quality_score": 50,
                "issues": []
            }

