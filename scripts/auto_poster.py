#!/usr/bin/env python3
"""
자동 포스팅 메인 스크립트
- 키워드 하나만 처리
- 영문 1개 + 한글 1개 포스팅 (영문 먼저)
- 중복 방지
- 출처 및 면책문구 필수
"""

#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import subprocess

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from src.core.config import load_env_file
load_env_file()

# 모듈 import
from src.core.database import Database
from agents.agent_chain import AgentChain
from agents.keyword_inference_agent import KeywordInferenceAgent


def commit_and_push_posting(keyword: str, timestamp: datetime = None):
    """
    포스팅 완료 후 Git 커밋 및 push
    커밋 메시지: "키워드 : {키워드}, {년}년{월}월{일}일 {시}시{분}분 포스팅 완료"
    예시: "키워드 : 데이터, 2025년12월2일 15시30분 포스팅 완료"
    """
    if timestamp is None:
        # 한국 시간(KST, UTC+9) 기준
        kst = timezone(timedelta(hours=9))
        timestamp = datetime.now(kst)
    
    # 커밋 메시지 형식: "키워드 : 데이터, 2025년12월2일 15시30분 포스팅 완료"
    commit_message = f"키워드 : {keyword}, {timestamp.year}년{timestamp.month}월{timestamp.day}일 {timestamp.hour}시{timestamp.minute}분 포스팅 완료"
    
    try:
        # Git 저장소인지 확인
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"  ⚠️  Git 저장소가 아닙니다. 커밋을 건너뜁니다.")
            return
        
        # 변경사항 확인
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        has_changes = bool(result.stdout.strip())
        
        if has_changes:
            # 변경사항이 있으면 add
            print(f"\n  📝 Git 커밋 준비 중...")
            subprocess.run(
                ["git", "add", "."],
                cwd=project_root,
                check=True,
                capture_output=True
            )
        
        # 커밋 (변경사항이 없어도 빈 커밋 허용 - 포스팅 완료 기록용)
        print(f"  📝 커밋 메시지: {commit_message}")
        if has_changes:
            # 변경사항이 있으면 일반 커밋
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=project_root,
                check=True,
                capture_output=True
            )
        else:
            # 변경사항이 없어도 빈 커밋 생성 (포스팅 완료 기록용)
            print(f"  ℹ️  변경사항 없음. 포스팅 완료 기록을 위한 빈 커밋 생성...")
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", commit_message],
                cwd=project_root,
                check=True,
                capture_output=True
            )
        
        # Push (origin main)
        print(f"  📤 GitHub에 push 중...")
        push_result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode == 0:
            print(f"  ✅ Git push 완료!")
        else:
            print(f"  ⚠️  Git push 실패: {push_result.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Git 커밋/푸시 중 오류: {e}")
    except Exception as e:
        print(f"  ⚠️  Git 커밋/푸시 중 예외 발생: {e}")


def ensure_sources_and_disclaimer(content: str) -> str:
    """출처와 면책문구가 있는지 확인하고 없으면 추가"""
    has_sources = "## 참고 출처" in content or "## References" in content
    
    # 면책 문구 중복 체크 강화 (다양한 패턴 체크, HTML 포함)
    # 면책 문구가 이미 포함되어 있는지 정확히 체크
    disclaimer_patterns = [
        "본 글은 AI를 활용하여",
        "본 글의 정보는 100%",
        "This article was generated using AI",
        "information in this article may not be 100%",
        "article was generated using AI",
        "AI를 활용하여 작성되었습니다",
        "was generated using AI",
        "Please use it as a reference",
        "참고용으로만 활용해 주세요"
    ]
    
    # HTML 태그와 함께 있는 경우도 체크
    has_disclaimer = any(
        pattern in content for pattern in disclaimer_patterns
    ) or (
        "This article was generated" in content and "AI" in content and "reference" in content.lower()
    ) or (
        "AI를 활용하여" in content and "작성되었습니다" in content
    )
    
    if not has_sources:
        # 출처 섹션 추가 필요 (경고)
        print("  ⚠️  경고: 출처 섹션이 없습니다.")
    
    # 면책 문구가 이미 있으면 추가하지 않음 (중복 방지)
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
    else:
        # 이미 면책 문구가 있으면 로그만 출력
        print("  ℹ️  면책 문구가 이미 포함되어 있습니다. 중복 추가하지 않습니다.")
    
    return content


