"""
스케줄러 (크론 작업용)
매일 오전 7시에 자동 실행
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import Database


def run_scheduled_tasks(db: Database = None):
    """크론 작업 실행 - 키워드 하나만 처리 (한글 + 영문 각 1개)"""
    if db is None:
        db = Database()
    
    print("⏰ 크론 작업 시작 (매일 오전 7시)")
    print("=" * 60)
    
    # 순환 import 방지를 위해 함수 내부에서 import
    from scripts.auto_poster import process_single_keyword_dual_language
    process_single_keyword_dual_language()


if __name__ == '__main__':
    run_scheduled_tasks()

