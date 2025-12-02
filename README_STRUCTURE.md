# 프로젝트 구조 안내

## 📁 올바른 파일 생성 위치

### ✅ 새 파일 생성 시 참고

1. **핵심 로직** → `src/core/`
   - 데이터베이스, 설정 등

2. **서비스 레이어** → `src/services/`
   - 외부 API 연동

3. **유틸리티** → `src/utils/`
   - 헬퍼 함수들

4. **실행 스크립트** → `scripts/`
   - 메인 스크립트들

5. **유틸리티 스크립트** → `tools/`
   - 개발/관리 도구

6. **크론 스크립트** → `cron/`
   - 스케줄링 스크립트

7. **데이터 파일** → `data/`
   - 데이터베이스, 로그 등

8. **문서** → `docs/`
   - 프로젝트 문서

## ⚠️ 주의사항

루트 디렉토리에 `.py` 파일을 만들지 마세요!
- 새 모듈은 반드시 `src/` 하위에 생성
- 새 스크립트는 `scripts/` 또는 `tools/`에 생성

## 📝 Import 예시

```python
# ✅ 올바름
from src.core.database import Database
from src.services.notion import create_notion_page

# ❌ 잘못됨 (루트에 직접 import)
from database import Database  # Deprecated!
```

자세한 내용은 `FILE_STRUCTURE_GUIDE.md`를 참조하세요.

