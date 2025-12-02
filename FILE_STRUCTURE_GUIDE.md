# 파일 구조 가이드

## 📁 올바른 파일 생성 위치

새로운 파일을 만들 때는 다음 폴더 구조를 따라주세요:

### 1. **핵심 로직** → `src/core/`
- 데이터베이스 관련: `src/core/database.py`
- 설정/환경 변수: `src/core/config.py`
- 공통 유틸리티 클래스 등

### 2. **서비스 레이어** → `src/services/`
- 외부 API 연동: `src/services/notion.py`, `src/services/search.py`
- 외부 서비스 래퍼 등

### 3. **유틸리티 함수** → `src/utils/`
- 헬퍼 함수: `src/utils/helpers.py`
- 공통 함수들

### 4. **AI 에이전트** → `agents/`
- 에이전트 클래스: `agents/content_agent.py`
- 에이전트 체인: `agents/agent_chain.py`

### 5. **실행 스크립트** → `scripts/`
- 메인 스크립트: `scripts/auto_poster.py`
- 스케줄러: `scripts/scheduler.py`
- 배포 스크립트: `scripts/check_and_redeploy.py`

### 6. **유틸리티 스크립트** → `tools/`
- 설정 확인: `tools/check_setup.py`
- 개발 도구 등

### 7. **크론 스크립트** → `cron/`
- 크론 활성화: `cron/enable_cron.sh`
- 크론 비활성화: `cron/disable_cron.sh`

### 8. **데이터 파일** → `data/`
- 데이터베이스: `data/keywords.db`
- 로그 파일: `data/cron.log`

### 9. **문서** → `docs/`
- 아키텍처 문서: `docs/AGENT_ARCHITECTURE.md`
- 워크플로우: `docs/WORKFLOW.md`

## ⚠️ 루트 디렉토리에 생성하지 말아야 할 것

다음 파일들은 **절대 루트에 만들지 마세요**:

- ❌ `database.py` (→ `src/core/database.py`)
- ❌ `notion_api.py` (→ `src/services/notion.py`)
- ❌ `search.py` (→ `src/services/search.py`)
- ❌ `utils.py` (→ `src/utils/helpers.py`)
- ❌ 실행 스크립트 (→ `scripts/`)
- ❌ 크론 스크립트 (→ `cron/`)

## ✅ 올바른 예시

### 새 서비스 추가
```python
# ✅ 올바름: src/services/new_service.py
from src.core.config import load_env_file

# ❌ 잘못됨: new_service.py (루트)
```

### 새 유틸리티 추가
```python
# ✅ 올바름: src/utils/my_helpers.py
def my_function():
    pass

# ❌ 잘못됨: my_helpers.py (루트)
```

### 새 스크립트 추가
```python
#!/usr/bin/env python3
# ✅ 올바름: scripts/my_script.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import Database

# ❌ 잘못됨: my_script.py (루트)
```

## 📝 Import 경로 규칙

### 올바른 Import
```python
# 핵심 모듈
from src.core.database import Database
from src.core.config import load_env_file

# 서비스
from src.services.notion import create_notion_page
from src.services.search import search_keywords

# 유틸리티
from src.utils.helpers import validate_korean_content

# 에이전트
from agents.content_agent import ContentGenerationAgent
```

### 프로젝트 루트 추가 (스크립트에서)
```python
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 이제 import 가능
from src.core.database import Database
```

## 🔄 기존 파일 (하위 호환성)

루트에 남아있는 다음 파일들은 **하위 호환성을 위한 래퍼**입니다:
- `database.py` → `src/core/database.py`로 리다이렉트
- `notion_api.py` → `src/services/notion.py`로 리다이렉트
- `search.py` → `src/services/search.py`로 리다이렉트
- `utils.py` → `src/utils/helpers.py`로 리다이렉트

**새 코드를 작성할 때는 이 파일들을 직접 import하지 말고, 새 경로를 사용하세요!**

