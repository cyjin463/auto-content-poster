#!/usr/bin/env python3
"""
MCP를 사용하여 draft 포스트를 노션에 포스팅하는 도우미 스크립트

이 스크립트는 draft 포스트 정보를 출력하고,
Cursor에서 MCP 도구를 호출할 수 있는 명령어를 제공합니다.
"""

import sys
import argparse
from database import Database
import json


def list_drafts(db: Database):
    """draft 포스트 목록 조회"""
    posts = db.get_draft_posts()
    
    if not posts:
        print("📝 draft 상태인 포스트가 없습니다.")
        return
    
    print("\n📋 Draft 포스트 목록:\n")
    print("-" * 80)
    
    for i, post in enumerate(posts, 1):
        print(f"\n[{i}] {post['title']}")
        print(f"    키워드: {post['keyword']}")
        print(f"    생성일: {post['created_at']}")
        print(f"    포스트 ID: {post['id']}")
        if post.get('parent_page_id'):
            print(f"    부모 페이지 ID: {post['parent_page_id']}")
        print(f"    내용 미리보기: {post['content'][:100]}...")
        print(f"\n    💡 MCP 포스팅 명령:")
        print(f"       python publish_mcp.py {post['id']}")
    
    print("\n" + "-" * 80)


def show_mcp_command(post_id: str, db: Database):
    """특정 포스트의 MCP 포스팅 명령 출력"""
    posts = db.get_draft_posts()
    
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        print(f"❌ 포스트 ID '{post_id}'를 찾을 수 없거나 draft 상태가 아닙니다.")
        return
    
    print(f"\n📝 MCP 포스팅 명령:\n")
    print(f"제목: {post['title']}\n")
    print(f"📋 Cursor에서 다음 MCP 도구를 호출하세요:\n")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n도구: mcp_Notion_notion-create-pages")
    print(f"\n파라미터 (JSON):")
    
    params = {
        "pages": [
            {
                "properties": {
                    "title": post['title']
                },
                "content": post['content']
            }
        ]
    }
    
    if post.get('parent_page_id'):
        params["parent"] = {"page_id": post['parent_page_id']}
    
    print(json.dumps(params, indent=2, ensure_ascii=False))
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n📝 또는 Cursor에서 직접 요청:")
    print(f"\n\"draft 포스트 ID {post_id}를 노션에 포스팅해줘\"")
    print(f"\n📄 포스트 정보:")
    print(f"   - 제목: {post['title']}")
    print(f"   - 키워드: {post['keyword']}")
    print(f"   - 생성일: {post['created_at']}")
    if post.get('parent_page_id'):
        print(f"   - 부모 페이지 ID: {post['parent_page_id']}")
    print(f"\n💾 포스트 ID: {post_id}")


def main():
    parser = argparse.ArgumentParser(
        description='MCP를 사용하여 노션에 포스팅하는 도우미',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'post_id',
        nargs='?',
        help='포스팅할 draft 포스트 ID (없으면 목록 표시)'
    )
    
    args = parser.parse_args()
    
    db = Database()
    
    if args.post_id:
        show_mcp_command(args.post_id, db)
    else:
        list_drafts(db)


if __name__ == '__main__':
    main()

