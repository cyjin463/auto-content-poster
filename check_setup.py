#!/usr/bin/env python3
"""
설정 확인 스크립트
"""

import os
import sys

def check_setup():
    print("🔍 설정 확인 중...\n")
    
    issues = []
    
    # 1. Python 버전
    print("1. Python 버전:")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}\n")
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (3.8 이상 필요)\n")
        issues.append("Python 버전이 너무 낮습니다.")
    
    # 2. 필수 패키지
    print("2. 필수 패키지:")
    try:
        import requests
        print(f"   ✅ requests {requests.__version__}\n")
    except ImportError:
        print("   ❌ requests 패키지가 설치되지 않았습니다.\n")
        issues.append("requests 패키지 설치 필요: pip install -r requirements.txt")
    
    # 3. 환경 변수
    print("3. 환경 변수:")
    
    # .env 파일 로드 시도
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv 없어도 직접 읽기
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        except FileNotFoundError:
            pass
    
    groq_key = os.getenv('GROQ_API_KEY')
    notion_key = os.getenv('NOTION_API_KEY')
    
    if groq_key:
        masked = groq_key[:8] + '...' if len(groq_key) > 8 else groq_key
        print(f"   ✅ GROQ_API_KEY 설정됨 ({masked})\n")
    else:
        print("   ❌ GROQ_API_KEY 설정 안됨\n")
        issues.append("GROQ_API_KEY 환경 변수 설정 필요 (https://console.groq.com)")
    
    if notion_key:
        masked = notion_key[:8] + '...' if len(notion_key) > 8 else notion_key
        print(f"   ✅ NOTION_API_KEY 설정됨 ({masked}) [선택사항]\n")
    else:
        print("   ⚠️  NOTION_API_KEY 설정 안됨 [선택사항, MCP 사용 시 불필요]\n")
    
    # 4. 데이터베이스
    print("4. 데이터베이스:")
    try:
        from database import Database
        db = Database()
        print("   ✅ 데이터베이스 초기화 성공\n")
    except Exception as e:
        print(f"   ❌ 데이터베이스 초기화 실패: {e}\n")
        issues.append(f"데이터베이스 오류: {e}")
    
    # 5. 필수 파일
    print("5. 필수 파일:")
    required_files = [
        'main.py',
        'main_agent.py',
        'database.py',
        'search.py',
        'content_generator.py',
        'agents/agent_chain.py'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (없음)")
            all_exist = False
            issues.append(f"{file} 파일이 없습니다.")
    
    print()
    
    # 결과
    if issues:
        print("❌ 설정 문제 발견:\n")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n위 문제를 해결한 후 다시 시도하세요.")
        return False
    else:
        print("✅ 모든 설정이 완료되었습니다! 테스트를 시작할 수 있습니다.\n")
        print("테스트 실행:")
        print("  python main_agent.py '테스트 키워드' --save-to-db")
        return True

if __name__ == '__main__':
    success = check_setup()
    sys.exit(0 if success else 1)

