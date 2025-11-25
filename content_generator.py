"""
AI 콘텐츠 생성 (Groq API 사용)
"""

import os
import json
import requests
from typing import List, Dict
from utils import validate_korean_content


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


# .env 파일 로드
load_env_file()


def generate_content(keywords: str, category: str, search_results: List[Dict]) -> Dict[str, str]:
    """검색 결과 기반 콘텐츠 생성"""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError("GROQ_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    search_summary = "\n".join([
        f"{i+1}. {r['title']}\n   {r['snippet']}\n   출처: {r['link']}"
        for i, r in enumerate(search_results)
    ])
    
    prompt = f"""다음 검색 결과를 기반으로 "{category}" 분야의 "{keywords}"에 대한 전문적이고 유용한 블로그 포스트를 작성해주세요.

검색 결과:
{search_summary}

⚠️ 중요: 반드시 한글로만 작성해주세요. 영어나 다른 언어는 사용하지 마세요.

요구사항:
1. 제목: 매력적이고 SEO 친화적인 제목 (반드시 한글로만)
2. 본문: 최소 1000자 이상의 상세한 내용 (반드시 한글로만)
3. 검색 결과의 정보를 참고하되, 원본을 그대로 복사하지 말고 재구성
4. ⚠️ 반드시 한글로만 작성 (영어, 일본어, 중국어 등 다른 언어 사용 금지)
5. 말투: 30대 초반 평범한 남성의 말투로 작성
   - 자연스럽고 친근한 말투
   - 과하지 않고 차분한 톤
   - 전문적이되 딱딱하지 않음
   - "~입니다", "~네요", "~죠" 같은 평범한 존댓말 사용
   - "~할 수 있습니다", "~가 좋을 것 같아요" 같은 자연스러운 표현
6. 적절한 소제목과 문단 구분
7. 기술 용어는 한글 번역을 우선 사용 (예: "인공지능", "머신러닝")

다음 JSON 형식으로 응답해주세요 (모든 필드가 한글이어야 함):
{{
  "title": "제목 (한글로만)",
  "content": "본문 내용 (마크다운 형식 가능, 한글로만)",
  "summary": "요약 (200자 이내, 한글로만)"
}}"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 30대 초반 평범한 남성 블로그 작가입니다. 검색 결과를 분석하고 독창적이고 유용한 콘텐츠를 작성합니다. ⚠️ 반드시 한글로만 작성해야 합니다. 영어나 다른 언어는 절대 사용하지 마세요. 자연스럽고 친근한 말투를 사용하며, 과하지 않고 차분한 톤으로 작성합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
        },
        timeout=60
    )
    
    if not response.ok:
        raise Exception(f"Groq API 오류: {response.text}")
    
    data = response.json()
    content = json.loads(data["choices"][0]["message"]["content"])
    
    title = content.get("title", "")
    content_text = content.get("content", "")
    summary = content.get("summary", "")
    
    # 한글 검증
    is_valid, error_msg = validate_korean_content(title, content_text)
    if not is_valid:
        print(f"  ⚠️  한글 검증 실패: {error_msg}")
        print(f"  ⚠️  재생성 시도...")
        
        # 재생성 시도 (1회)
        retry_prompt = f"""{prompt}

⚠️ 이전 응답이 한글이 아니었습니다. 반드시 한글로만 다시 작성해주세요.
영어나 다른 언어는 절대 사용하지 마세요."""
        
        retry_response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "당신은 30대 초반 평범한 남성 블로그 작가입니다. ⚠️ 반드시 한글로만 작성해야 합니다. 영어나 다른 언어는 절대 사용하지 마세요. 자연스럽고 친근한 말투를 사용하며, 과하지 않고 차분한 톤으로 작성합니다."
                    },
                    {
                        "role": "user",
                        "content": retry_prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
            },
            timeout=60
        )
        
        if retry_response.ok:
            retry_data = retry_response.json()
            retry_content = json.loads(retry_data["choices"][0]["message"]["content"])
            title = retry_content.get("title", title)
            content_text = retry_content.get("content", content_text)
            summary = retry_content.get("summary", summary)
            
            # 재검증
            is_valid_retry, _ = validate_korean_content(title, content_text)
            if is_valid_retry:
                print(f"  ✅ 한글 재생성 성공")
            else:
                print(f"  ⚠️  재생성 후에도 한글 검증 실패, 경고만 표시")
        else:
            print(f"  ⚠️  재생성 실패, 원본 사용")
    
    # 출처 추가
    sources_section = "\n\n## 참고 출처\n\n"
    sources_list = []
    
    # 검색 결과에서 출처 추출 (중복 제거)
    seen_links = set()
    for result in search_results[:10]:  # 최대 10개 출처
        link = result.get('link', '')
        title_link = result.get('title', '')
        
        if link and link not in seen_links and link.startswith('http'):
            seen_links.add(link)
            sources_list.append(f"- [{title_link}]({link})")
    
    if sources_list:
        sources_section += "\n".join(sources_list)
        sources_section += "\n"
    else:
        sources_section += "검색 결과를 기반으로 작성되었습니다.\n"
    
    # 면책 문구 추가 (티스토리 호환 형식)
    disclaimer = "\n\n---\n\n<span style='color: #666; font-size: 0.9em;'>⚠️ 본 글의 정보는 100% 정확하지 않을 수 있습니다. 참고 자료로 활용하시기 바랍니다.</span>"
    
    content_text = content_text + sources_section + disclaimer
    
    return {
        "title": title,
        "content": content_text,
        "summary": summary
    }

