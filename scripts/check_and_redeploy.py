#!/usr/bin/env python3
"""
자동 배포 확인 및 재배포 스크립트
매일 오전 9시 30분에 실행되어 이전 배포 상태를 확인하고
오류가 있으면 수정 후 재배포
"""

#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from src.core.config import load_env_file
load_env_file()

# 모듈 import
from src.core.database import Database


def check_recent_posts():
    """최근 포스팅 상태 확인"""
    load_env_file()
    
    db = Database()
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    
    # 오늘 9시 10분 이후 포스팅 확인
    today_9_10am_kst = now_kst.replace(hour=9, minute=10, second=0, microsecond=0)
    
    print("🔍 자동 배포 확인 시작 (9시 30분)")
    print("=" * 60)
    
    # 오늘 9시 10분 이후 포스팅 조회
    conn = db._get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT p.*, k.keyword, k.id as keyword_id
        FROM posts p
        JOIN keywords k ON p.keyword_id = k.id
        WHERE p.created_at >= datetime(?, '-9 hours')
        ORDER BY p.created_at DESC
        LIMIT 10
    """
    
    # KST 기준으로 오늘 9시 10분 이후 포스팅 확인
    today_9_10am_utc = (today_9_10am_kst - timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(query, (today_9_10am_utc,))
    
    posts = cursor.fetchall()
    conn.close()
    
    if not posts:
        print("📝 오늘 9시 10분 이후 포스팅이 없습니다.")
        print("   → 자동 포스팅이 실행되지 않았거나 실패했을 수 있습니다.")
        
        # 자동 포스팅 재시도
        print("\n🔄 자동 포스팅 재시도 중...")
        from auto_poster import process_single_keyword_dual_language
        try:
            process_single_keyword_dual_language()
            print("\n✅ 재배포 완료!")
        except Exception as e:
            print(f"\n❌ 재배포 실패: {e}")
            import traceback
            traceback.print_exc()
        return
    
    # 포스팅 상태 확인
    print(f"📊 오늘 9시 10분 이후 포스팅: {len(posts)}건\n")
    
    issues_found = False
    posts_to_fix = []
    
    for post in posts:
        post_dict = dict(post)
        title = post_dict.get('title', '제목 없음')
        status = post_dict.get('status', 'unknown')
        language = post_dict.get('language', 'unknown')
        page_id = post_dict.get('notion_page_id')
        created_at = post_dict.get('created_at', '')
        
        print(f"  [{language.upper()}] {title[:50]}")
        print(f"      상태: {status}, Notion ID: {page_id or '없음'}")
        
        # 문제가 있는 포스팅 체크
        if status != 'published' or not page_id:
            issues_found = True
            posts_to_fix.append(post_dict)
            print(f"      ⚠️  문제 발견: 상태={status}, Notion ID={'없음' if not page_id else '있음'}")
    
    print()
    
    if not issues_found:
        print("✅ 모든 포스팅이 정상입니다!")
        return
    
    # 문제가 있는 포스팅 수정 시도
    print(f"🔧 문제가 있는 포스팅 {len(posts_to_fix)}건 수정 시도...\n")
    
    for post in posts_to_fix:
        keyword_id = post.get('keyword_id')
        keyword = post.get('keyword', '')
        language = post.get('language', 'korean')
        
        if not keyword:
            print(f"  ⚠️  키워드 정보가 없어 수정할 수 없습니다.")
            continue
        
        print(f"  🔄 [{language.upper()}] '{keyword}' 재배포 시도...")
        
        try:
            from agents.agent_chain import AgentChain
            from src.services.notion import create_notion_page
            from auto_poster import ensure_sources_and_disclaimer
            
            chain = AgentChain()
            notion_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
            
            # 콘텐츠 재생성
            result = chain.process(keyword, notion_page_id, language=language, skip_posting=True)
            
            if result["status"] == "success":
                content = result['generated_content']
                content['content'] = ensure_sources_and_disclaimer(content['content'])
                
                # 재포스팅
                database_id = os.getenv("NOTION_DATABASE_ID")
                notion_result = create_notion_page(
                    title=content['title'],
                    content=content['content'],
                    parent_page_id=notion_page_id,
                    database_id=database_id
                )
                
                if notion_result and notion_result.get("status") == "success":
                    page_id = notion_result.get('page_id')
                    page_url = notion_result.get('page_url')
                    
                    # 데이터베이스 업데이트
                    post_id = post.get('id')
                    if post_id and page_id:
                        db.update_post_published(post_id, page_id, page_url or '')
                    
                    print(f"     ✅ 재배포 성공: {page_url or page_id}")
                else:
                    print(f"     ❌ 재배포 실패: {notion_result.get('message', '알 수 없는 오류')}")
            else:
                print(f"     ❌ 콘텐츠 재생성 실패: {result.get('message', '알 수 없는 오류')}")
                
        except Exception as e:
            print(f"     ❌ 재배포 오류: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    check_recent_posts()

