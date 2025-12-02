"""
[DEPRECATED] 이 파일은 더 이상 사용되지 않습니다.
새 구조: src/services/search.py

하위 호환성을 위해 래퍼 제공
"""
import warnings
warnings.warn(
    "search.py는 더 이상 사용되지 않습니다. src.services.search을 사용하세요.",
    DeprecationWarning,
    stacklevel=2
)

from src.services.search import search_keywords, search_keywords_google, search_keywords_duckduckgo

__all__ = ['search_keywords', 'search_keywords_google', 'search_keywords_duckduckgo']
