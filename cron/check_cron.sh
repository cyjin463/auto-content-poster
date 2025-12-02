#!/bin/bash
# 크론 작업 상태 확인 스크립트

echo "=== 크론 작업 상태 확인 ==="
echo ""

# 1. 크론 작업 목록 확인
echo "1️⃣ 크론 작업 목록:"
CRON_JOBS=$(crontab -l 2>/dev/null | grep "auto_poster.py")
if [ -z "$CRON_JOBS" ]; then
    echo "   ❌ 크론 작업이 설정되지 않았습니다."
    CRON_ENABLED=false
else
    # 주석 처리되어 있는지 확인
    if echo "$CRON_JOBS" | grep -q "^#"; then
        echo "   ⏸️  크론 작업이 주석 처리되어 있습니다 (비활성화됨):"
        echo "   $CRON_JOBS"
        CRON_ENABLED=false
    else
        echo "   ✅ 크론 작업이 활성화되어 있습니다:"
        echo "   $CRON_JOBS"
        CRON_ENABLED=true
    fi
fi

echo ""

# 2. 로그 파일 확인
echo "2️⃣ 로그 파일 확인:"
LOG_FILE="cron.log"
if [ -f "$LOG_FILE" ]; then
    echo "   ✅ 로그 파일이 존재합니다: $LOG_FILE"
    
    # 파일 크기
    FILE_SIZE=$(ls -lh "$LOG_FILE" | awk '{print $5}')
    echo "   파일 크기: $FILE_SIZE"
    
    # 마지막 수정 시간
    LAST_MODIFIED=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LOG_FILE" 2>/dev/null || stat -c "%y" "$LOG_FILE" 2>/dev/null | cut -d'.' -f1)
    echo "   마지막 수정: $LAST_MODIFIED"
    
    # 마지막 실행 확인
    if echo "$LAST_MODIFIED" | grep -q "$(date +%Y-%m-%d)"; then
        echo "   ✅ 오늘 실행된 기록이 있습니다!"
    else
        echo "   ⚠️  오늘 실행 기록이 없습니다."
    fi
    
    echo ""
    echo "   📝 최근 로그 (마지막 10줄):"
    echo "   ─────────────────────────────"
    tail -10 "$LOG_FILE" 2>/dev/null | sed 's/^/   /'
    echo "   ─────────────────────────────"
else
    echo "   ⚠️  로그 파일이 없습니다. (아직 실행된 적이 없을 수 있음)"
fi

echo ""

# 3. 다음 실행 시간 확인
echo "3️⃣ 다음 실행 시간:"
if [ "$CRON_ENABLED" = true ]; then
    CRON_TIME=$(echo "$CRON_JOBS" | awk '{print $2":"$1}')
    echo "   예정 시간: 매일 $CRON_TIME"
    
    # 현재 시간과 비교
    CURRENT_HOUR=$(date +%H)
    CURRENT_MIN=$(date +%M)
    
    if [ -n "$CRON_TIME" ]; then
        CRON_HOUR=$(echo "$CRON_TIME" | cut -d':' -f1)
        CRON_MIN=$(echo "$CRON_TIME" | cut -d':' -f2)
        
        echo "   현재 시간: $CURRENT_HOUR:$CURRENT_MIN"
        
        if [ "$CURRENT_HOUR" -lt "$CRON_HOUR" ] || ([ "$CURRENT_HOUR" -eq "$CRON_HOUR" ] && [ "$CURRENT_MIN" -lt "$CRON_MIN" ]); then
            echo "   ⏰ 오늘 $CRON_TIME에 실행 예정입니다."
        else
            echo "   ⏰ 내일 $CRON_TIME에 실행 예정입니다."
        fi
    fi
else
    echo "   ❌ 크론 작업이 비활성화되어 있어 실행되지 않습니다."
fi

echo ""

# 4. 데이터베이스에서 마지막 포스팅 확인
echo "4️⃣ 마지막 포스팅 확인:"
if command -v python3 &> /dev/null; then
    LAST_POSTED=$(python3 -c "
from database import Database
from datetime import datetime
try:
    db = Database()
    keyword = db.get_first_active_keyword()
    if keyword:
        last_posted = db.get_keyword_last_posted(keyword['id'])
        if last_posted:
            print(str(last_posted))
        else:
            print('아직 포스팅 안 됨')
    else:
        print('활성 키워드 없음')
except Exception as e:
    print(f'오류: {e}')
" 2>/dev/null)
    
    if [ -n "$LAST_POSTED" ] && [ "$LAST_POSTED" != "오류:"* ]; then
        if [ "$LAST_POSTED" = "아직 포스팅 안 됨" ] || [ "$LAST_POSTED" = "활성 키워드 없음" ]; then
            echo "   ⚠️  $LAST_POSTED"
        else
            echo "   ✅ 마지막 포스팅: $LAST_POSTED"
            
            # 오늘 포스팅했는지 확인
            TODAY=$(date +%Y-%m-%d)
            if echo "$LAST_POSTED" | grep -q "$TODAY"; then
                echo "   ✅ 오늘 포스팅 완료!"
            else
                echo "   ⚠️  오늘 아직 포스팅하지 않았습니다."
            fi
        fi
    else
        echo "   ⚠️  데이터베이스 확인 실패"
    fi
else
    echo "   ⚠️  Python3를 찾을 수 없습니다."
fi

echo ""

# 5. 최종 상태 요약
echo "════════════════════════════════════"
echo "📊 상태 요약:"
echo "════════════════════════════════════"

if [ "$CRON_ENABLED" = true ]; then
    echo "✅ 크론 작업: 활성화됨"
    
    if [ -f "$LOG_FILE" ]; then
        if echo "$LAST_MODIFIED" | grep -q "$(date +%Y-%m-%d)"; then
            echo "✅ 오늘 실행됨"
            echo "✅ 모든 것이 정상 작동 중입니다!"
        else
            echo "⚠️  오늘 실행 안 됨 (아직 시간 안 지남 또는 오류)"
        fi
    else
        echo "⚠️  로그 파일 없음 (아직 실행 안 됨)"
    fi
else
    echo "❌ 크론 작업: 비활성화됨"
    echo "💡 활성화하려면: ./enable_cron.sh 또는 crontab -e"
fi

echo "════════════════════════════════════"

