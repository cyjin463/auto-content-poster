#!/usr/bin/env python3
"""
자동 노션 포스팅 시스템 - Python CLI

사용법:
    python main.py add-keyword "키워드" [--notion-page-id PAGE_ID]
    python main.py list-keywords
    python main.py process-keyword "키워드"
    python main.py process-all
    python main.py delete-keyword "키워드"
    python main.py toggle-keyword "키워드"
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

from database import Database
from search import search_keywords
from content_generator import generate_content
from notion_poster import publish_to_notion_mcp
from scheduler import run_scheduled_tasks


def main():
    parser = argparse.ArgumentParser(
        description='자동 노션 포스팅 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='명령어')
    
    # 키워드 추가
    add_parser = subparsers.add_parser('add-keyword', help='키워드 추가')
    add_parser.add_argument('keyword', help='추가할 키워드')
    add_parser.add_argument('--notion-page-id', help='노션 부모 페이지 ID (선택사항)')
    
    # 키워드 목록
    subparsers.add_parser('list-keywords', help='키워드 목록 조회')
    
    # 키워드 처리
    process_parser = subparsers.add_parser('process-keyword', help='키워드 즉시 처리')
    process_parser.add_argument('keyword', help='처리할 키워드')
    
    # 언어 선택 옵션
    lang_group = process_parser.add_mutually_exclusive_group()
    lang_group.add_argument('--korean', action='store_true', help='한글로 포스팅 (기본값)')
    lang_group.add_argument('--english', action='store_true', help='영문으로 포스팅')
    
    # 모든 키워드 처리
    subparsers.add_parser('process-all', help='모든 활성 키워드 처리')
    
    # 키워드 삭제
    delete_parser = subparsers.add_parser('delete-keyword', help='키워드 삭제')
    delete_parser.add_argument('keyword', help='삭제할 키워드')
    
    # 키워드 활성화/비활성화
    toggle_parser = subparsers.add_parser('toggle-keyword', help='키워드 활성화/비활성화')
    toggle_parser.add_argument('keyword', help='토글할 키워드')
    
    # 크론 실행
    subparsers.add_parser('cron', help='크론 작업 실행 (자동 실행용)')
    
    # Draft 포스트 목록
    subparsers.add_parser('list-drafts', help='draft 포스트 목록 조회 (MCP 포스팅용)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    db = Database()
    
    try:
        if args.command == 'add-keyword':
            keyword_id = db.add_keyword(args.keyword, args.notion_page_id)
            print(f"✅ 키워드 '{args.keyword}' 추가되었습니다. (ID: {keyword_id})")
            
        elif args.command == 'list-keywords':
            keywords = db.list_keywords()
            if not keywords:
                print("📝 등록된 키워드가 없습니다.")
                return
            
            print("\n📋 등록된 키워드:")
            print("-" * 80)
            for kw in keywords:
                status = "🟢 활성" if kw['is_active'] else "🔴 비활성"
                posts_count = kw.get('posts_count', 0)
                last_posted = kw.get('last_posted', '없음')
                print(f"  {status} | {kw['keyword']:30s} | 포스트: {posts_count}개 | 마지막: {last_posted}")
            print()
            
        elif args.command == 'process-keyword':
            process_single_keyword(db, args.keyword)
            
        elif args.command == 'process-all':
            process_all_keywords(db)
            
        elif args.command == 'delete-keyword':
            deleted = db.delete_keyword_by_name(args.keyword)
            if deleted:
                print(f"✅ 키워드 '{args.keyword}' 삭제되었습니다.")
            else:
                print(f"❌ 키워드 '{args.keyword}'를 찾을 수 없습니다.")
                
        elif args.command == 'toggle-keyword':
            toggled = db.toggle_keyword(args.keyword)
            if toggled:
                status = "활성화" if toggled['is_active'] else "비활성화"
                print(f"✅ 키워드 '{args.keyword}' {status}되었습니다.")
            else:
                print(f"❌ 키워드 '{args.keyword}'를 찾을 수 없습니다.")
                
        elif args.command == 'cron':
            run_scheduled_tasks(db)
            
        elif args.command == 'list-drafts':
            from publish_mcp import list_drafts
            list_drafts(db)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  작업이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def process_single_keyword(db: Database, keyword_name: str):
    """단일 키워드 처리"""
    keyword = db.get_keyword_by_name(keyword_name)
    if not keyword:
        print(f"❌ 키워드 '{keyword_name}'를 찾을 수 없습니다.")
        return
    
    if not keyword['is_active']:
        print(f"⚠️  키워드 '{keyword_name}'가 비활성화되어 있습니다.")
        return
    
    print(f"\n🔍 키워드 '{keyword_name}' 처리 시작...")
    process_keyword(db, keyword['id'], keyword['keyword'], keyword.get('notion_page_id'))


def process_all_keywords(db: Database):
    """활성 키워드 하나만 처리 (한글 + 영문 각 1개 포스팅)"""
    # 첫 번째 활성 키워드만 가져오기
    keyword = db.get_first_active_keyword()
    
    if not keyword:
        print("📝 처리할 활성 키워드가 없습니다.")
        return
    
    print(f"\n🚀 키워드 처리 시작: '{keyword['keyword']}' (한글 + 영문 각 1개 포스팅)\n")
    
    try:
        process_keyword_dual_language(db, keyword['id'], keyword['keyword'], keyword.get('notion_page_id'))
    except Exception as e:
        print(f"❌ 키워드 '{keyword['keyword']}' 처리 실패: {e}\n")
        import traceback
        traceback.print_exc()


def process_keyword(db: Database, keyword_id: str, keyword: str, notion_page_id: Optional[str]):
    """키워드 처리 (검색 → AI 생성 → 노션 포스팅)"""
    
    # 1. 오늘 이미 포스팅했는지 확인
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_posted = db.get_keyword_last_posted(keyword_id)
    
    if last_posted and last_posted >= today:
        print(f"⏭️  오늘 이미 포스팅되었습니다. 건너뜁니다.")
        db.update_keyword_last_checked(keyword_id)
        return
    
    # 2. 검색
    print(f"  📡 최신 정보 검색 중...")
    query = f"{keyword} 최신"
    search_results = search_keywords(query, num_results=10)
    
    if not search_results:
        print(f"  ⚠️  검색 결과가 없습니다. 건너뜁니다.")
        db.update_keyword_last_checked(keyword_id)
        return
    
    print(f"  ✅ 검색 결과 {len(search_results)}개 발견")
    
    # 3. AI 콘텐츠 생성
    print(f"  🤖 AI 콘텐츠 생성 중...")
    try:
        generated_content = generate_content(keyword, keyword, search_results)
        print(f"  ✅ 콘텐츠 생성 완료: {generated_content['title']}")
    except Exception as e:
        print(f"  ❌ 콘텐츠 생성 실패: {e}")
        raise
    
    # 4. 노션에 포스팅 (Notion API 사용)
    print(f"  📝 노션에 포스팅 중...")
    notion_result = None
    post_status = 'draft'
    
    try:
        from notion_poster import publish_to_notion
        import os
        database_id = os.getenv("NOTION_DATABASE_ID")
        
        notion_result = publish_to_notion(
            generated_content['title'],
            generated_content['content'],
            notion_page_id,
            database_id
        )
        
        if notion_result.get("status") == "success":
            print(f"  ✅ 노션 포스팅 성공!")
            print(f"     페이지 ID: {notion_result.get('page_id', 'N/A')}")
            print(f"     페이지 URL: {notion_result.get('page_url', 'N/A')}")
            post_status = 'published'
        else:
            print(f"  ⚠️  노션 포스팅 실패: {notion_result.get('message', '알 수 없는 오류')}")
            print(f"  💡 MCP를 사용하여 Cursor에서 직접 포스팅하세요.")
    except Exception as e:
        print(f"  ⚠️  노션 포스팅 오류: {e}")
        print(f"  💡 MCP를 사용하여 Cursor에서 직접 포스팅하세요.")
    
    # 5. 데이터베이스에 저장
    post_id = db.create_post(
        keyword_id=keyword_id,
        title=generated_content['title'],
        content=generated_content['content'],
        search_results=search_results,
        status=post_status
    )
    print(f"  💾 포스트 저장됨 (ID: {post_id}, 상태: {post_status})")
    
    # 포스팅 성공 시 노션 페이지 정보 업데이트
    if notion_result and notion_result.get("status") == "success":
        page_id = notion_result.get("page_id")
        page_url = notion_result.get("page_url", "")
        db.update_post_published(post_id, page_id, page_url)
    
    # 키워드 상태 업데이트
    db.update_keyword_last_checked(keyword_id)
    if post_status == 'published':
        db.update_keyword_last_posted(keyword_id)
    
    print(f"  ✅ 처리 완료!")


if __name__ == '__main__':
    main()

