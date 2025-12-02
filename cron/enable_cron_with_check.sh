#!/bin/bash
# 크론 작업 활성화 (9시 10분 포스팅 + 9시 30분 확인)

# 프로젝트 루트 디렉토리 찾기
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$PROJECT_ROOT/scripts"
CRON_DIR="$PROJECT_ROOT/cron"

CRON_FILE=$(mktemp)
crontab -l > "$CRON_FILE" 2>/dev/null || touch "$CRON_FILE"

# 기존 auto_poster 관련 크론 작업 제거
sed -i '' '/auto_poster\.py/d' "$CRON_FILE" 2>/dev/null || sed -i.bak '/auto_poster\.py/d' "$CRON_FILE"
sed -i '' '/scheduler\.py/d' "$CRON_FILE" 2>/dev/null || sed -i.bak '/scheduler\.py/d' "$CRON_FILE"
sed -i '' '/check_and_redeploy\.py/d' "$CRON_FILE" 2>/dev/null || sed -i.bak '/check_and_redeploy\.py/d' "$CRON_FILE"

# Python 경로 확인
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    PYTHON_PATH="/usr/bin/python3"
fi

# 9시 10분 포스팅 작업 추가 (월~금, 오전 9시 10분 KST - GROQ 초기화 후)
echo "10 9 * * 1-5 cd $PROJECT_ROOT && $PYTHON_PATH $SCRIPT_DIR/scheduler.py >> $CRON_DIR/cron.log 2>&1" >> "$CRON_FILE"

# 9시 30분 배포 확인 작업 추가 (월~금, 포스팅 후 20분)
echo "30 9 * * 1-5 cd $PROJECT_ROOT && $PYTHON_PATH $SCRIPT_DIR/check_and_redeploy.py >> $CRON_DIR/cron.log 2>&1" >> "$CRON_FILE"

crontab "$CRON_FILE"
rm -f "$CRON_FILE" "$CRON_FILE.bak" 2>/dev/null

echo "✅ 크론 작업이 활성화되었습니다."
echo ""
echo "📅 설정된 크론 작업:"
echo "   - 매일 오전 9시 10분 (월~금): 자동 포스팅 (GROQ 초기화 후)"
echo "   - 매일 오전 9시 30분 (월~금): 배포 확인 및 재배포"
echo ""
echo "현재 크론 작업 목록:"
crontab -l

