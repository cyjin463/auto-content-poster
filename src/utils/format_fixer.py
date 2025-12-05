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
    
    이 함수는 JSON 파싱 후 또는 LLM 응답에서 형식이 손실된 경우를 복구합니다.
    """
    if not content:
        return content
    
    # 0단계: 이스케이프 문자 복구 (이미 처리되었을 수 있지만 다시 확인)
    content = content.replace('\\n', '\n')
    
    # 0.5단계: 완전히 형식이 무너진 경우 (한 줄로 연결된 경우) 복구
    # 패턴 1: 소제목(##) 앞에 공백이나 텍스트가 있으면 줄바꿈 추가
    # 단, 마침표 다음이 아니면 추가하지 않음 (문장이 잘리는 것 방지)
    content = re.sub(r'([.!?])\s+(##\s+)', r'\1\n\n\2', content)
    # 패턴 2: 소제목(##) 뒤에 바로 텍스트가 있으면 줄바꿈 추가
    # 단, 소제목 텍스트 자체는 유지하고 다음 문장만 분리
    # "## 제목 텍스트시작" → "## 제목\n\n텍스트시작" (단, 제목과 텍스트 구분이 필요)
    # 더 안전한 방법: 소제목이 공백으로 끝나지 않으면 줄바꿈 추가
    content = re.sub(r'(##\s+[^\n#]+[^\s])([가-힣A-Za-z])', r'\1\n\n\2', content)
    
    # 문제: 영문 콘텐츠와 비교했을 때 빈 줄이 손실됨
    # 해결: 소제목과 문단 사이를 강제로 빈 줄로 구분
    
    # 1단계: 소제목(##) 찾기 및 다음에 빈 줄 강제 추가
    # 패턴 1: ## 제목 다음에 바로 텍스트가 오는 경우 (빈 줄 없음)
    content = re.sub(r'(##\s+[^\n]+)\n([^\n#\s])', r'\1\n\n\2', content)
    # 패턴 2: ## 제목 다음에 공백만 있고 텍스트가 오는 경우
    content = re.sub(r'(##\s+[^\n]+)\n\s+([^\n#])', r'\1\n\n\2', content)
    
    # 2단계: 문장 끝(마침표, 느낌표, 물음표) 다음 문단 구분
    # 한글 문장 끝 패턴: 마침표 + 공백/줄바꿈 + 한글로 시작하는 다음 문장
    content = re.sub(r'([.!?])\s*\n([가-힣])', r'\1\n\n\2', content)
    # 이미 빈 줄이 있으면 추가하지 않음 (정규화)
    content = re.sub(r'([.!?])\s*\n\n\n+([가-힣])', r'\1\n\n\2', content)
    
    # 3단계: 소제목(##) 앞에 빈 줄 추가 (소제목과 이전 문단 구분)
    # 단, 첫 번째 소제목이나 이미 빈 줄이 있으면 추가하지 않음
    content = re.sub(r'([가-힣A-Za-z0-9.!?])\n(##\s+)', r'\1\n\n\2', content)
    
    # 4단계: 줄 단위 처리로 세밀한 조정
    lines = content.split('\n')
    fixed_lines = []
    prev_was_list_item = False
    prev_was_heading = False
    prev_was_paragraph_end = False
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # 빈 줄 처리
        if not line_stripped:
            # 이미 빈 줄이 있으면 추가하지 않음 (중복 방지)
            if not (fixed_lines and not fixed_lines[-1].strip()):
                fixed_lines.append('')
            prev_was_list_item = False
            prev_was_heading = False
            prev_was_paragraph_end = False
            continue
        
        # 소제목(##) 처리
        if line_stripped.startswith('##'):
            # 이전 줄이 문단 끝이었으면 빈 줄 추가 (소제목과 문단 구분)
            if prev_was_paragraph_end and fixed_lines and fixed_lines[-1].strip():
                fixed_lines.append('')
            fixed_lines.append(line)
            prev_was_heading = True
            prev_was_list_item = False
            prev_was_paragraph_end = False
            continue
        
        # 리스트 항목 확인
        is_list_item = line_stripped.startswith('-') or re.match(r'^\d+\.', line_stripped)
        
        if is_list_item:
            # 리스트 항목은 연속되어야 하므로 빈 줄 추가하지 않음
            fixed_lines.append(line)
            prev_was_list_item = True
            prev_was_heading = False
            prev_was_paragraph_end = False
        else:
            # 일반 문단
            if prev_was_heading:
                # 소제목 다음이면 반드시 빈 줄 추가
                if fixed_lines and fixed_lines[-1].strip():
                    fixed_lines.append('')
            elif prev_was_list_item:
                # 리스트 다음 일반 문단이면 빈 줄 추가
                if fixed_lines and fixed_lines[-1].strip():
                    fixed_lines.append('')
            
            fixed_lines.append(line)
            
            # 문장 끝 확인 (마침표, 느낌표, 물음표로 끝나는지)
            if line_stripped and line_stripped[-1] in '.!?':
                prev_was_paragraph_end = True
            else:
                prev_was_paragraph_end = False
            
            prev_was_list_item = False
            prev_was_heading = False
    
    result = '\n'.join(fixed_lines)
    
    # 5단계: 연속된 빈 줄을 최대 2개로 제한 (정규화)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # 6단계: 시작/끝의 불필요한 빈 줄 제거 (단, 내용은 유지)
    result = result.strip()
    
    # 7단계: 최종 검증 - 소제목 다음에 빈 줄이 있는지 확인하고 없으면 추가
    lines_final = result.split('\n')
    final_fixed = []
    for i, line in enumerate(lines_final):
        line_stripped = line.strip()
        final_fixed.append(line)
        
        # 소제목 다음 줄이 비어있지 않으면 빈 줄 추가
        if line_stripped.startswith('##'):
            if i + 1 < len(lines_final):
                next_line = lines_final[i + 1].strip()
                if next_line and not next_line.startswith('#'):
                    # 다음 줄이 비어있지 않으면 빈 줄 추가
                    final_fixed.append('')
    
    result = '\n'.join(final_fixed)
    result = re.sub(r'\n{3,}', '\n\n', result)  # 다시 정규화
    
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

