"""
스케줄러 (크론 작업용)
매일 오전 7시에 자동 실행
"""

from database import Database


def run_scheduled_tasks(db: Database = None):
    """크론 작업 실행 - 키워드 하나만 처리 (한글 + 영문 각 1개)"""
    if db is None:
        db = Database()
    
    print("⏰ 크론 작업 시작 (매일 오전 7시)")
    print("=" * 60)
    
    # 순환 import 방지를 위해 함수 내부에서 import
    from auto_poster import process_single_keyword_dual_language
    process_single_keyword_dual_language()

