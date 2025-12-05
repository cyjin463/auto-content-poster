#!/usr/bin/env python3
"""
오늘 생성된 영문 포스팅을 한글로 번역하여 포스팅
"""

import os
import sys
from datetime import datetime
import pytz

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.database import Database
from agents.content_agent import ContentGenerationAgent
from src.services.notion import create_notion_page


def translate_today_english_post():
    """오늘 생성된 최신 영문 포스팅을 한글로 번역"""
    
    db = Database()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    today_str = now.strftime('%Y-%m-%d')
    
    print("="*60)
    print(f"🔄 오늘 생성된 영문 포스팅을 한글로 번역")
    print("="*60)
    
    # 오늘 생성된 최신 영문 포스팅 찾기
    cursor.execute('''
        SELECT p.id, p.title, p.content, k.keyword, k.id as keyword_id
        FROM posts p
        JOIN keywords k ON p.keyword_id = k.id
        WHERE p.language = 'english'
          AND date(p.created_at) = date(?)
        ORDER BY p.created_at DESC
        LIMIT 1
    ''', (today_str,))
    
    post = cursor.fetchone()
    
    if not post:
        print("❌ 오늘 생성된 영문 포스팅이 없습니다.")
        conn.close()
        return
    
    post_id, english_title, english_content, keyword, keyword_id = post
    
    print(f"\n📝 영문 포스팅 발견:")
    print(f"   제목: {english_title}")
    print(f"   키워드: {keyword}")
    print(f"   콘텐츠 길이: {len(english_content)}자")
    
    # 이미 한글 포스팅이 있는지 확인
    cursor.execute('''
        SELECT id, title 
        FROM posts 
        WHERE keyword_id = ?
          AND language = 'korean'
          AND date(created_at) = date(?)
        LIMIT 1
    ''', (keyword_id, today_str))
    
    existing_korean = cursor.fetchone()
    if existing_korean:
        print(f"\n⚠️  이미 오늘 한글 포스팅이 존재합니다:")
        print(f"   제목: {existing_korean[1]}")
        conn.close()
        return
    
    # 한글 번역 시작
    print(f"\n🔄 한글로 번역 중...")
    agent = ContentGenerationAgent()
    
    try:
        # process 메서드의 한글 번역 로직 직접 사용
        # language='korean'으로 호출하면 영문 생성 후 번역하는 로직이 실행됨
        # 하지만 이미 영문 콘텐츠가 있으므로 직접 번역만 수행
        
        # 번역 프롬프트 준비
        import json
        from src.utils.format_fixer import fix_korean_content_format
        
        translation_prompt = f"""다음 영문 블로그 포스트를 자연스러운 한국어로 번역해주세요.

🚨🚨🚨 **절대적 명령: 반드시 한글로만 번역! 형식 반드시 유지!** 🚨🚨🚨

⚠️ 매우 중요:
- 반드시 한글로만 번역 (제목, 본문 모두)
- 소제목(##) 다음 반드시 빈 줄 필요
- 문단 사이 반드시 빈 줄 필요
- 서론-본론-결론 구조 유지
- 마크다운 형식 유지

영문 제목:
{english_title}

영문 본문:
{english_content[:4000]}

다음 JSON 형식으로 응답해주세요:
{{
  "title": "번역된 한글 제목 (15자 이내)",
  "content": "번역된 한글 본문 (빈 줄 포함, 형식 유지)"
}}"""
        
        translation_system_prompt = """당신은 전문 번역가입니다. 영문 블로그 포스트를 자연스러운 한국어로 번역합니다. 
🚨🚨🚨 **절대적 명령: 반드시 한글로만 번역! 형식 반드시 유지!** 🚨🚨🚨"""

        messages = [
            {"role": "system", "content": translation_system_prompt},
            {"role": "user", "content": translation_prompt}
        ]
        
        translation_response = agent._call_llm(
            messages,
            response_format={"type": "json_object"}
        )
        
        translated_content = json.loads(translation_response)
        korean_title = translated_content.get("title", "")
        korean_content = translated_content.get("content", "")
        
        # 이스케이프 복구
        if '\\n' in korean_content:
            korean_content = korean_content.replace('\\n', '\n')
        
        # 형식 자동 수정
        korean_content = fix_korean_content_format(korean_content)
        
        translation_result = {
            'status': 'success',
            'title': korean_title,
            'content': korean_content
        }
        
        if not translation_result or translation_result.get('status') != 'success':
            print(f"❌ 번역 실패: {translation_result}")
            conn.close()
            return
        
        korean_title = translation_result.get('title', '')
        korean_content = translation_result.get('content', '')
        
        print(f"✅ 번역 완료!")
        print(f"   한글 제목: {korean_title}")
        print(f"   한글 콘텐츠 길이: {len(korean_content)}자")
        
        # 출처 및 면책문구 확인
        from scripts.auto_poster import ensure_sources_and_disclaimer
        korean_content = ensure_sources_and_disclaimer(korean_content)
        
        # Notion에 포스팅
        print(f"\n📝 Notion에 포스팅 중...")
        database_id = os.getenv("NOTION_DATABASE_ID")
        notion_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
        
        if not database_id and not notion_page_id:
            print(f"❌ 포스팅 실패: NOTION_DATABASE_ID 또는 NOTION_PARENT_PAGE_ID가 설정되지 않았습니다.")
            conn.close()
            return
        
        notion_result = create_notion_page(
            title=korean_title,
            content=korean_content,
            parent_page_id=notion_page_id,
            database_id=database_id
        )
        
        if not notion_result or notion_result.get("status") != "success":
            print(f"❌ Notion 포스팅 실패: {notion_result}")
            conn.close()
            return
        
        page_id = notion_result.get('page_id')
        page_url = notion_result.get('page_url')
        
        print(f"✅ Notion 포스팅 완료!")
        print(f"   페이지 ID: {page_id}")
        print(f"   페이지 URL: {page_url or 'N/A'}")
        
        # 데이터베이스에 저장
        try:
            post_id_korean = db.create_post(
                keyword_id=keyword_id,
                title=korean_title,
                content=korean_content,
                search_results=[],
                status='published',
                language='korean'
            )
            
            if page_id:
                db.update_post_published(post_id_korean, page_id, page_url or '')
                
                # 학습용 캐시 업데이트
                db.update_learning_cache(
                    post_id=post_id_korean,
                    language='korean',
                    title=korean_title,
                    content=korean_content
                )
            
            print(f"\n✅ 한글 포스팅 완료!")
            print(f"   포스트 ID: {post_id_korean}")
            
        except ValueError as e:
            if "중복" in str(e):
                print(f"⚠️  중복 포스트: {e}")
            else:
                raise
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.close()


if __name__ == '__main__':
    translate_today_english_post()

