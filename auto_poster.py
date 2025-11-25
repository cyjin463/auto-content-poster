#!/usr/bin/env python3
"""
자동 포스팅 메인 스크립트
- 키워드 하나만 처리
- 한글 1개 + 영문 1개 포스팅
- 중복 방지
- 출처 및 면책문구 필수
"""

import sys
from datetime import datetime
from database import Database
from agents.agent_chain import AgentChain
from agents.keyword_inference_agent import KeywordInferenceAgent
import os


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


def ensure_sources_and_disclaimer(content: str) -> str:
    """출처와 면책문구가 있는지 확인하고 없으면 추가"""
    has_sources = "## 참고 출처" in content or "## References" in content
    has_disclaimer = "본 글의 정보는 100%" in content or "information in this article may not be 100%" in content
    
    if not has_sources:
        # 출처 섹션 추가 필요 (경고)
        print("  ⚠️  경고: 출처 섹션이 없습니다.")
    
    if not has_disclaimer:
        # 면책 문구 추가
        if "## 참고 출처" in content or "References" in content:
            # 출처 다음에 추가
            if "## References" in content:
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ The information in this article may not be 100% accurate. Please use it as a reference.</span>"
            else:
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글의 정보는 100% 정확하지 않을 수 있습니다. 참고 자료로 활용하시기 바랍니다.</span>"
        else:
            # 끝에 추가
            if any(keyword in content.lower() for keyword in ['the', 'is', 'are', 'this', 'that']):
                # 영문으로 판단
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ The information in this article may not be 100% accurate. Please use it as a reference.</span>"
            else:
                # 한글로 판단
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글의 정보는 100% 정확하지 않을 수 있습니다. 참고 자료로 활용하시기 바랍니다.</span>"
    
    return content


