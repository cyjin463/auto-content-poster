#!/usr/bin/env python3
"""
한글 콘텐츠만 테스트 포스팅
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from src.core.config import load_env_file
load_env_file()

# 모듈 import
from src.core.database import Database
from agents.agent_chain import AgentChain
from src.services.notion import create_notion_page
from scripts.auto_poster import ensure_sources_and_disclaimer
import os

def test_korean_posting():
    """한글 콘텐츠만 테스트 포스팅"""
    db = Database()
    keyword_obj = db.get_first_active_keyword()
    
    if not keyword_obj:
        print("❌ 활성 키워드가 없습니다.")
        return
    
    keyword_name = keyword_obj['keyword']
    print(f"📝 테스트 포스팅 시작: '{keyword_name}' (한글만)")
    print("=" * 60)
    
    try:
        # Agent Chain 초기화
        chain = AgentChain()
        notion_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
        
        # 한글 콘텐츠 생성
        print(f"\n🔄 한글 콘텐츠 생성 중...")
        result = chain.process(keyword_name, notion_page_id, language='korean', skip_posting=True)
        
        if result["status"] != "success":
            print(f"❌ 콘텐츠 생성 실패: {result.get('message', '알 수 없는 오류')}")
            return
        
        content = result['generated_content']
        validated_results = result.get('validated_results', [])
        
        print(f"\n📊 생성된 콘텐츠 정보:")
        print(f"   제목: {content['title']}")
        print(f"   본문 길이: {len(content['content'])}자")
        
        # 검증 테스트
        print(f"\n🔍 검증 테스트 시작...")
        from src.utils.helpers import validate_korean_content
        
        is_valid, error = validate_korean_content(content['title'], content['content'])
        
        print(f"\n{'='*60}")
        if is_valid:
            print("✅ 검증 통과!")
        else:
            print(f"❌ 검증 실패!")
            print(f"   실패 이유: {error}")
        print(f"{'='*60}")
        
        # 상세 검증 정보 출력
        print(f"\n📋 상세 검증 정보:")
        import re
        
        # 한글 비율 계산
        def _calc_ratio(text, pattern):
            matches = len(re.findall(pattern, text))
            total = len(re.sub(r'[\s.,!?;:()\[\]{}"\'-]', '', text))
            return (matches / total * 100) if total > 0 else 0
        
        title_korean = _calc_ratio(content['title'], r'[가-힣]')
        content_korean = _calc_ratio(content['content'], r'[가-힣]')
        content_english = _calc_ratio(content['content'], r'[a-zA-Z]')
        
        print(f"   제목 한글 비율: {title_korean:.1f}% (필요: 70% 이상)")
        print(f"   본문 한글 비율: {content_korean:.1f}% (필요: 80% 이상)")
        print(f"   본문 영어 비율: {content_english:.1f}% (최대: 25%)")
        
        # 검증 통과 시에만 포스팅
        if is_valid:
            print(f"\n📝 Notion에 포스팅 중...")
            content['content'] = ensure_sources_and_disclaimer(content['content'])
            
            database_id = os.getenv("NOTION_DATABASE_ID")
            notion_result = create_notion_page(
                title=content['title'],
                content=content['content'],
                parent_page_id=notion_page_id,
                database_id=database_id
            )
            
            if notion_result and notion_result.get("status") == "success":
                page_url = notion_result.get('page_url')
                print(f"✅ 포스팅 완료: {page_url}")
            else:
                print(f"❌ 포스팅 실패: {notion_result.get('message', '알 수 없는 오류')}")
        else:
            print(f"\n⚠️  검증 실패로 포스팅하지 않습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_korean_posting()