def validate_and_fix_content(content: dict, keyword: str, language: str, validated_results: list = None, max_attempts: int = 3) -> dict:
    """
    콘텐츠 검증 및 수정 (통과될 때까지 반복)
    
    Returns:
        검증 통과된 content dict
    """
    from agents.validation_agent import ContentValidationAgent
    from agents.fact_check_agent import ContentRevisionAgent
    
    validation_agent = ContentValidationAgent()
    revision_agent = ContentRevisionAgent()
    
    attempt = 0
    current_content = content['content']
    current_title = content['title']
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n  🔍 [{attempt}/{max_attempts}] {language.upper()} 콘텐츠 검증 중...")
        
        validation_input = {
            "keyword": keyword,
            "title": current_title,
            "content": current_content,
            "language": language
        }
        validation_result = validation_agent.process(validation_input)
        
        if validation_result.get("is_valid", False):
            print(f"  ✅ 검증 통과! (품질 점수: {validation_result.get('quality_score', 'N/A')})")
            content['content'] = current_content
            content['title'] = current_title
            return content
        
        # 검증 실패 시 수정
        issues = validation_result.get("issues", [])
        print(f"  ⚠️  검증 실패: {len(issues)}개 이슈 발견")
        
        # 키워드/카테고리/출처 섹션 분리
        import re
        footer_pattern = r'(\n\n## (?:참고 출처|References|카테고리|Category|관련 키워드|Related Keywords).*$)'
        footer_match = re.search(footer_pattern, current_content, re.DOTALL)
        footer_section = footer_match.group(1) if footer_match else ""
        main_content = current_content[:footer_match.start()] if footer_match else current_content
        
        revision_input = {
            "content": main_content,
            "title": current_title,
            "issues": issues,
            "search_results": validated_results or [],
            "language": language
        }
        
        revision_result = revision_agent.process(revision_input)
        
        if revision_result.get("status") == "revised":
            revised_content = revision_result.get("revised_content", main_content)
            
            # 한글 모드일 때 한자/외국어 제거
            if language == 'korean':
                from src.utils.helpers import remove_hanja_from_text
                revised_content = remove_hanja_from_text(revised_content)
            
            # footer 섹션 다시 추가
            if footer_section:
                revised_content = revised_content + footer_section
            
            current_content = revised_content
            print(f"  ✅ 수정 완료 ({len(revision_result.get('revisions', []))}개 수정)")
        else:
            print(f"  ⚠️  수정 실패")
            break
    
    print(f"  ❌ 최대 시도 횟수({max_attempts})에 도달했으나 검증을 통과하지 못했습니다.")
    print(f"  ❌ 검증 실패로 포스팅을 중단합니다.")
    # 검증 실패 시 None 반환하여 포스팅 중단
    return None


