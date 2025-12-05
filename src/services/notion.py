"""
Notion API 서비스
- Notion API를 사용한 자동 포스팅
- MCP 폴백 지원
"""

import os
import requests
from typing import Dict, Optional, List
import json
from datetime import datetime, timezone, timedelta

# 환경 변수 로드
from src.core.config import load_env_file
load_env_file()


def markdown_to_notion_blocks(markdown_text: str) -> List[Dict]:
    """
    마크다운 텍스트를 노션 블록으로 변환
    """
    blocks = []
    lines = markdown_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # 제목 (### 제목)
        if line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line[4:]}
                    }]
                }
            })
        
        # 제목 (## 제목)
        elif line.startswith('## '):
            heading_text = line[3:].strip()
            # Notion API 제한: heading_2는 최대 2000자
            if len(heading_text) > 2000:
                heading_text = heading_text[:1997] + "..."
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": heading_text}
                    }]
                }
            })
        
        # 제목 (# 제목)
        elif line.startswith('# '):
            heading_text = line[2:].strip()
            
            # Notion API 제한: heading_1은 최대 2000자
            if len(heading_text) > 2000:
                heading_text = heading_text[:1997] + "..."
            
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": heading_text}
                    }]
                }
            })
        
        # 구분선 (---)
        elif line == '---' or line.startswith('---'):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        
        # 링크 ([텍스트](URL))
        elif '[' in line and '](' in line:
            import re
            link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            matches = re.findall(link_pattern, line)
            
            rich_text = []
            last_end = 0
            current_line = line
            
            for match_text, match_url in matches:
                # 링크 앞의 텍스트
                link_pattern_full = f'[{match_text}]({match_url})'
                link_start = current_line.find(link_pattern_full, last_end)
                
                if link_start > last_end:
                    before_text = current_line[last_end:link_start].strip()
                    if before_text:
                        rich_text.append({
                            "type": "text",
                            "text": {"content": before_text}
                        })
                
                # 링크 (Notion API 형식)
                rich_text.append({
                    "type": "text",
                    "text": {
                        "content": match_text,
                        "link": {"url": match_url}
                    }
                })
                
                last_end = link_start + len(link_pattern_full)
            
            # 링크 뒤의 텍스트
            if last_end < len(current_line):
                after_text = current_line[last_end:].strip()
                if after_text:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": after_text}
                    })
            
            if not rich_text:
                rich_text = [{"type": "text", "text": {"content": line}}]
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text}
            })
        
        # 일반 텍스트
        else:
            # HTML 태그 제거 (예: <small>)
            import re
            clean_line = re.sub(r'<[^>]+>', '', line)
            
            if clean_line:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": clean_line}
                        }]
                    }
                })
        
        i += 1
    
    return blocks


def create_notion_page(
    title: str,
    content: str,
    parent_page_id: Optional[str] = None,
    database_id: Optional[str] = None
) -> Dict:
    """
    Notion API를 사용하여 페이지 생성
    
    Args:
        title: 페이지 제목
        content: 마크다운 형식의 콘텐츠
        parent_page_id: 부모 페이지 ID (선택사항)
        database_id: 데이터베이스 ID (선택사항)
    
    Returns:
        생성된 페이지 정보
    """
    api_key = os.getenv("NOTION_API_KEY")
    
    if not api_key:
        raise ValueError("NOTION_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    # 한국 시간 기준 날짜 포맷팅
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    date_str = now_kst.strftime("%Y년 %m월 %d일 (%A)")
    
    # 요일을 한글로 변환
    weekday_map = {
        'Monday': '월요일',
        'Tuesday': '화요일',
        'Wednesday': '수요일',
        'Thursday': '목요일',
        'Friday': '금요일',
        'Saturday': '토요일',
        'Sunday': '일요일'
    }
    weekday_kr = weekday_map.get(now_kst.strftime('%A'), now_kst.strftime('%A'))
    date_str = date_str.replace(now_kst.strftime('%A'), weekday_kr)
    
    # 날짜 블록 생성
    date_blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"📅 {date_str}"},
                    "annotations": {
                        "color": "gray"
                    }
                }]
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    ]
    
    # 마크다운을 노션 블록으로 변환
    content_blocks = markdown_to_notion_blocks(content)
    
    # 페이지 생성 요청
    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 부모 설정
    if parent_page_id:
        parent = {
            "type": "page_id",
            "page_id": parent_page_id
        }
    elif database_id:
        parent = {
            "type": "database_id",
            "database_id": database_id
        }
    else:
        # 루트에 생성 (Integration의 공유 페이지가 있어야 함)
        raise ValueError("parent_page_id 또는 database_id 중 하나는 필수입니다.")
    
    # 날짜 블록 + 콘텐츠 블록 결합 (날짜가 먼저 오도록)
    all_blocks = date_blocks + content_blocks
    
    # 페이지 생성 시 children 블록을 함께 전달
    payload = {
        "parent": parent,
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        },
        "children": all_blocks  # 날짜 블록 + 콘텐츠 블록을 함께 전달
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if not response.ok:
        error_text = response.text
        raise Exception(f"Notion API 오류: {error_text}")
    
    data = response.json()
    
    return {
        "status": "success",
        "page_id": data.get("id"),
        "page_url": data.get("url", "").replace("https://www.notion.so/", "https://notion.so/"),
        "data": data
    }


def publish_to_notion_api(
    title: str,
    content: str,
    parent_page_id: Optional[str] = None,
    database_id: Optional[str] = None
) -> Dict:
    """
    Notion API를 사용하여 콘텐츠 포스팅
    
    Args:
        title: 제목
        content: 마크다운 콘텐츠
        parent_page_id: 부모 페이지 ID
        database_id: 데이터베이스 ID (parent_page_id 대신 사용 가능)
    
    Returns:
        포스팅 결과
    """
    try:
        result = create_notion_page(title, content, parent_page_id, database_id)
        
        return {
            "status": "success",
            "message": "노션에 성공적으로 포스팅되었습니다.",
            "page_id": result["page_id"],
            "page_url": result["page_url"]
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"노션 포스팅 실패: {str(e)}",
            "error": str(e)
        }


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


def publish_to_notion(
    title: str,
    content: str,
    parent_page_id: Optional[str] = None,
    database_id: Optional[str] = None
) -> Dict:
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
            return publish_to_notion_api(title, content, parent_page_id, database_id)
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Notion API 포스팅 실패: {str(e)}",
                "error": str(e)
            }
    
    # Notion API 키가 없으면 MCP 안내
    return publish_to_notion_mcp(title, content, parent_page_id)


# 하위 호환성을 위한 별칭
create_notion_page = create_notion_page
publish_to_notion_api = publish_to_notion_api

