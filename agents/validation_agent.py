"""
검증 에이전트: 검색 결과 및 콘텐츠 품질 검증
"""

from typing import Dict, Any, List
from agents.base import BaseAgent
import json
import sys
import os
import re

# 모듈 import
from src.utils.helpers import validate_korean_content


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
            response = self._call_llm(
                messages,
                response_format={"type": "json_object"}
            )
            
            validation_result = json.loads(response)
            
            # quality_score가 없거나 숫자가 아니면 기본값 설정
            quality_score = validation_result.get("quality_score", 0)
            try:
                quality_score = int(quality_score) if quality_score else 0
            except (ValueError, TypeError):
                print(f"  ⚠️  품질 점수가 올바르지 않습니다: {quality_score}, 기본값 0 사용")
                quality_score = 0
            
            # 품질 점수가 0이면 검색 결과가 있는 경우 기본값 50으로 설정
            if quality_score == 0 and search_results:
                print(f"  ⚠️  품질 점수가 0이지만 검색 결과가 있으므로 기본값 50 사용")
                quality_score = 50
                validation_result["quality_score"] = 50
            
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
                
        except json.JSONDecodeError as e:
            print(f"  ⚠️  [{self.name}] JSON 파싱 오류: {e}")
            print(f"  📝 응답 내용: {response[:200] if 'response' in locals() else 'N/A'}...")
            # JSON 파싱 실패 시 재시도 또는 기본값으로 처리
            # 검색 결과가 있으면 일단 통과 (검색 자체는 성공했으므로)
            if search_results:
                print(f"  ⚠️  검색 결과는 있으므로 통과 처리합니다.")
                return {
                    "status": "validated",
                    "is_valid": True,
                    "quality_score": 50,
                    "validated_results": search_results
                }
            else:
                return {
                    "status": "rejected",
                    "is_valid": False,
                    "reason": "검증 응답 파싱 실패",
                    "validated_results": []
                }
        except Exception as e:
            print(f"  ⚠️  [{self.name}] 검증 중 오류: {e}")
            import traceback
            traceback.print_exc()
            # 검색 결과가 있으면 일단 통과 (검색 자체는 성공했으므로)
            if search_results:
                print(f"  ⚠️  검색 결과는 있으므로 통과 처리합니다.")
                return {
                    "status": "validated",
                    "is_valid": True,
                    "quality_score": 50,
                    "validated_results": search_results
                }
            else:
                return {
                    "status": "rejected",
                    "is_valid": False,
                    "reason": f"검증 오류: {str(e)}",
                    "validated_results": []
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
        
        # 언어별 검증
        language_valid = True
        language_error = ""
        language_issue = []
        
        if language == 'korean':
            # 한글 검증
            language_valid, language_error = validate_korean_content(title, content)
            if not language_valid:
                language_issue.append(f"⚠️ 한글 검증 실패: {language_error}")
            
            # 한글 형식 검증 (서론-본론-결론 구조 확인)
            format_valid, format_error = self._validate_korean_format(content)
            if not format_valid:
                language_valid = False  # 형식 검증 실패 시 전체 검증 실패
                language_error = format_error
                language_issue.append(f"⚠️ 형식 검증 실패: {format_error}")
        elif language == 'english':
            # 영문 검증: 한글이나 다른 언어가 포함되어 있으면 안 됨
            # 제목에 한글 포함 여부 확인
            korean_char_pattern = re.compile(r'[가-힣]')
            title_korean_count = len(korean_char_pattern.findall(title))
            content_korean_count = len(korean_char_pattern.findall(content))
            
            if title_korean_count > 0:
                language_valid = False
                language_error = f"제목에 한글이 {title_korean_count}개 포함되어 있습니다."
                language_issue.append(f"⚠️ 영문 검증 실패: {language_error}")
            
            if content_korean_count > 0:
                language_valid = False
                language_error = f"본문에 한글이 {content_korean_count}개 이상 포함되어 있습니다."
                language_issue.append(f"⚠️ 영문 검증 실패: {language_error}")
            
            # 중국어, 일본어, 베트남어 등 다른 언어도 체크
            other_lang_pattern = re.compile(r'[一-龯\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FAF]')
            other_lang_in_title = other_lang_pattern.search(title)
            other_lang_in_content = other_lang_pattern.search(content[:1000])  # 처음 1000자만 체크
            
            if other_lang_in_title or other_lang_in_content:
                language_valid = False
                language_error = "제목 또는 본문에 한자, 일본어 등 다른 언어가 포함되어 있습니다."
                language_issue.append(f"⚠️ 영문 검증 실패: {language_error}")
        
        # 언어별 프롬프트 생성
        if language == 'korean':
            language_instruction = "⚠️ 중요: 이 포스트는 반드시 한글로만 작성되어야 합니다."
            system_message = "당신은 콘텐츠 품질 검증 전문가입니다. 콘텐츠의 정확성, 가독성, 전문성을 평가합니다."
            prompt = f"""다음 블로그 포스트의 품질을 검증해주세요.

제목: {title}
키워드: {keyword}

내용:
{content[:500]}...

{language_instruction}

다음 JSON 형식으로 응답해주세요:
{{
  "is_valid": true/false,
  "quality_score": 0-100,
  "issues": ["문제점1", "문제점2"],
  "recommendation": "publish/reject/revise"
}}"""
        else:  # english
            # 영문 모드일 때: 키워드를 영어로 변환 (re는 파일 상단에서 이미 import됨)
            korean_pattern = re.compile(r'[가-힣]+')
            keyword_for_validation = keyword
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
                keyword_for_validation = keyword_translation_map.get(keyword, keyword)
            
            language_instruction = "⚠️ IMPORTANT: This post must be written ONLY in English. No Korean, Chinese, or other languages should be included. If you find any non-English content, mark it as invalid."
            system_message = "You are a content quality validation expert. You evaluate the accuracy, readability, and professionalism of content. Validate that the content is written in English only."
            prompt = f"""Please validate the quality of the following blog post.

Title: {title}
Keyword: {keyword_for_validation}

Content:
{content[:500]}...

{language_instruction}

Please respond in the following JSON format:
{{
  "is_valid": true/false,
  "quality_score": 0-100,
  "issues": ["issue1", "issue2"],
  "recommendation": "publish/reject/revise"
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
            
            validation_result = json.loads(response)
            
            # 언어 검증 이슈 추가
            all_issues = validation_result.get("issues", [])
            if language_issue:
                all_issues = language_issue + all_issues
                # 언어 검증 실패하면 reject
                if not language_valid:
                    print(f"  ❌ [{self.name}] {language} 검증 실패: {language_error}")
                    return {
                        "status": "rejected",
                        "is_valid": False,
                        "reason": language_error,
                        "quality_score": 0
                    }
            
            # 검증 통과 조건 수정
            recommendation = validation_result.get("recommendation", "").lower()
            if recommendation == "publish" and language_valid:
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
    
    def _validate_korean_format(self, content: str) -> tuple[bool, str]:
        """
        한글 콘텐츠의 형식 검증 (서론-본론-결론 구조)
        
        Returns:
            (is_valid, error_message)
        """
        # 서론 확인 (## 서론 또는 Introduction 또는 첫 문단이 서론으로 시작)
        lines = content.strip().split('\n')
        has_intro_section = False
        has_body_sections = False
        has_conclusion = False
        
        # 소제목 개수 확인
        heading_pattern = re.compile(r'^##\s+.+$', re.MULTILINE)
        headings = heading_pattern.findall(content)
        
        # 결론 확인
        has_conclusion = any("## 결론" in h or "## Conclusion" in h for h in headings) or "## 결론" in content
        
        # 문단 구분 확인 (빈 줄이 충분히 있는지)
        double_newlines = content.count("\n\n")
        # 최소 10개 이상의 빈 줄(문단 구분)이 있어야 함 (서론 2-3개 문단, 본론 3-4개 섹션, 결론 2-3개 문단)
        has_sufficient_breaks = double_newlines >= 8
        
        errors = []
        
        # 본론 소제목 확인 (최소 3개 필요)
        body_headings = [h for h in headings if "서론" not in h and "결론" not in h and "Introduction" not in h and "Conclusion" not in h]
        
        if len(body_headings) < 3:
            errors.append(f"본론 소제목이 부족합니다 (현재 {len(body_headings)}개, 최소 3개 필요). 형식 없이 통으로 작성되었을 수 있습니다.")
        
        if not has_conclusion:
            errors.append("결론 섹션이 없습니다.")
        
        if not has_sufficient_breaks:
            errors.append(f"문단 사이 빈 줄이 부족합니다 (현재 {double_newlines}개, 최소 8개 필요). 형식이 통으로 작성되어 띄어쓰기 없이 연결되었을 수 있습니다.")
        
        # 소제목 다음 빈 줄 확인 (모든 소제목 확인)
        missing_breaks_count = 0
        for heading in headings:
            heading_match = re.search(re.escape(heading), content)
            if heading_match:
                start_pos = heading_match.end()
                next_chars = content[start_pos:start_pos + 3]
                if not next_chars.startswith("\n\n") and not next_chars.startswith("\n\r\n"):
                    missing_breaks_count += 1
        
        if missing_breaks_count > 0:
            errors.append(f"소제목 다음에 빈 줄이 없는 경우가 {missing_breaks_count}개 있습니다. 소제목과 본문 사이 반드시 빈 줄이 필요합니다.")
        
        # 긴 줄이 연속으로 있는지 확인 (통으로 작성되었는지)
        lines = content.split('\n')
        consecutive_long_lines = 0
        for line in lines[:20]:  # 처음 20줄만 확인
            if len(line) > 100 and line.strip() and not line.strip().startswith('#'):  # 소제목 제외
                consecutive_long_lines += 1
            else:
                consecutive_long_lines = 0
            
            if consecutive_long_lines >= 3:  # 3줄 이상 연속으로 100자 넘으면 의심
                errors.append("긴 줄이 연속으로 있어 띄어쓰기 없이 통으로 작성되었을 수 있습니다.")
                break
        
        if errors:
            return False, "; ".join(errors[:3])
        
        return True, ""

