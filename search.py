"""
검색 기능 (DuckDuckGo 무료 검색)
"""

import requests
import re
from typing import List, Dict


def search_keywords(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """DuckDuckGo 검색"""
    results = []
    
    try:
        # DuckDuckGo HTML 검색 (더 안정적)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
        # URL 인코딩
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)
        
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
            # DuckDuckGo HTML 구조에 맞춰 파싱
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
                # 간단한 웹 검색 (더 기본적인 방식)
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
                    # 더 간단한 패턴으로 시도
                    link_pattern = r'href="(https?://[^"]+)"[^>]*>([^<]{20,100})</a>'
                    matches = re.finditer(link_pattern, html)
                    
                    seen_links = set()
                    for match in matches:
                        if len(results) >= num_results:
                            break
                        link = match.group(1)
                        title = match.group(2).strip()
                        
                        # 중복 제거 및 필터링
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
        print(f"검색 오류: {e}")
        return []

