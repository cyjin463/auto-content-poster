#!/usr/bin/env python3
"""
자동 포스팅 메인 스크립트
- 키워드 하나만 처리
- 한글 1개 + 영문 1개 포스팅
- 중복 방지
- 출처 및 면책문구 필수
"""

import sys
from datetime import datetime, timedelta, timezone
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
    has_disclaimer = "본 글은 AI를 활용하여" in content or "본 글의 정보는 100%" in content or "information in this article may not be 100%" in content
    
    if not has_sources:
        # 출처 섹션 추가 필요 (경고)
        print("  ⚠️  경고: 출처 섹션이 없습니다.")
    
    if not has_disclaimer:
        # 면책 문구 추가
        if "## 참고 출처" in content or "References" in content:
            # 출처 다음에 추가
            if "## References" in content:
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ This article was generated using AI. The information may not be 100% accurate. Please use it as a reference.</span>"
            else:
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글은 AI를 활용하여 작성되었습니다. 일부 정보는 정확하지 않을 수 있으니 참고용으로만 활용해 주세요.</span>"
        else:
            # 끝에 추가
            if any(keyword in content.lower() for keyword in ['the', 'is', 'are', 'this', 'that']):
                # 영문으로 판단
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ This article was generated using AI. The information may not be 100% accurate. Please use it as a reference.</span>"
            else:
                # 한글로 판단
                content += "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글은 AI를 활용하여 작성되었습니다. 일부 정보는 정확하지 않을 수 있으니 참고용으로만 활용해 주세요.</span>"
    
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
    
    # 한국 시간(KST, UTC+9) 기준으로 오늘 이미 포스팅했는지 확인
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    
    # 오늘 오전 7시 기준 (한국 시간)
    today_7am_kst = now_kst.replace(hour=7, minute=0, second=0, microsecond=0)
    
    last_posted = db.get_keyword_last_posted(keyword_id)
    
    if last_posted:
        # last_posted가 naive datetime이면 한국 시간대로 가정하고 비교
        if last_posted.tzinfo is None:
            last_posted_kst = last_posted.replace(tzinfo=kst)
        else:
            last_posted_kst = last_posted.astimezone(kst)
        
        # 오늘 7시 이후에 포스팅이 있었는지 확인
        if last_posted_kst >= today_7am_kst:
            print(f"⏭️  오늘(한국 시간 기준) 이미 포스팅되었습니다. (마지막 포스팅: {last_posted_kst.strftime('%Y-%m-%d %H:%M:%S KST')})")
            return
    
    chain = AgentChain()
    
    # 1. 한글 콘텐츠 생성 및 포스팅
    print(f"\n📝 [1/2] 한글 콘텐츠 생성 중...\n")
    content_korean = None
    page_url_korean = None
    post_id_korean = None
    rate_limit_error = False
    try:
        result_korean = chain.process(keyword_name, notion_page_id, language='korean', skip_posting=True)
        
        if result_korean["status"] == "success":
            content_korean = result_korean['generated_content']
            content_korean['content'] = ensure_sources_and_disclaimer(content_korean['content'])
            
            # 한글 포스팅 (skip_posting=True로 설정했으므로 여기서 포스팅)
            print(f"  📝 한글 포스팅 중...")
            from notion_api import create_notion_page
            notion_result_korean = create_notion_page(
                title=content_korean['title'],
                content=content_korean['content'],
                parent_page_id=notion_page_id,
                database_id=os.getenv("NOTION_DATABASE_ID")
            )
            
            page_id_korean = None
            if notion_result_korean.get("status") == "success":
                page_id_korean = notion_result_korean.get('page_id')
                page_url_korean = notion_result_korean.get('page_url')
                print(f"  ✅ 한글 포스팅 완료: {page_url_korean or ''}")
            else:
                print(f"  ❌ 한글 포스팅 실패")
                return
            
            # 데이터베이스에 저장
            try:
                post_id_korean = db.create_post(
                    keyword_id=keyword_id,
                    title=content_korean['title'],
                    content=content_korean['content'],
                    search_results=[],
                    status='published',
                    language='korean'
                )
                
                if page_id_korean:
                    db.update_post_published(post_id_korean, page_id_korean, page_url_korean or '')
            except ValueError as e:
                if "중복" in str(e):
                    print(f"  ⏭️  중복 포스트: {e}")
                    # 중복이어도 계속 진행
                else:
                    raise
            
            print(f"  ✅ 한글 콘텐츠 생성 및 저장 완료")
        else:
            error_msg = result_korean.get('message', '알 수 없는 오류')
            print(f"  ❌ 한글 콘텐츠 생성 실패: {error_msg}")
            # Rate Limit 에러 체크
            if "rate_limit" in str(error_msg).lower() or "Rate limit" in str(error_msg):
                rate_limit_error = True
                print(f"  ⚠️  Rate Limit 감지: 키워드는 변환하되 포스팅은 건너뜁니다.")
            else:
                return
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ 한글 콘텐츠 생성 오류: {e}")
        # Rate Limit 에러 체크
        if "rate_limit" in error_str.lower() or "Rate limit" in error_str:
            rate_limit_error = True
            print(f"  ⚠️  Rate Limit 감지: 키워드는 변환하되 포스팅은 건너뜁니다.")
        else:
            import traceback
            traceback.print_exc()
            return
    
    # 2. 영문 콘텐츠 생성 및 포스팅
    print(f"\n📝 [2/2] 영문 콘텐츠 생성 중...\n")
    content_english = None
    page_url_english = None
    post_id_english = None
    try:
        result_english = chain.process(keyword_name, notion_page_id, language='english', skip_posting=True)
        
        if result_english["status"] == "success":
            content_english = result_english['generated_content']
            content_english['content'] = ensure_sources_and_disclaimer(content_english['content'])
            
            # 영문 포스팅 (skip_posting=True로 설정했으므로 여기서 포스팅)
            print(f"  📝 영문 포스팅 중...")
            from notion_api import create_notion_page
            notion_result_english = create_notion_page(
                title=content_english['title'],
                content=content_english['content'],
                parent_page_id=notion_page_id,
                database_id=os.getenv("NOTION_DATABASE_ID")
            )
            
            page_id_english = None
            if notion_result_english.get("status") == "success":
                page_id_english = notion_result_english.get('page_id')
                page_url_english = notion_result_english.get('page_url')
                print(f"  ✅ 영문 포스팅 완료: {page_url_english or ''}")
            else:
                print(f"  ❌ 영문 포스팅 실패")
                return
            
            # 데이터베이스에 저장
            try:
                post_id_english = db.create_post(
                    keyword_id=keyword_id,
                    title=content_english['title'],
                    content=content_english['content'],
                    search_results=[],
                    status='published',
                    language='english'
                )
                
                if page_id_english:
                    db.update_post_published(post_id_english, page_id_english, page_url_english or '')
            except ValueError as e:
                if "중복" in str(e):
                    print(f"  ⏭️  중복 포스트: {e}")
                    # 중복이어도 계속 진행
                else:
                    raise
            
            print(f"  ✅ 영문 콘텐츠 생성 및 저장 완료")
        else:
            error_msg = result_english.get('message', '알 수 없는 오류')
            print(f"  ❌ 영문 콘텐츠 생성 실패: {error_msg}")
            # Rate Limit 에러 체크
            if "rate_limit" in str(error_msg).lower() or "Rate limit" in str(error_msg):
                rate_limit_error = True
                print(f"  ⚠️  Rate Limit 감지: 키워드는 변환하되 포스팅은 건너뜁니다.")
            else:
                return
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ 영문 콘텐츠 생성 오류: {e}")
        # Rate Limit 에러 체크
        if "rate_limit" in error_str.lower() or "Rate limit" in error_str:
            rate_limit_error = True
            print(f"  ⚠️  Rate Limit 감지: 키워드는 변환하되 포스팅은 건너뜁니다.")
        else:
            import traceback
            traceback.print_exc()
            return
    
    # 포스팅 성공 시 last_posted 업데이트
    if not rate_limit_error and (page_url_korean or page_url_english):
        print(f"\n✅ 포스팅 완료!")
        if page_url_korean:
            print(f"   한글: {page_url_korean}")
        if page_url_english:
            print(f"   영문: {page_url_english}")
    
    elif rate_limit_error:
        print(f"\n⏭️  Rate Limit으로 인해 포스팅을 건너뜁니다.")
        print(f"   다음 키워드로 변환을 진행합니다.")
    
    # 키워드 상태 업데이트 (Rate Limit이어도 체크 시간은 업데이트)
    db.update_keyword_last_checked(keyword_id)
    # 포스팅 성공한 경우에만 last_posted 업데이트
    if not rate_limit_error and content_korean and content_english:
        db.update_keyword_last_posted(keyword_id)
    
    # 다음 키워드 자동 추론 및 추가
    print(f"\n{'='*60}")
    print(f"🔄 다음 키워드 활성화 중...")
    print(f"{'='*60}\n")
    
    # 커리큘럼 모드: sequence_number 기반으로 다음 키워드 찾기
    use_curriculum = os.getenv("USE_CURRICULUM_MODE", "true").lower() == "true"
    
    if use_curriculum:
        # 현재 키워드의 sequence_number 확인
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sequence_number FROM keywords WHERE id = ?",
            (keyword_id,)
        )
        row = cursor.fetchone()
        current_seq = row['sequence_number'] if row else None
        conn.close()
        
        if current_seq is not None:
            # 다음 순서 키워드 찾기
            next_seq = current_seq + 1
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, keyword FROM keywords WHERE sequence_number = ?",
                (next_seq,)
            )
            next_row = cursor.fetchone()
            conn.close()
            
            if next_row:
                next_keyword_id = next_row['id']
                next_keyword_name = next_row['keyword']
                
                # 완전 자동화: 현재 키워드 비활성화, 다음 키워드 활성화
                auto_activate = os.getenv("AUTO_ACTIVATE_NEXT_KEYWORD", "true").lower() == "true"
                
                if auto_activate:
                    # 현재 키워드 비활성화 (오늘 포스팅 완료했으므로)
                    db.toggle_keyword(keyword_name)
                    # 다음 키워드 활성화
                    db.toggle_keyword(next_keyword_name)
                    print(f"  ✅ 커리큘럼 순서 기반:")
                    print(f"     이전: [{current_seq}] {keyword_name}")
                    print(f"     다음: [{next_seq}] {next_keyword_name}")
                    print(f"  🔄 자동화 모드: 다음 키워드 활성화 완료!")
                else:
                    print(f"  💡 다음 키워드: [{next_seq}] {next_keyword_name}")
                    print(f"     (AUTO_ACTIVATE_NEXT_KEYWORD=true로 설정하면 자동 활성화됩니다)")
            else:
                print(f"  🎉 모든 커리큘럼을 완료했습니다! (현재: [{current_seq}] {keyword_name})")
        else:
            print(f"  ⚠️  '{keyword_name}' 키워드에 순서 번호가 없습니다. AI 추론 모드로 전환합니다.")
            use_curriculum = False
    
    # AI 추론 모드 (커리큘럼 순서가 없을 때만)
    if not use_curriculum:
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
                
                print(f"  💡 AI 추론된 다음 키워드: '{next_keyword}'")
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

