"""
유틸리티 함수
"""

import re


def _calculate_korean_ratio(text: str) -> float:
    """
    텍스트의 한글 비율 계산 (내부 함수)
    
    Returns:
        한글 비율 (0.0 ~ 1.0)
    """
    if not text:
        return 0.0
    
    # 한글 문자만 추출
    korean_only = re.compile(r'[가-힣]')
    korean_char_count = len(korean_only.findall(text))
    
    # 전체 문자 수 (공백, 구두점 제외)
    total_chars = len(re.sub(r'[\s.,!?;:()\[\]{}"\'-]', '', text))
    
    if total_chars == 0:
        return 0.0
    
    return korean_char_count / total_chars


def is_korean_text(text: str, threshold: float = 0.8) -> bool:
    """
    텍스트가 한글로 작성되었는지 확인 (한글이 주가 되어야 함)
    
    Args:
        text: 확인할 텍스트
        threshold: 한글 비율 임계값 (0.0 ~ 1.0, 기본값 0.8 = 80%)
    
    Returns:
        True if 한글 비율이 threshold 이상
    """
    if not text:
        return False
    
    # 한글 문자만 추출
    korean_only = re.compile(r'[가-힣]')
    korean_char_count = len(korean_only.findall(text))
    
    # 전체 문자 수 (공백, 구두점 제외, 한글+영어+숫자만)
    # 기술 용어를 위한 영어는 허용하지만, 전체적으로는 한글이 주가 되어야 함
    total_chars = len(re.sub(r'[\s.,!?;:()\[\]{}"\'-]', '', text))
    
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
    
    # 일본어 문자 검사 (히라가나, 가타카나, 일본어 한자)
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    title_japanese = japanese_pattern.findall(title)
    content_japanese = japanese_pattern.findall(content)
    
    if title_japanese:
        return False, f"제목에 일본어 문자가 포함되어 있습니다: {', '.join(set(title_japanese[:5]))}"
    
    if content_japanese:
        return False, f"본문에 일본어 문자가 포함되어 있습니다: {', '.join(set(content_japanese[:5]))}"
    
    # 외국어 단어 패턴 검사 (예: interesant, interessante, interesting 등)
    foreign_word_patterns = [
        r'\binteress?ant\w*\b',  # interessant, interessante (s가 1개 또는 2개)
        r'\binteresting\w*\b',  # interesting
        r'\bkhá\w*\b',  # khá
    ]
    for pattern in foreign_word_patterns:
        title_match = re.search(pattern, title, re.IGNORECASE)
        content_match = re.search(pattern, content, re.IGNORECASE)
        if title_match:
            return False, f"제목에 외국어 단어가 포함되어 있습니다: {title_match.group()}"
        if content_match:
            return False, f"본문에 외국어 단어가 포함되어 있습니다: {content_match.group()}"
    
    # 한글 비율 검사 (한글이 주가 되어야 함! 영어는 필요시만)
    # 제목: 한글 비율 70% 이상
    title_korean_ratio = _calculate_korean_ratio(title)
    if title_korean_ratio < 0.7:
        return False, f"제목이 한글로 작성되지 않았습니다. 한글이 주가 되어야 합니다. (현재 한글 비율: {title_korean_ratio*100:.1f}%, 필요: 70% 이상)"
    
    # 본문: 한글 비율 80% 이상 (한글이 주, 영어는 기술 용어 등 필요시만)
    content_korean_ratio = _calculate_korean_ratio(content)
    if content_korean_ratio < 0.8:
        return False, f"본문이 한글로 작성되지 않았습니다. 한글이 주가 되어야 하며, 영어는 기술 용어나 고유명사 설명 시에만 사용 가능합니다. (현재 한글 비율: {content_korean_ratio*100:.1f}%, 필요: 80% 이상)"
    
    # 영어 비율 검사 (영어가 너무 많으면 실패 - 영어가 주가 되면 안 됨!)
    english_pattern = re.compile(r'[a-zA-Z]')
    english_chars = len(english_pattern.findall(content))
    total_chars_no_space = len(re.sub(r'[\s.,!?;:()\[\]{}"\'-]', '', content))
    
    if total_chars_no_space > 0:
        english_ratio = english_chars / total_chars_no_space
        # 영어 비율이 25%를 넘으면 실패 (한글이 주가 되어야 함!)
        if english_ratio > 0.25:
            return False, f"본문에 영어가 너무 많습니다. 한글이 주가 되어야 하며, 영어는 기술 용어나 고유명사 설명 시에만 사용해야 합니다. (현재 영어 비율: {english_ratio*100:.1f}%, 최대 허용: 25%)"
    
    return True, ""


