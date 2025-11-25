"""
검색 기능 (Google Custom Search API 우선, DuckDuckGo 백업)
"""

import requests
import re
import os
from typing import List, Dict
from urllib.parse import quote_plus

# 환경 변수에서 API 키 로드
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
USE_GOOGLE_SEARCH = bool(GOOGLE_API_KEY and GOOGLE_CSE_ID)


def search_keywords_google(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """Google Custom Search API 사용 (하루 100건 무료)"""
    results = []
    
    if not USE_GOOGLE_SEARCH:
        return []
    
    try:
        # Google Custom Search API 호출
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CSE_ID,
            "q": query,
            "num": min(num_results, 10),  # Google API는 한 번에 최대 10개
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.ok:
            data = response.json()
            
            # 검색 결과 파싱
            if "items" in data:
                for item in data["items"][:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
        
        return results[:num_results]
        
    except Exception as e:
        print(f"  ⚠️  Google 검색 오류: {e}")
        return []


def search_keywords_duckduckgo(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """DuckDuckGo 검색 (백업용)"""
    results = []
    
    try:
        # DuckDuckGo HTML 검색
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=15,
            allow_redirects=True
        )
        
        if response.ok:
            html = response.text
            
            # HTML에서 검색 결과 추출 (여러 패턴 시도)
            patterns = [
                # 패턴 1: result__a 클래스
                (r'<a\s+class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r'<a\s+class="result__snippet"[^>]*>([^<]+)</a>'),
                # 패턴 2: result-link 클래스
                (r'<a\s+class="[^"]*result[^"]*link[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r'<a\s+class="[^"]*snippet[^"]*"[^>]*>([^<]+)</a>'),
                # 패턴 3: 일반 링크 패턴
                (r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*result[^"]*"[^>]*>([^<]+)</a>', r'<a[^>]*class="[^"]*snippet[^"]*"[^>]*>([^<]+)</a>'),
            ]
            
            for title_pattern, snippet_pattern in patterns:
                # 제목과 링크 추출
                title_matches = list(re.finditer(title_pattern, html))
                if title_matches:
                    titles_links = []
                    for match in title_matches:
                        link = match.group(1)
                        title = match.group(2).strip()
                        # HTML 엔티티 디코딩
                        title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                        if link and title and (link.startswith('http') or link.startswith('//')):
                            if link.startswith('//'):
                                link = 'https:' + link
                            titles_links.append({"title": title, "link": link})
                    
                    # 스니펫 추출
                    snippet_matches = list(re.finditer(snippet_pattern, html))
                    snippets = []
                    for match in snippet_matches:
                        snippet = match.group(1).strip()
                        snippet = snippet.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
                        snippets.append(snippet)
                    
                    # 결과 조합
                    for i, item in enumerate(titles_links[:num_results]):
                        snippet = snippets[i] if i < len(snippets) else ""
                        results.append({
                            "title": item["title"],
                            "link": item["link"],
                            "snippet": snippet
                        })
                    
                    if results:
                        break
        
        # 결과가 부족하면 Instant Answer API도 시도
        if len(results) < num_results:
            try:
                ia_response = requests.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": "1",
                        "skip_disambig": "1",
                    },
                    timeout=10
                )
                
                if ia_response.ok:
                    data = ia_response.json()
                    
                    # RelatedTopics 처리
                    if data.get("RelatedTopics"):
                        for topic in data["RelatedTopics"]:
                            if len(results) >= num_results:
                                break
                            if isinstance(topic, dict) and topic.get("FirstURL") and topic.get("Text"):
                                title = topic["Text"].split(" - ")[0] if " - " in topic["Text"] else topic["Text"]
                                # 중복 제거
                                if not any(r["link"] == topic["FirstURL"] for r in results):
                                    results.append({
                                        "title": title[:200],
                                        "link": topic["FirstURL"],
                                        "snippet": topic["Text"][:300]
                                    })
                    
                    # Abstract 추가
                    if data.get("AbstractURL") and data.get("Abstract"):
                        if not any(r["link"] == data["AbstractURL"] for r in results):
                            results.insert(0, {
                                "title": data.get("Heading", query)[:200],
                                "link": data.get("AbstractURL"),
                                "snippet": data.get("Abstract", "")[:300]
                            })
            except Exception:
                pass
        
        # 결과가 없으면 간단한 웹 검색 시도
        if not results:
            try:
                simple_response = requests.get(
                    f"https://duckduckgo.com/?q={quote_plus(query)}",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    },
                    timeout=10,
                    allow_redirects=True
                )
                
                if simple_response.ok:
                    html = simple_response.text
                    link_pattern = r'href="(https?://[^"]+)"[^>]*>([^<]{20,100})</a>'
                    matches = re.finditer(link_pattern, html)
                    
                    seen_links = set()
                    for match in matches:
                        if len(results) >= num_results:
                            break
                        link = match.group(1)
                        title = match.group(2).strip()
                        
                        if (link not in seen_links and 
                            link.startswith('http') and 
                            'duckduckgo.com' not in link and
                            len(title) > 10):
                            seen_links.add(link)
                            results.append({
                                "title": title[:200],
                                "link": link,
                                "snippet": title[:300]
                            })
            except Exception:
                pass
        
        return results[:num_results]
        
    except Exception as e:
        print(f"  ⚠️  DuckDuckGo 검색 오류: {e}")
        return []


def search_keywords(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    검색 함수 (Google 우선, 실패 시 DuckDuckGo)
    
    Google Custom Search API를 우선 사용하며, 
    API 키가 없거나 실패 시 DuckDuckGo로 폴백합니다.
    
    환경 변수:
    - GOOGLE_API_KEY: Google Custom Search API 키
    - GOOGLE_CSE_ID: Custom Search Engine ID
    """
    results = []
    
    # Google Search API 사용 가능한 경우
    if USE_GOOGLE_SEARCH:
        results = search_keywords_google(query, num_results)
        if results:
            return results
        # Google 검색 실패 시 DuckDuckGo로 폴백
    
    # DuckDuckGo 검색 (기본값 또는 Google 실패 시)
    results = search_keywords_duckduckgo(query, num_results)
    
    return results
