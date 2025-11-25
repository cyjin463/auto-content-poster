"""
키워드 추론 에이전트
이전 포스팅 내용을 기반으로 다음에 학습할 키워드를 추론
"""

from typing import Dict, Any, Optional, List
from agents.base import BaseAgent
import json
import os


class KeywordInferenceAgent(BaseAgent):
    """다음 키워드를 추론하는 에이전트"""
    
    def __init__(self):
        super().__init__("키워드 추론 에이전트")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        이전 포스팅 내용 기반 다음 키워드 추론
        
        input_data:
            - keyword: 현재 키워드
            - previous_posts: 이전 포스팅 목록 (최근 N개)
            - learning_path: 현재까지의 학습 경로
        """
        current_keyword = input_data.get("keyword", "")
        previous_posts = input_data.get("previous_posts", [])
        learning_path = input_data.get("learning_path", [])
        
        print(f"  🤔 [{self.name}] 다음 키워드 추론 중...")
        
        # 이전 포스팅 요약 생성
        previous_context = ""
        if previous_posts:
            previous_context = "\n".join([
                f"- {post.get('title', '제목 없음')}: {post.get('content', '')[:500]}..."
                for post in previous_posts[:5]  # 최근 5개만
            ])
        else:
            previous_context = "이전 포스팅이 없습니다. 첫 번째 학습 단계입니다."
        
        # 학습 경로 요약
        path_summary = " → ".join(learning_path) if learning_path else "없음"
        
        system_prompt = """당신은 학습 경로 설계 전문가입니다. 사용자가 하나씩 차근차근 학습하는 스토리를 만듭니다.
이전에 학습한 내용을 바탕으로, 자연스럽게 다음에 배워야 할 주제나 개념을 추론합니다.
초보자가 점진적으로 깊이 있게 학습할 수 있도록 연결고리를 만들어야 합니다."""
        
        prompt = f"""현재까지의 학습 경로를 분석하고, 다음에 학습할 키워드를 추론해주세요.

**현재 키워드**: {current_keyword}

**학습 경로**: {path_summary}

**이전 포스팅 요약**:
{previous_context}

**추론 기준**:
1. 자연스러운 학습 흐름: 이전 주제에서 자연스럽게 연결되는 다음 주제
2. 단계별 심화: 너무 어렵거나 쉬운 것이 아닌, 적절한 다음 단계
3. 실용성: 독자가 실제로 알아야 할 연관 개념
4. 논리적 연결: 왜 이 키워드가 다음인지 명확한 이유

**예시**:
- "AI" → "머신러닝" (AI의 핵심 기술)
- "머신러닝" → "딥러닝" (머신러닝의 하위 분야)
- "딥러닝" → "신경망" (딥러닝의 기반)
- "Python" → "자료구조" (프로그래밍 기초)

다음 JSON 형식으로 응답해주세요:
{{
  "next_keyword": "다음 키워드 (한글)",
  "reason": "왜 이 키워드가 다음인지 설명 (한글, 200자 이내)",
  "learning_level": "beginner|intermediate|advanced",
  "connection": "이전 키워드와의 연결고리 (한글, 100자 이내)"
}}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_groq(
                messages,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            next_keyword = result.get("next_keyword", "")
            reason = result.get("reason", "")
            learning_level = result.get("learning_level", "intermediate")
            connection = result.get("connection", "")
            
            if not next_keyword:
                print(f"  ⚠️  [{self.name}] 추론 실패: 키워드가 비어있습니다.")
                return {
                    "status": "failed",
                    "message": "키워드 추론 실패"
                }
            
            print(f"  ✅ [{self.name}] 다음 키워드 추론 완료: '{next_keyword}'")
            print(f"     이유: {reason}")
            
            return {
                "status": "success",
                "next_keyword": next_keyword,
                "reason": reason,
                "learning_level": learning_level,
                "connection": connection
            }
            
        except Exception as e:
            print(f"  ❌ [{self.name}] 추론 오류: {e}")
            return {
                "status": "failed",
                "message": f"추론 오류: {e}"
            }
