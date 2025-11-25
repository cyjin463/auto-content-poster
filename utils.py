"""
유틸리티 함수
"""

import re


def is_korean_text(text: str, threshold: float = 0.7) -> bool:
    """
    텍스트가 한글로 작성되었는지 확인
    
    Args:
        text: 확인할 텍스트
        threshold: 한글 비율 임계값 (0.0 ~ 1.0)
    
    Returns:
        True if 한글 비율이 threshold 이상
    """
    if not text:
        return False
    
    # 한글, 공백, 구두점, 숫자만 추출
    korean_pattern = re.compile(r'[가-힣\s.,!?;:()\[\]{}"\'-]')
    korean_chars = korean_pattern.findall(text)
    
    # 한글 문자만 추출 (공백/구두점 제외)
    korean_only = re.compile(r'[가-힣]')
    korean_char_count = len(korean_only.findall(text))
    
    # 전체 문자 수 (공백 제외)
    total_chars = len(re.sub(r'\s', '', text))
    
    if total_chars == 0:
        return False
    
    korean_ratio = korean_char_count / total_chars
    
    return korean_ratio >= threshold


def validate_korean_content(title: str, content: str) -> tuple[bool, str]:
    """
    제목과 본문이 한글로 작성되었는지 검증
    
    Returns:
        (is_valid, error_message)
    """
    if not is_korean_text(title, threshold=0.5):
        return False, "제목이 한글로 작성되지 않았습니다."
    
    if not is_korean_text(content, threshold=0.7):
        return False, "본문이 한글로 작성되지 않았습니다. (한글 비율 70% 미만)"
    
    return True, ""

