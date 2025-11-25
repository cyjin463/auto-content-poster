"""
노션 API를 사용한 자동 포스팅
"""

import os
import requests
from typing import Dict, Optional, List
import json


def load_env_file():
    """.env 파일에서 환경 변수 로드"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ[key] = value


# .env 파일 로드
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
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line[3:]}
                    }]
                }
            })
        
        # 제목 (# 제목)
        elif line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line[2:]}
                    }]
                }
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
    
    # 마크다운을 노션 블록으로 변환
    blocks = markdown_to_notion_blocks(content)
    
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
        "children": blocks
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

