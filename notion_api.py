"""
[DEPRECATED] 이 파일은 더 이상 사용되지 않습니다.
새 구조: src/services/notion.py

하위 호환성을 위해 래퍼 제공
"""
import warnings
warnings.warn(
    "notion_api.py는 더 이상 사용되지 않습니다. src.services.notion을 사용하세요.",
    DeprecationWarning,
    stacklevel=2
)

from src.services.notion import (
    create_notion_page,
    publish_to_notion_api,
    markdown_to_notion_blocks
)

__all__ = [
    'create_notion_page',
    'publish_to_notion_api',
    'markdown_to_notion_blocks'
]
