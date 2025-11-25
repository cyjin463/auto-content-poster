"""
검색 에이전트: 키워드 검색 및 결과 수집
"""

from typing import Dict, Any, List
from agents.base import BaseAgent
from search import search_keywords


class SearchAgent(BaseAgent):
    """검색 에이전트"""
    
    def __init__(self):
        # 검색 에이전트는 Groq API를 사용하지 않으므로 require_api_key=False
        super().__init__("검색 에이전트", require_api_key=False)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """키워드 검색 수행"""
        keyword = input_data["keyword"]
        
        # 키워드 정규화 (쉼표 제거, 공백 정리)
        normalized_keyword = keyword.replace(',', ' ').replace('，', ' ').strip()
        normalized_keyword = ' '.join(normalized_keyword.split())
        
        # 여러 쿼리 시도 (한글과 영어 혼합)
        queries = [
            normalized_keyword,  # 정규화된 키워드 먼저
            keyword,  # 원본 키워드
            f"{normalized_keyword} 최신",
            f"{normalized_keyword} 2024",
            f"{normalized_keyword} technology",
            f"{normalized_keyword} news",
            # 개별 키워드로도 시도 (쉼표로 구분된 경우)
            normalized_keyword.split()[0] if len(normalized_keyword.split()) > 1 else normalized_keyword,
        ]
        
        search_results = []
        
        for query in queries:
            print(f"  🔍 [{self.name}] 키워드 검색 중: {query}")
            results = search_keywords(query, num_results=10)
            
            if results:
                search_results = results
                print(f"  ✅ [{self.name}] 검색 결과 {len(search_results)}개 발견")
                break
        
        if not search_results:
            print(f"  ⚠️  [{self.name}] 모든 쿼리에서 검색 결과 없음")
            return {
                "status": "no_results",
                "keyword": keyword,
                "results": [],
                "message": "검색 결과가 없습니다."
            }
        
        return {
            "status": "success",
            "keyword": keyword,
            "results": search_results,
            "count": len(search_results)
        }

