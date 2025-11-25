#!/usr/bin/env python3
"""
Notion API 테스트 스크립트
"""

import os
import sys
from notion_api import load_env_file, create_notion_page

load_env_file()

api_key = os.getenv('NOTION_API_KEY')
parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
database_id = os.getenv('NOTION_DATABASE_ID')

print("🔍 Notion API 설정 확인:")
print(f"  API 키: {'✅ 설정됨' if api_key else '❌ 설정 안됨'}")
print(f"  Parent Page ID: {parent_page_id or '없음'}")
print(f"  Database ID: {database_id or '없음'}")

if not api_key:
    print("\n❌ NOTION_API_KEY가 설정되지 않았습니다.")
    print("   .env 파일에 NOTION_API_KEY를 설정하세요.")
    sys.exit(1)

if not parent_page_id and not database_id:
    print("\n⚠️  Parent Page ID 또는 Database ID가 필요합니다.")
    print("   .env 파일에 NOTION_PARENT_PAGE_ID 또는 NOTION_DATABASE_ID를 설정하세요.")
    print("\n   또는 테스트용 페이지 ID를 직접 입력하세요:")
    test_id = input("   테스트용 페이지/데이터베이스 ID (엔터로 종료): ").strip()
    if test_id:
        parent_page_id = test_id
    else:
        sys.exit(1)

# 테스트 콘텐츠
test_title = "테스트: Notion API 자동 포스팅"
test_content = """# 테스트 제목

이것은 Notion API 자동 포스팅 테스트입니다.

## 섹션 1

테스트 콘텐츠입니다.

## 참고 출처

- [테스트 링크](https://example.com)

---

<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글의 정보는 100% 정확하지 않을 수 있습니다. 참고 자료로 활용하시기 바랍니다.</span>
"""

print(f"\n🚀 Notion API 테스트 시작...")
print(f"   제목: {test_title}")

try:
    result = create_notion_page(
        test_title,
        test_content,
        parent_page_id=parent_page_id if parent_page_id else None,
        database_id=database_id if database_id else None
    )
    
    print(f"\n✅ 성공!")
    print(f"   페이지 ID: {result['page_id']}")
    print(f"   페이지 URL: {result['page_url']}")
    print(f"\n   노션에서 확인하세요: {result['page_url']}")
    
except Exception as e:
    print(f"\n❌ 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

