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
    - 한자 검사
    - 외국어 검사 (베트남어, 중국어 등)
    
    Returns:
        (is_valid, error_message)
    """
    # 한자 검사 (한자 범위: \u4e00-\u9fff)
    hanja_pattern = re.compile(r'[\u4e00-\u9fff]+')
    title_hanja = hanja_pattern.findall(title)
    content_hanja = hanja_pattern.findall(content)
    
    if title_hanja:
        return False, f"제목에 한자가 포함되어 있습니다: {', '.join(title_hanja[:3])}"
    
    if content_hanja:
        return False, f"본문에 한자가 포함되어 있습니다: {', '.join(content_hanja[:3])}"
    
    # 외국어 특수 문자 검사 (베트남어, 스페인어, 프랑스어, 독일어 등)
    # 라틴 확장 문자 범위 검사 (U+00C0-U+024F)
    foreign_chars_pattern = re.compile(r'[\u00C0-\u024F]')
    title_foreign = foreign_chars_pattern.findall(title)
    content_foreign = foreign_chars_pattern.findall(content)
    
    if title_foreign:
        return False, f"제목에 외국어 문자가 포함되어 있습니다: {', '.join(set(title_foreign[:5]))}"
    
    if content_foreign:
        return False, f"본문에 외국어 문자가 포함되어 있습니다: {', '.join(set(content_foreign[:5]))}"
    
    # 외국어 단어 패턴 검사 (예: interesant, interesante 등)
    # 한글이 아닌 연속된 알파벳 단어 중 일반적이지 않은 패턴
    foreign_word_patterns = [
        r'\binteresant\w*\b',  # interesant, interesante
        r'\bkhá\w*\b',  # khá
    ]
    for pattern in foreign_word_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return False, f"제목에 외국어 단어가 포함되어 있습니다"
        if re.search(pattern, content, re.IGNORECASE):
            return False, f"본문에 외국어 단어가 포함되어 있습니다: {pattern}"
    
    # 한글 비율 검사
    if not is_korean_text(title, threshold=0.5):
        return False, "제목이 한글로 작성되지 않았습니다."
    
    if not is_korean_text(content, threshold=0.7):
        return False, "본문이 한글로 작성되지 않았습니다. (한글 비율 70% 미만)"
    
    return True, ""


def remove_hanja_from_text(text: str) -> str:
    """
    텍스트에서 한자 및 모든 외국어 특수 문자를 제거
    - 한자 제거 (\u4e00-\u9fff)
    - 모든 라틴 확장 문자 제거 (\u00C0-\u024F)
    - 외국어 단어 제거 (interesant, khá 등)
    - 한글, 기본 영어, 숫자, 기본 구두점만 남김
    """
    if not text:
        return text
    
    cleaned = text
    
    # 외국어 단어 패턴 제거 (먼저 제거)
    foreign_words = [
        (r'\binteresant\w*\b', ''),  # interesant, interesante
        (r'\bkhá\w*\b', ''),  # khá
        (r'\bkh\s', ' '),  # 불완전한 "kh" 조각 제거
    ]
    for pattern, replacement in foreign_words:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    
    # 한자 범위 제거 (\u4e00-\u9fff)
    hanja_pattern = re.compile(r'[\u4e00-\u9fff]')
    cleaned = hanja_pattern.sub('', cleaned)
    
    # 모든 라틴 확장 문자 제거 (U+00C0-U+024F)
    # 이 범위에는 베트남어, 스페인어, 프랑스어, 독일어 등 모든 유럽 언어 특수 문자가 포함됨
    latin_extended_pattern = re.compile(r'[\u00C0-\u024F]')
    cleaned = latin_extended_pattern.sub('', cleaned)
    
    # 연속된 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # 앞뒤 공백 제거
    cleaned = cleaned.strip()
    
    return cleaned


def remove_foreign_characters_from_text(text: str) -> str:
    """
    텍스트에서 모든 외국어 특수 문자 제거 (한자 포함)
    remove_hanja_from_text의 별칭
    """
    return remove_hanja_from_text(text)

