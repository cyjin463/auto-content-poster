#!/usr/bin/env python3
"""
A2A 에이전트 체인을 사용한 메인 스크립트
"""

import sys
import argparse
from agents.agent_chain import AgentChain
from database import Database


def main():
    parser = argparse.ArgumentParser(description='A2A 에이전트 체인을 사용한 자동 포스팅')
    parser.add_argument('keyword', help='처리할 키워드')
    parser.add_argument('--notion-page-id', help='노션 부모 페이지 ID (선택사항)')
    parser.add_argument('--save-to-db', action='store_true', help='결과를 데이터베이스에 저장')
    
    # 언어 선택 옵션
    lang_group = parser.add_mutually_exclusive_group()
    lang_group.add_argument('--korean', action='store_true', help='한글로 포스팅 (기본값)')
    lang_group.add_argument('--english', action='store_true', help='영문으로 포스팅')
    
    args = parser.parse_args()
    
    # 언어 설정 (기본값: 한글)
    language = 'english' if args.english else 'korean'
    
    # 에이전트 체인 실행
    chain = AgentChain()
    result = chain.process(args.keyword, args.notion_page_id, language=language)
    
    if result["status"] == "success":
        print("\n✅ 처리 완료!")
        print(f"\n제목: {result['generated_content']['title']}")
        print(f"요약: {result['generated_content']['summary']}")
        print(f"\n품질 점수:")
        print(f"  - 검색 품질: {result['quality_scores']['search_quality']}")
        print(f"  - 사실 정확도: {result['quality_scores'].get('fact_accuracy', 'N/A')}")
        print(f"  - 콘텐츠 품질: {result['quality_scores']['content_quality']}")
        
        # 수정 내역 표시
        revisions = result.get("revisions", [])
        if revisions:
            print(f"\n🔧 수정 내역 ({len(revisions)}개):")
            for i, rev in enumerate(revisions[:3], 1):  # 상위 3개만 표시
                print(f"  {i}. [{rev.get('section', '섹션')}] {rev.get('reason', '수정')}")
                if len(revisions) > 3:
                    print(f"  ... 및 {len(revisions) - 3}개 더")
                    break
        
        # 사실 확인 이슈 표시
        fact_issues = result.get("fact_check_issues", [])
        if fact_issues:
            high_severity = [i for i in fact_issues if i.get("severity") == "high"]
            if high_severity:
                print(f"\n⚠️  사실 확인 이슈 ({len(high_severity)}개 심각):")
                for issue in high_severity[:2]:
                    print(f"  - {issue.get('issue', '문제')}")
        
        # 포스팅 상태 확인
        posting_status = result['posting_info'].get('status', 'ready')
        page_id = result['posting_info'].get('page_id')
        page_url = result['posting_info'].get('page_url')
        
        # 데이터베이스에 저장 (선택적)
        if args.save_to_db:
            db = Database()
            # 키워드가 없으면 추가
            keyword_data = db.get_keyword_by_name(args.keyword)
            if not keyword_data:
                keyword_id = db.add_keyword(args.keyword, args.notion_page_id)
            else:
                keyword_id = keyword_data['id']
            
            # 포스팅 성공 시 published, 실패 시 draft
            post_status = 'published' if posting_status == 'success' and page_id else 'draft'
            
            # 포스트 저장
            post_id = db.create_post(
                keyword_id=keyword_id,
                title=result['generated_content']['title'],
                content=result['generated_content']['content'],
                search_results=[],
                status=post_status,
                language=language
            )
            
            # 포스팅 성공 시 노션 페이지 정보 업데이트
            if posting_status == 'success' and page_id:
                db.update_post_published(post_id, page_id, page_url or '')
                print(f"\n💾 데이터베이스에 저장됨 (포스트 ID: {post_id}, 상태: published)")
            else:
                print(f"\n💾 데이터베이스에 저장됨 (포스트 ID: {post_id}, 상태: draft)")
        
        # 포스팅 결과 안내
        if posting_status == 'success':
            print(f"\n✅ 노션 포스팅 완료!")
            if page_url:
                print(f"   페이지 URL: {page_url}")
        else:
            print(f"\n📝 MCP를 사용하여 노션에 포스팅하세요:")
            print(f"\n💡 Cursor에서 다음 MCP 도구를 호출하세요:")
            print(f"\n도구: mcp_Notion_notion-create-pages")
            print(f"파라미터:")
            if result['posting_info'].get('parent_page_id'):
                print(f"  parent: {{ \"page_id\": \"{result['posting_info']['parent_page_id']}\" }}")
            else:
                print(f"  parent: null (또는 생략)")
            print(f"  pages: [{{")
            print(f"    \"properties\": {{ \"title\": \"{result['generated_content']['title']}\" }},")
            print(f"    \"content\": \"{result['generated_content']['content'][:100]}...\"")
            print(f"  }}]")
            print(f"\n또는 데이터베이스에 저장된 draft 포스트를 확인하세요:")
            if args.save_to_db:
                print(f"  python main.py list-drafts  # draft 포스트 목록")
        
    else:
        print(f"\n❌ 처리 실패: {result.get('message', '알 수 없는 오류')}")
        sys.exit(1)


if __name__ == '__main__':
    main()

