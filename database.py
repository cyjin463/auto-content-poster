"""
[DEPRECATED] 이 파일은 더 이상 사용되지 않습니다.
새 구조: src/core/database.py

하위 호환성을 위해 래퍼 제공
"""
import warnings
warnings.warn(
    "database.py는 더 이상 사용되지 않습니다. src.core.database를 사용하세요.",
    DeprecationWarning,
    stacklevel=2
)

from src.core.database import Database

__all__ = ['Database']