def process_single_keyword_dual_language():
    """단일 키워드를 한글/영문 각 1개씩 포스팅"""
    load_env_file()
    
    db = Database()
    
    # 첫 번째 활성 키워드만 가져오기
    keyword = db.get_first_active_keyword()
    
    if not keyword:
        print("📝 처리할 활성 키워드가 없습니다.")
        return
    
    keyword_id = keyword['id']
    keyword_name = keyword['keyword']
    notion_page_id = keyword.get('notion_page_id') or os.getenv("NOTION_PARENT_PAGE_ID")
    
    print(f"\n{'='*60}")
    print(f"🚀 자동 포스팅 시작: '{keyword_name}'")
    print(f"{'='*60}\n")
    
    # 오늘 이미 포스팅했는지 확인
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_posted = db.get_keyword_last_posted(keyword_id)
    
    if last_posted and last_posted >= today:
        print(f"⏭️  오늘 이미 포스팅되었습니다. 건너뜁니다.")
        return
    
    chain = AgentChain()
    
    # 1. 한글 포스팅
    print(f"\n📝 [1/2] 한글 포스팅 시작\n")
    try:
        result_korean = chain.process(keyword_name, notion_page_id, language='korean')
        
        if result_korean["status"] == "success":
            content_korean = result_korean['generated_content']
            
            # 출처와 면책문구 확인
            content_korean['content'] = ensure_sources_and_disclaimer(content_korean['content'])
            
            # 중복 체크 후 저장
            try:
                post_id_korean = db.create_post(
                    keyword_id=keyword_id,
                    title=content_korean['title'],
                    content=content_korean['content'],
                    search_results=[],
                    status='published' if result_korean['posting_info'].get('page_id') else 'draft',
                    language='korean'
                )
                
                # 포스팅 성공 시 업데이트
                if result_korean['posting_info'].get('page_id'):
                    db.update_post_published(
                        post_id_korean,
                        result_korean['posting_info']['page_id'],
                        result_korean['posting_info'].get('page_url', '')
                    )
                
                print(f"\n✅ 한글 포스팅 완료!")
                if result_korean['posting_info'].get('page_url'):
                    print(f"   URL: {result_korean['posting_info']['page_url']}")
            except ValueError as e:
                if "중복" in str(e):
                    print(f"  ⏭️  중복 포스트: {e}")
                else:
                    raise
        else:
            print(f"  ❌ 한글 포스팅 실패: {result_korean.get('message', '알 수 없는 오류')}")
    except Exception as e:
        print(f"  ❌ 한글 포스팅 오류: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 영문 포스팅
    print(f"\n📝 [2/2] 영문 포스팅 시작\n")
    try:
        result_english = chain.process(keyword_name, notion_page_id, language='english')
        
        if result_english["status"] == "success":
            content_english = result_english['generated_content']
            
            # 출처와 면책문구 확인
            content_english['content'] = ensure_sources_and_disclaimer(content_english['content'])
            
            # 중복 체크 후 저장
            try:
                post_id_english = db.create_post(
                    keyword_id=keyword_id,
                    title=content_english['title'],
                    content=content_english['content'],
                    search_results=[],
                    status='published' if result_english['posting_info'].get('page_id') else 'draft',
                    language='english'
                )
                
                # 포스팅 성공 시 업데이트
                if result_english['posting_info'].get('page_id'):
                    db.update_post_published(
                        post_id_english,
                        result_english['posting_info']['page_id'],
                        result_english['posting_info'].get('page_url', '')
                    )
                
                print(f"\n✅ 영문 포스팅 완료!")
                if result_english['posting_info'].get('page_url'):
                    print(f"   URL: {result_english['posting_info']['page_url']}")
            except ValueError as e:
                if "중복" in str(e):
                    print(f"  ⏭️  중복 포스트: {e}")
                else:
                    raise
        else:
            print(f"  ❌ 영문 포스팅 실패: {result_english.get('message', '알 수 없는 오류')}")
    except Exception as e:
        print(f"  ❌ 영문 포스팅 오류: {e}")
        import traceback
        traceback.print_exc()
    
    # 키워드 상태 업데이트
    db.update_keyword_last_checked(keyword_id)
    db.update_keyword_last_posted(keyword_id)
    
    # 다음 키워드 자동 추론 및 추가
    print(f"\n{'='*60}")
    print(f"🔮 다음 키워드 추론 중...")
    print(f"{'='*60}\n")
    
    try:
        inference_agent = KeywordInferenceAgent()
        
        # 이전 포스팅 수집
        previous_posts = db.get_recent_posts_for_keyword(keyword_id, limit=5)
        parent_posts = db.get_recent_posts_for_parent_keywords(keyword_id, limit=5)
        all_previous_posts = (previous_posts + parent_posts)[:10]  # 최대 10개
        
        # 학습 경로 가져오기
        learning_path = db.get_keyword_learning_path(keyword_id)
        
        inference_input = {
            "keyword": keyword_name,
            "previous_posts": all_previous_posts,
            "learning_path": learning_path
        }
        
        inference_result = inference_agent.process(inference_input)
        
        if inference_result.get("status") == "success":
            next_keyword = inference_result.get("next_keyword")
            reason = inference_result.get("reason", "")
            learning_level = inference_result.get("learning_level", "intermediate")
            connection = inference_result.get("connection", "")
            
            print(f"  💡 추론된 다음 키워드: '{next_keyword}'")
            print(f"     이유: {reason}")
            print(f"     연결고리: {connection}")
            
            # 다음 키워드가 이미 존재하는지 확인
            existing_keyword = db.get_keyword_by_name(next_keyword)
            
            if not existing_keyword:
                # 새 키워드 추가
                next_keyword_id = db.add_keyword(
                    keyword=next_keyword,
                    notion_page_id=notion_page_id,
                    parent_keyword_id=keyword_id,  # 현재 키워드를 부모로
                    learning_level=learning_level
                )
                print(f"  ✅ 다음 키워드 '{next_keyword}' 추가됨 (ID: {next_keyword_id})")
                
                # 완전 자동화: 현재 키워드 비활성화, 다음 키워드 자동 활성화
                auto_activate = os.getenv("AUTO_ACTIVATE_NEXT_KEYWORD", "false").lower() == "true"
                
                if auto_activate:
                    # 현재 키워드 비활성화 (오늘 포스팅 완료했으므로)
                    db.toggle_keyword(keyword_name)
                    # 다음 키워드 활성화
                    db.toggle_keyword(next_keyword)
                    print(f"  🔄 완전 자동화 모드: 현재 키워드 '{keyword_name}' 비활성화, 다음 키워드 '{next_keyword}' 자동 활성화")
                else:
                    print(f"  💡 현재 키워드 '{keyword_name}'는 활성화 상태를 유지합니다.")
                    print(f"     다음 키워드 '{next_keyword}'를 활성화하려면:")
                    print(f"     python3 main.py toggle-keyword \"{next_keyword}\"")
                    print(f"     (완전 자동화를 원하시면 .env에 AUTO_ACTIVATE_NEXT_KEYWORD=true 추가)")
            else:
                print(f"  ℹ️  다음 키워드 '{next_keyword}'는 이미 존재합니다.")
                
                # 완전 자동화: 기존 키워드가 있으면 자동 활성화
                auto_activate = os.getenv("AUTO_ACTIVATE_NEXT_KEYWORD", "false").lower() == "true"
                
                if auto_activate and not existing_keyword.get('is_active'):
                    # 현재 키워드 비활성화
                    db.toggle_keyword(keyword_name)
                    # 다음 키워드 활성화
                    db.toggle_keyword(next_keyword)
                    print(f"  🔄 완전 자동화 모드: 기존 키워드 '{next_keyword}' 자동 활성화")
                
        else:
            print(f"  ⚠️  다음 키워드 추론 실패: {inference_result.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"  ⚠️  다음 키워드 추론 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"✅ 자동 포스팅 완료!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    process_single_keyword_dual_language()

