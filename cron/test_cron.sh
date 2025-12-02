#!/bin/bash
# 크론 실행 테스트 스크립트

cd /Users/leo/auto-content-poster
echo "[$(date '+%Y-%m-%d %H:%M:%S KST')] 크론 테스트 시작" >> cron_test.log 2>&1

# Python 경로 확인
PYTHON_PATH="/Users/leo/.pyenv/shims/python3"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python 경로를 찾을 수 없습니다: $PYTHON_PATH" >> cron_test.log 2>&1
    exit 1
fi

# 환경 변수 로드 테스트
$PYTHON_PATH -c "
import sys
sys.path.insert(0, '/Users/leo/auto-content-poster')
from auto_poster import load_env_file
load_env_file()
print('✅ 환경 변수 로드 성공')
" >> cron_test.log 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S KST')] 크론 테스트 완료" >> cron_test.log 2>&1
