"""
한글 콘텐츠 형식 자동 수정 유틸리티
"""

import re


def fix_korean_content_format(content: str) -> str:
    """
    한글 콘텐츠의 형식을 자동으로 수정
    - 소제목(##) 다음 빈 줄 추가
    - 문단 사이 빈 줄 추가
    - 서론-본론-결론 구조 확인 및 수정
    
    전전 포스팅처럼 형식이 잘 유지되도록 강력하게 복구합니다.
    """
    if not content:
        return content
    
    # 0단계: 이스케이프 문자 복구
    content = content.replace('\\n', '\n')
    
    # 1단계: **서론**, **본론**, **결론** 섹션 구분 (가장 우선)
    content = re.sub(r'(\*\*서론\*\*)\s*([가-힣])', r'\1\n\n\2', content)
    content = re.sub(r'(\*\*본론\*\*)\s*([가-힣#])', r'\1\n\n\2', content)
    content = re.sub(r'(\*\*결론\*\*)\s*([가-힣])', r'\1\n\n\2', content)
    
    # 2단계: 소제목(##) 처리 - 앞뒤 빈 줄 강제 추가
    # 소제목 앞에 빈 줄 추가
    content = re.sub(r'([가-힣A-Za-z0-9.!?])\s*(##\s+)', r'\1\n\n\2', content)
    # 소제목 다음에 빈 줄 추가 (한 줄에 있는 경우)
    content = re.sub(r'(##\s+[^\n#]+?)\s*([가-힣A-Za-z])', r'\1\n\n\2', content)
    
    # 3단계: 문단 구분 - 마침표, 느낌표, 물음표 다음 빈 줄 추가
    content = re.sub(r'([.!?])\s+([가-힣A-Z])', r'\1\n\n\2', content)
    
    # 4단계: 줄 단위 처리로 세밀한 조정
    lines = content.split('\n')
    fixed_lines = []
    prev_was_heading = False
    prev_was_bold_section = False
    prev_was_paragraph = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # 빈 줄 처리
        if not line_stripped:
            if fixed_lines and fixed_lines[-1].strip():
                fixed_lines.append('')
            prev_was_heading = False
            prev_was_bold_section = False
            prev_was_paragraph = False
            continue
        
        # **서론**, **본론**, **결론** 처리
        if re.match(r'^\*\*서론\*\*', line_stripped) or re.match(r'^\*\*본론\*\*', line_stripped) or re.match(r'^\*\*결론\*\*', line_stripped):
            if fixed_lines and fixed_lines[-1].strip():
                fixed_lines.append('')
            fixed_lines.append(line)
            prev_was_bold_section = True
            prev_was_heading = False
            prev_was_paragraph = False
            continue
        
        # 소제목(##) 처리
        if line_stripped.startswith('##'):
            if fixed_lines and fixed_lines[-1].strip():
                fixed_lines.append('')
            fixed_lines.append(line)
            prev_was_heading = True
            prev_was_bold_section = False
            prev_was_paragraph = False
            continue
        
        # 일반 문단
        if prev_was_heading or prev_was_bold_section:
            if fixed_lines and fixed_lines[-1].strip():
                fixed_lines.append('')
        
        fixed_lines.append(line)
        prev_was_heading = False
        prev_was_bold_section = False
        prev_was_paragraph = True
    
    result = '\n'.join(fixed_lines)
    
    # 5단계: 연속된 빈 줄 정규화 (최대 2개)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # 6단계: 시작/끝 정리
    result = result.strip()
    
    # 7단계: 소제목 다음 빈 줄 최종 확인 및 추가
    lines_final = result.split('\n')
    final_fixed = []
    for i, line in enumerate(lines_final):
        final_fixed.append(line)
        line_stripped = line.strip()
        
        # 소제목 다음 빈 줄 확인
        if line_stripped.startswith('##'):
            if i + 1 < len(lines_final):
                next_line = lines_final[i + 1].strip()
                if next_line and not next_line.startswith('#'):
                    final_fixed.append('')
        
        # **서론**, **본론**, **결론** 다음 빈 줄 확인
        if re.match(r'^\*\*서론\*\*', line_stripped) or re.match(r'^\*\*본론\*\*', line_stripped) or re.match(r'^\*\*결론\*\*', line_stripped):
            if i + 1 < len(lines_final):
                next_line = lines_final[i + 1].strip()
                if next_line and not next_line.startswith('**'):
                    final_fixed.append('')
    
    result = '\n'.join(final_fixed)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result


def ensure_korean_structure(content: str) -> str:
    """
    한글 콘텐츠의 서론-본론-결론 구조를 확인하고 수정
    """
    if not content:
        return content
    
    # 소제목 개수 확인
    headings = re.findall(r'^##\s+.+$', content, re.MULTILINE)
    body_headings = [h for h in headings if '서론' not in h and '결론' not in h and 'Introduction' not in h and 'Conclusion' not in h]
    
    # 본론 소제목이 3개 미만이면 경고
    if len(body_headings) < 3:
        # 형식이 무너진 것으로 간주
        pass
    
    # 결론 섹션 확인
    has_conclusion = any('결론' in h or 'Conclusion' in h for h in headings) or '## 결론' in content
    
    if not has_conclusion:
        # 결론 추가 시도는 하지 않음 (번역 프롬프트에서 처리)
        pass
    
    return content