def process_single_keyword_dual_language():
    """단일 키워드를 영문/한글 각 1개씩 포스팅 (영문 먼저)"""
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
    
    # 토요일(5), 일요일(6) 체크 - 포스팅 건너뛰기
    weekday = now_kst.weekday()  # 0=월요일, 5=토요일, 6=일요일
    if weekday == 5:  # 토요일
        print(f"⏭️  토요일(한국 시간)이므로 포스팅을 건너뜁니다.")
        return
    if weekday == 6:  # 일요일
        print(f"⏭️  일요일(한국 시간)이므로 포스팅을 건너뜁니다.")
        return
    
    # 오늘 오전 9시 10분 기준 (한국 시간, GROQ 초기화 후)
    today_9_10am_kst = now_kst.replace(hour=9, minute=10, second=0, microsecond=0)
    
    last_posted = db.get_keyword_last_posted(keyword_id)
    
    if last_posted:
        # last_posted가 naive datetime이면 한국 시간대로 가정하고 비교
        if last_posted.tzinfo is None:
            last_posted_kst = last_posted.replace(tzinfo=kst)
        else:
            last_posted_kst = last_posted.astimezone(kst)
        
        # 오늘 9시 10분 이후에 포스팅이 있었는지 확인
        if last_posted_kst >= today_9_10am_kst:
            print(f"⏭️  오늘(한국 시간 기준) 이미 포스팅되었습니다. (마지막 포스팅: {last_posted_kst.strftime('%Y-%m-%d %H:%M:%S KST')})")
            return
    
    chain = AgentChain()
    
    # ============================================================
    # 1단계: 영문 콘텐츠 생성, 검증, 포스팅
    # ============================================================
    print(f"\n📝 [1/2] 영문 콘텐츠 생성 및 포스팅\n")
    content_english = None
    page_url_english = None
    post_id_english = None
    rate_limit_error = False
    
    try:
        result_english = chain.process(keyword_name, notion_page_id, language='english', skip_posting=True)
        
        if result_english["status"] == "success":
            content_english = result_english['generated_content']
            validated_results = result_english.get('validated_results', [])
            
            # 영문 콘텐츠 검증 (통과될 때까지 반복)
            print(f"\n  🔍 영문 콘텐츠 검증 시작...")
            content_english = validate_and_fix_content(
                content_english,
                keyword_name,
                'english',
                validated_results,
                max_attempts=3
            )
            
            # 검증 실패 시 경고만 하고 계속 진행 (한글 포함만 체크)
            if content_english is None:
                print(f"  ⚠️  영문 콘텐츠 검증 실패했지만, 한글 포함 여부를 재확인 후 진행합니다.")
                # 한글 포함 여부만 재확인
                from src.utils.helpers import remove_korean_from_english_text
                # content_english가 None이므로 다시 가져오기
                content_english = result_english['generated_content']
                original_content = content_english['content']
                original_title = content_english['title']
                
                # 한글 제거 후 재확인
                cleaned_content = remove_korean_from_english_text(original_content)
                cleaned_title = remove_korean_from_english_text(original_title)
                
                # 한글이 제거되었다면 경고만 하고 계속 진행
                import re
                korean_pattern = re.compile(r'[가-힣]')
                has_korean = bool(korean_pattern.search(cleaned_content + cleaned_title))
                
                if has_korean:
                    print(f"  ❌ 영문 콘텐츠에 한글이 포함되어 포스팅을 중단합니다.")
                    rate_limit_error = True
                    raise Exception("영문 콘텐츠 검증 실패: 한글 포함")
                else:
                    print(f"  ⚠️  한글 포함은 없지만 품질 검증 실패. 경고 후 계속 진행합니다.")
                    content_english['content'] = cleaned_content
                    content_english['title'] = cleaned_title
            
            # 출처 및 면책문구 확인
            content_english['content'] = ensure_sources_and_disclaimer(content_english['content'])
            
            # 영문 포스팅
            print(f"\n  📝 영문 포스팅 중...")
            from src.services.notion import create_notion_page
            database_id = os.getenv("NOTION_DATABASE_ID")
            
            notion_result_english = create_notion_page(
                title=content_english['title'],
                content=content_english['content'],
                parent_page_id=notion_page_id,
                database_id=database_id
            )
            
            if notion_result_english and notion_result_english.get("status") == "success":
                page_id_english = notion_result_english.get('page_id')
                page_url_english = notion_result_english.get('page_url')
                print(f"  ✅ 영문 포스팅 완료!")
                print(f"     페이지 ID: {page_id_english}")
                print(f"     페이지 URL: {page_url_english or 'N/A'}")
                
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
                        # 학습용 캐시 업데이트 (영문 최근 2건 유지)
                        db.update_learning_cache(
                            post_id=post_id_english,
                            language='english',
                            title=content_english['title'],
                            content=content_english['content']
                        )
                except ValueError as e:
                    if "중복" in str(e):
                        print(f"  ⏭️  중복 포스트: {e}")
                    else:
                        raise
            else:
                error_msg = notion_result_english.get("message", "알 수 없는 오류") if notion_result_english else "결과를 받지 못함"
                print(f"  ❌ 영문 포스팅 실패: {error_msg}")
                return
        else:
            error_msg = result_english.get('message', '알 수 없는 오류')
            print(f"  ❌ 영문 콘텐츠 생성 실패: {error_msg}")
            if "rate_limit" in str(error_msg).lower() or "Rate limit" in str(error_msg):
                rate_limit_error = True
                print(f"  ⚠️  Rate Limit 감지: 포스팅을 건너뜁니다.")
            else:
                return
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ 영문 콘텐츠 생성 오류: {e}")
        if "rate_limit" in error_str.lower() or "Rate limit" in error_str:
            rate_limit_error = True
        else:
            import traceback
            traceback.print_exc()
            return
    
    # ============================================================
    # 2단계: 한글 콘텐츠 생성 (영문 기반 번역), 검증, 포스팅
    # ============================================================
    print(f"\n📝 [2/2] 한글 콘텐츠 생성 및 포스팅 (영문 기반 번역)\n")
    content_korean = None
    page_url_korean = None
    post_id_korean = None
    
    # 1단계에서 생성된 영문 콘텐츠가 없으면 종료
    if not content_english:
        print(f"  ❌ 영문 콘텐츠가 없어 한글 포스팅을 건너뜁니다.")
        return
    
    try:
        # 1단계에서 생성된 영문 콘텐츠를 직접 한글로 번역
        print(f"  🔄 1단계에서 생성된 영문 콘텐츠를 한글로 번역 중...")
        from agents.content_agent import ContentGenerationAgent
        import json
        from src.utils.format_fixer import fix_korean_content_format
        
        agent = ContentGenerationAgent()
        
        english_title = content_english['title']
        english_content_text = content_english['content']
        
        # 번역 프롬프트 준비 (형식 유지 강화)
        translation_prompt = f"""다음 영문 블로그 포스트를 자연스러운 한국어로 번역해주세요.

🚨🚨🚨 **절대적 명령: 반드시 한글로만 번역! 형식 반드시 유지!** 🚨🚨🚨

⚠️ 매우 중요 (절대 위반 불가):

1. **언어 규칙**: 반드시 한글로만 번역 (제목, 본문 모두)

2. **구조 유지 (매우 중요)**:
   - ⚠️ 반드시 서론-본론(3-4개 소제목)-결론 구조 유지
   - 서론: 2-3개 문단, 각 문단 사이 빈 줄(\\n\\n) 필수
   - 본론: 3-4개 소제목(##), 각 소제목 다음 빈 줄(\\n\\n) 필수, 각 문단 사이 빈 줄(\\n\\n) 필수
   - 결론: 2-3개 문단, 각 문단 사이 빈 줄(\\n\\n) 필수

3. **빈 줄 규칙 (절대 필수)**:
   - 모든 소제목(##) 다음: 반드시 빈 줄(\\n\\n) 1개
   - 모든 문단 끝(마침표 다음): 반드시 빈 줄(\\n\\n) 1개
   - **서론** 제목 다음: 반드시 빈 줄(\\n\\n) 1개
   - **본론** 제목 다음: 반드시 빈 줄(\\n\\n) 1개

4. **절대 금지**:
   - 띄어쓰기 없이 통으로 작성하면 절대 안 됩니다!
   - 문단 구분 없이 한 덩어리로 작성하면 절대 안 됩니다!
   - 소제목 다음 빈 줄 없이 바로 본문 작성하면 절대 안 됩니다!

영문 제목:
{english_title}

영문 본문:
{english_content_text[:4000]}

⚠️ **중요**: 영문 본문의 형식(빈 줄, 소제목 구조)을 그대로 유지하면서 번역하세요!

📋 **형식 예시** (전전 포스팅처럼):
```
**서론**

첫 번째 문단입니다.

두 번째 문단입니다.

**본론**

## 소제목 1

본문 내용입니다.

## 소제목 2

본문 내용입니다.

**결론**

결론 문단입니다.
```

⚠️ 위 예시처럼 문단 사이, 소제목 다음 반드시 빈 줄이 있어야 합니다!

다음 JSON 형식으로 응답해주세요:
{{
  "title": "번역된 한글 제목 (15자 이내)",
  "content": "번역된 한글 본문 (⚠️ 반드시 빈 줄 포함, JSON에서 \\\\n으로 표현, 소제목 다음 \\\\n\\\\n, 문단 끝 다음 \\\\n\\\\n)"
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
        korean_content_text = translated_content.get("content", "")
        
        # 이스케이프 복구
        if '\\n' in korean_content_text:
            korean_content_text = korean_content_text.replace('\\n', '\n')
        
        # 형식 자동 수정
        korean_content_text = fix_korean_content_format(korean_content_text)
        print(f"  🔧 번역 후 형식 자동 수정 완료")
        
        # 한자/외국어 제거
        from src.utils.helpers import remove_hanja_from_text
        korean_content_text = remove_hanja_from_text(korean_content_text)
        korean_title = remove_hanja_from_text(korean_title)
        
        # content_korean 딕셔너리 생성
        content_korean = {
            'title': korean_title,
            'content': korean_content_text,
            'summary': content_english.get('summary', ''),
            'keywords': content_english.get('keywords', []),
            'category': content_english.get('category', 'IT/컴퓨터')
        }
        
        validated_results_korean = []
        
        # 기존 체인 프로세스 결과를 시뮬레이션
        result_korean = {
            'status': 'success',
            'generated_content': content_korean
        }
        
        if result_korean["status"] == "success":
            # 한글 콘텐츠 검증 (형식 및 언어 - 통과될 때까지 반복)
            print(f"\n  🔍 한글 콘텐츠 검증 시작... (형식 및 언어)")
            content_korean = validate_and_fix_content(
                content_korean,
                keyword_name,
                'korean',
                validated_results_korean,
                max_attempts=3
            )
            
            # 검증 실패 시 경고만 하고 계속 진행 (외국어 포함만 체크)
            if content_korean is None:
                print(f"  ⚠️  한글 콘텐츠 검증 실패했지만, 외국어 포함 여부를 재확인 후 진행합니다.")
                # 외국어(일본어, 중국어 등) 포함 여부만 재확인
                from src.utils.helpers import remove_hanja_from_text
                # content_korean이 None이므로 다시 가져오기
                content_korean = result_korean['generated_content']
                original_content = content_korean['content']
                original_title = content_korean['title']
                
                # 한자/외국어 제거 후 재확인
                cleaned_content = remove_hanja_from_text(original_content)
                cleaned_title = remove_hanja_from_text(original_title)
                
                # 한자/외국어 제거 여부 확인
                import re
                hanja_pattern = re.compile(r'[一-龯\u3040-\u309F\u30A0-\u30FF\u3400-\u4DBF\u4E00-\u9FAF]')
                has_foreign_chars = bool(hanja_pattern.search(cleaned_content + cleaned_title))
                
                if has_foreign_chars:
                    print(f"  ❌ 한글 콘텐츠에 한자/일본어 등 외국어가 포함되어 포스팅을 중단합니다.")
                    raise Exception("한글 콘텐츠 검증 실패: 한자/외국어 포함")
                else:
                    print(f"  ⚠️  외국어 포함은 없지만 품질/비율 검증 실패. 경고 후 계속 진행합니다.")
                    content_korean['content'] = cleaned_content
                    content_korean['title'] = cleaned_title
            
            # 출처 및 면책문구 확인
            content_korean['content'] = ensure_sources_and_disclaimer(content_korean['content'])
            
            # 한글 포스팅
            print(f"\n  📝 한글 포스팅 중...")
            from src.services.notion import create_notion_page
            database_id = os.getenv("NOTION_DATABASE_ID")
            
            if not database_id and not notion_page_id:
                print(f"  ❌ 한글 포스팅 실패: NOTION_DATABASE_ID 또는 NOTION_PARENT_PAGE_ID가 설정되지 않았습니다.")
                return
            
            notion_result_korean = create_notion_page(
                title=content_korean['title'],
                content=content_korean['content'],
                parent_page_id=notion_page_id,
                database_id=database_id
            )
            
            if notion_result_korean and notion_result_korean.get("status") == "success":
                page_id_korean = notion_result_korean.get('page_id')
                page_url_korean = notion_result_korean.get('page_url')
                print(f"  ✅ 한글 포스팅 완료!")
                print(f"     페이지 ID: {page_id_korean}")
                print(f"     페이지 URL: {page_url_korean or 'N/A'}")
                
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
                        # 학습용 캐시 업데이트 (한글 최근 2건 유지)
                        db.update_learning_cache(
                            post_id=post_id_korean,
                            language='korean',
                            title=content_korean['title'],
                            content=content_korean['content']
                        )
                except ValueError as e:
                    if "중복" in str(e):
                        print(f"  ⏭️  중복 포스트: {e}")
                    else:
                        raise
            else:
                error_msg = notion_result_korean.get("message", "알 수 없는 오류") if notion_result_korean else "결과를 받지 못함"
                print(f"  ❌ 한글 포스팅 실패: {error_msg}")
                return
        else:
            error_msg = result_korean.get('message', '알 수 없는 오류')
            print(f"  ❌ 한글 콘텐츠 생성 실패: {error_msg}")
            if "rate_limit" in str(error_msg).lower() or "Rate limit" in str(error_msg):
                rate_limit_error = True
                print(f"  ⚠️  Rate Limit 감지: 포스팅을 건너뜁니다.")
            else:
                return
    except Exception as e:
        error_str = str(e)
        print(f"  ❌ 한글 콘텐츠 생성 오류: {e}")
        if "rate_limit" in error_str.lower() or "Rate limit" in error_str:
            rate_limit_error = True
        else:
            import traceback
            traceback.print_exc()
            return
    
    # ============================================================
    # 3단계: 포스팅 완료 및 키워드 변경
    # ============================================================
    if not rate_limit_error and page_url_english and page_url_korean:
        print(f"\n✅ 포스팅 완료!")
        print(f"   영문: {page_url_english}")
        print(f"   한글: {page_url_korean}")
        
        # 키워드 상태 업데이트
        db.update_keyword_last_checked(keyword_id)
        db.update_keyword_last_posted(keyword_id)
        
        # Git 커밋 및 push (포스팅 완료 기록)
        print(f"\n{'='*60}")
        print(f"📝 Git 커밋 및 Push")
        print(f"{'='*60}\n")
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        commit_and_push_posting(keyword_name, now_kst)
        
        # Git 커밋 및 push
        print(f"\n{'='*60}")
        print(f"📝 Git 커밋 및 Push")
        print(f"{'='*60}\n")
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst)
        commit_and_push_posting(keyword_name, now_kst)
        
        # 다음 키워드 활성화
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
                        # 현재 키워드 비활성화
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
                print(f"  ⚠️  '{keyword_name}' 키워드에 순서 번호가 없습니다.")
    else:
        print(f"\n⏭️  포스팅 완료되지 않았습니다. 키워드는 변경하지 않습니다.")
    
    # ============================================================
    # 4단계: 자기 학습 (최근 4건 분석)
    # ============================================================
    if not rate_limit_error and content_english and content_korean:
        print(f"\n{'='*60}")
        print(f"📚 자기 학습 시작 (최근 4건 분석)")
        print(f"{'='*60}\n")
        
        # 한글 포스팅 분석 (캐시에서 최근 2건 가져오기)
        print(f"  📚 한글 포스팅 분석 중... (캐시에서 최근 2건)")
        korean_posts = db.get_cached_posts_for_learning('korean', limit=2)
        if korean_posts:
            print(f"     캐시된 한글 포스팅 {len(korean_posts)}건 발견 (Notion 참조 없음)")
            # ContentGenerationAgent의 분석 기능 활용
            from agents.content_agent import ContentGenerationAgent
            content_agent = ContentGenerationAgent()
            korean_analysis = content_agent._analyze_previous_posts_from_cache('korean', keyword_name, korean_posts)
            print(f"     ✅ 한글 포스팅 분석 완료")
        else:
            print(f"     ⚠️  캐시된 한글 포스팅이 없습니다. (최초 포스팅 또는 캐시 미구축)")
        
        # 영문 포스팅 분석 (캐시에서 최근 2건 가져오기)
        print(f"  📚 영문 포스팅 분석 중... (캐시에서 최근 2건)")
        english_posts = db.get_cached_posts_for_learning('english', limit=2)
        if english_posts:
            print(f"     캐시된 영문 포스팅 {len(english_posts)}건 발견 (Notion 참조 없음)")
            # ContentGenerationAgent의 분석 기능 활용
            from agents.content_agent import ContentGenerationAgent
            content_agent = ContentGenerationAgent()
            english_analysis = content_agent._analyze_previous_posts_from_cache('english', keyword_name, english_posts)
            print(f"     ✅ 영문 포스팅 분석 완료")
        else:
            print(f"     ⚠️  캐시된 영문 포스팅이 없습니다. (최초 포스팅 또는 캐시 미구축)")
        
        print(f"\n✅ 자기 학습 완료! 다음 포스팅에 개선 사항이 반영됩니다.")


if __name__ == '__main__':
    try:
        process_single_keyword_dual_language()
    finally:
        # 정리 작업 (필요한 경우)
        pass