def remove_hanja_from_text(text: str) -> str:
    """
    텍스트에서 한자 및 모든 외국어 특수 문자를 제거
    - 한자 제거 (\u4e00-\u9fff)
    - 일본어 문자 제거 (히라가나, 가타카나)
    - 모든 라틴 확장 문자 제거 (\u00C0-\u024F)
    - 외국어 단어 제거 (interesant, khá 등)
    - 한글, 기본 영어, 숫자, 기본 구두점만 남김
    """
    if not text:
        return text
    
    cleaned = text
    
    # 외국어 단어 패턴 제거 (먼저 제거)
    foreign_words = [
        (r'\binteress?ant\w*\s*한\b', '흥미로운'),  # interessante한 → 흥미로운 (한 제거)
        (r'\binteress?ant\w*\b', '흥미로운'),  # interessant, interessante → 흥미로운
        (r'\binteresting\w*\s*한\b', '흥미로운'),  # interesting한 → 흥미로운
        (r'\binteresting\w*\b', '흥미로운'),  # interesting → 흥미로운
        (r'\bkhá\w*\b', '꽤'),  # khá → 꽤
        (r'\bkh\s', ' '),  # 불완전한 "kh" 조각 제거
        (r'まだ\s*', ''),  # 일본어 "まだ" 제거
    ]
    for pattern, replacement in foreign_words:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    
    # "아직 아직" 같은 중복 제거
    cleaned = re.sub(r'\b아직\s+아직\b', '아직', cleaned)
    
    # "흥미로운 흥미로운" 같은 중복 제거
    cleaned = re.sub(r'\b흥미로운\s+흥미로운\b', '흥미로운', cleaned)
    
    # "흥미로운한", "흥미로운 한" 같은 잘못된 조합 제거
    cleaned = re.sub(r'\b흥미로운\s*한\b', '흥미로운', cleaned)
    
    # "## 1. 제목" 같은 제목 섹션 제거
    cleaned = re.sub(r'##\s*1\.\s*제목\s*\n*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'#\s*제목\s*:?\s*\n*', '', cleaned, flags=re.IGNORECASE)
    
    # 일본어 문자 제거 (히라가나: \u3040-\u309F, 가타카나: \u30A0-\u30FF)
    # 일본어 단어 패턴 제거 (먼저 처리)
    japanese_words = [
        (r'データ', '데이터'),  # データ → 데이터
        (r'まだ', ''),  # まだ → 제거
        (r'あり', ''),  # あり → 제거
    ]
    for pattern, replacement in japanese_words:
        cleaned = re.sub(pattern, replacement, cleaned)
    
    # 일본어 문자 제거 (히라가나: \u3040-\u309F, 가타카나: \u30A0-\u30FF)
    # 먼저 일반적인 일본어 단어 변환
    japanese_word_replacements = [
        (r'データ', '데이터'),  # データ → 데이터
        (r'まだ', ''),  # まだ → 제거
    ]
    for pattern, replacement in japanese_word_replacements:
        cleaned = re.sub(pattern, replacement, cleaned)
    
    # 나머지 일본어 문자 제거 (히라가나: \u3040-\u309F, 가타카나: \u30A0-\u30FF)
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    cleaned = japanese_pattern.sub('', cleaned)
    
    # 한자 범위 제거 (\u4e00-\u9fff) - 일본어 한자도 포함
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


def remove_korean_from_english_text(text: str) -> str:
    """
    영문 콘텐츠에서 한글 문자 완전히 제거
    - 한글 문자 (가-힣) 제거
    - 한글이 포함된 문장/단어 제거
    - 문맥 손상 최소화
    """
    if not text:
        return text
    
    cleaned = text
    
    # 한글 문자 패턴
    korean_pattern = re.compile(r'[가-힣]')
    
    # 한글이 포함된 줄 찾기
    lines = cleaned.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # 한글이 포함되어 있으면
        if korean_pattern.search(line):
            # 한글 문자만 제거하고 나머지 유지
            cleaned_line = korean_pattern.sub('', line)
            # 괄호 안의 한글 포함 부분 제거 (예: "Public Data Portal (공공데이터포털)" → "Public Data Portal ()")
            cleaned_line = re.sub(r'\([^)]*[가-힣][^)]*\)', '()', cleaned_line)
            cleaned_line = re.sub(r'\(\)', '', cleaned_line)  # 빈 괄호 제거
            cleaned_line = cleaned_line.strip()
            
            # 내용이 남아있고, 의미있는 줄이면 유지
            if cleaned_line and len(cleaned_line) > 3:
                cleaned_lines.append(cleaned_line)
            # 내용이 없으면 빈 줄로 처리
            elif cleaned_line == '':
                cleaned_lines.append('')
        else:
            # 한글이 없으면 그대로 유지
            cleaned_lines.append(line)
    
    cleaned = '\n'.join(cleaned_lines)
    
    # 한글이 포함된 참조 링크 패턴 제거 (예: "[공공데이터포털](url)" → "")
    cleaned = re.sub(r'\[[^\]]*[가-힣][^\]]*\](\([^)]*\))?', '', cleaned)
    
    # 마크다운 링크에서 한글 제거
    cleaned = re.sub(r'\[([^\]]*[가-힣][^\]]*)\]\([^)]*\)', '', cleaned)
    
    # 연속된 빈 줄 정리 (3개 이상 → 2개)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # 앞뒤 공백 정리
    cleaned = cleaned.strip()
    
    return cleaned

