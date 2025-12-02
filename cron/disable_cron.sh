#!/bin/bash
# 크론 작업 일시 중지

CRON_FILE=$(mktemp)
crontab -l > "$CRON_FILE" 2>/dev/null || touch "$CRON_FILE"

# auto_poster.py 관련 라인 주석 처리
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's|^\(.*auto_poster\.py.*\)$|# \1|' "$CRON_FILE"
else
    # Linux
    sed -i.bak 's|^\(.*auto_poster\.py.*\)$|# \1|' "$CRON_FILE"
fi

crontab "$CRON_FILE"
rm -f "$CRON_FILE" "$CRON_FILE.bak" 2>/dev/null

echo "✅ 크론 작업이 중지되었습니다."
echo ""
echo "현재 크론 작업:"
crontab -l 2>/dev/null || echo "(크론 작업 없음)"
