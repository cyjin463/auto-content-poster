"""
포스팅 에이전트: 검증된 콘텐츠를 노션에 포스팅
"""

from typing import Dict, Any
from agents.base import BaseAgent
from notion_poster import publish_to_notion
import os


class PostingAgent(BaseAgent):
    """포스팅 에이전트"""
    
    def __init__(self):
        # 포스팅 에이전트는 Groq API를 사용하지 않음
        super().__init__("포스팅 에이전트", require_api_key=False)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """노션에 포스팅"""
        title = input_data["title"]
        content = input_data["content"]
        parent_page_id = input_data.get("parent_page_id")
        database_id = input_data.get("database_id")
        
        print(f"  📝 [{self.name}] 노션 포스팅 중...")
        
        # Notion API를 통한 포스팅 시도
        result = publish_to_notion(title, content, parent_page_id, database_id)
        
        if result["status"] == "success":
            print(f"  ✅ [{self.name}] 노션 포스팅 성공!")
            print(f"     페이지 ID: {result.get('page_id', 'N/A')}")
            print(f"     페이지 URL: {result.get('page_url', 'N/A')}")
            return {
                "status": "success",
                "title": title,
                "content": content,
                "parent_page_id": parent_page_id,
                "page_id": result.get("page_id"),
                "page_url": result.get("page_url"),
                "message": result.get("message", "포스팅 성공")
            }
        else:
            # Notion API 실패 시 MCP 안내
            print(f"  ⚠️  [{self.name}] Notion API 포스팅 실패: {result.get('message', '알 수 없는 오류')}")
            print(f"  💡 MCP를 사용하여 Cursor에서 직접 포스팅하세요.")
            return {
                "status": "ready",
                "title": title,
                "content": content,
                "parent_page_id": parent_page_id,
                "message": result.get("message", "MCP 도구를 사용하여 Cursor에서 직접 포스팅하세요."),
                "error": result.get("error")
            }

