"""
[DEPRECATED] 이 파일은 더 이상 사용되지 않습니다.
새 구조: src/utils/helpers.py

하위 호환성을 위해 래퍼 제공
"""
import warnings
warnings.warn(
    "utils.py는 더 이상 사용되지 않습니다. src.utils.helpers를 사용하세요.",
    DeprecationWarning,
    stacklevel=2
)

from src.utils.helpers import (
    is_korean_text,
    validate_korean_content,
    remove_hanja_from_text
)

__all__ = [
    'is_korean_text',
    'validate_korean_content',
    'remove_hanja_from_text'
]
