"""
노션 포스팅 (MCP 또는 Notion API 사용)
"""

import os
from typing import Dict, Optional


def publish_to_notion(title: str, content: str, parent_page_id: Optional[str] = None, database_id: Optional[str] = None) -> Dict:
    """
    노션에 포스팅 (Notion API 우선, 없으면 MCP 안내)
    
    Args:
        title: 제목
        content: 콘텐츠 (마크다운)
        parent_page_id: 부모 페이지 ID
        database_id: 데이터베이스 ID
    
    Returns:
        포스팅 결과
    """
    # Notion API 키가 있으면 API 사용
    if os.getenv("NOTION_API_KEY"):
        try:
            from notion_api import publish_to_notion_api
            return publish_to_notion_api(title, content, parent_page_id, database_id)
        except ImportError:
            pass
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Notion API 포스팅 실패: {str(e)}",
                "error": str(e)
            }
    
    # Notion API 키가 없으면 MCP 안내
    return publish_to_notion_mcp(title, content, parent_page_id)


def publish_to_notion_mcp(title: str, content: str, parent_page_id: Optional[str] = None) -> Dict:
    """
    MCP를 통한 노션 포스팅
    실제 호출은 Cursor에서 직접 수행해야 함
    """
    return {
        "status": "ready",
        "message": "MCP 도구를 사용하여 Cursor에서 직접 포스팅하세요.",
        "mcp_instructions": {
            "tool": "mcp_Notion_notion-create-pages",
            "params": {
                "parent": {"page_id": parent_page_id} if parent_page_id else None,
                "pages": [
                    {
                        "properties": {"title": title},
                        "content": content
                    }
                ]
            }
        }
    }

