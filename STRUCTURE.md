# 프로젝트 구조

## 📁 폴더 구조

```
auto-content-poster/
├── src/                      # 소스 코드
│   ├── agents/              # AI 에이전트들
│   │   ├── __init__.py
│   │   ├── base.py          # BaseAgent 클래스
│   │   ├── agent_chain.py   # 에이전트 체인 오케스트레이션
│   │   ├── search_agent.py  # 검색 에이전트
│   │   ├── validation_agent.py  # 검증 에이전트
│   │   ├── fact_check_agent.py  # 사실 확인 및 수정 에이전트
│   │   ├── content_agent.py     # 콘텐츠 생성 에이전트
│   │   ├── posting_agent.py     # 포스팅 에이전트
│   │   └── keyword_inference_agent.py  # 키워드 추론 에이전트
│   ├── core/                # 핵심 로직
│   │   ├── __init__.py
│   │   ├── database.py      # SQLite 데이터베이스 관리
│   │   └── config.py        # 환경 변수 로드 (통합)
│   ├── services/            # 서비스 레이어
│   │   ├── __init__.py
│   │   ├── search.py        # 웹 검색 서비스 (Google/DuckDuckGo)
│   │   └── notion.py        # Notion API 서비스 (통합)
│   └── utils/               # 유틸리티 함수
│       ├── __init__.py
│       └── helpers.py       # 헬퍼 함수들 (언어 검증 등)
│
├── scripts/                 # 실행 스크립트
│   ├── auto_poster.py       # 메인 포스팅 스크립트
│   ├── scheduler.py         # 크론 스케줄러
│   ├── check_and_redeploy.py  # 배포 확인 및 재배포
│   └── setup_curriculum.py  # 커리큘럼 설정
│
├── tools/                   # 유틸리티 스크립트
│   └── check_setup.py       # 설정 확인 스크립트
│
├── cron/                    # 크론 스크립트
│   ├── enable_cron.sh       # 크론 활성화
│   ├── enable_cron_with_check.sh  # 크론 활성화 (체크 포함)
│   ├── disable_cron.sh      # 크론 비활성화
│   └── check_cron.sh        # 크론 상태 확인
│
├── docs/                    # 문서
│   ├── AGENT_ARCHITECTURE.md
│   ├── AGENT_FLOW.md
│   ├── ARCHITECTURE_REFACTORING.md
│   ├── SUMMARY.md
│   └── WORKFLOW.md
│
├── keywords.db              # SQLite 데이터베이스
├── .env                     # 환경 변수 (gitignore)
├── requirements.txt         # Python 패키지 의존성
└── README.md               # 프로젝트 설명
```

## 🔄 주요 변경사항

### 1. 모듈화된 구조
- **src/core/**: 핵심 로직 (데이터베이스, 설정)
- **src/services/**: 외부 서비스 연동 (검색, Notion)
- **src/utils/**: 공통 유틸리티
- **scripts/**: 실행 가능한 스크립트
- **tools/**: 유틸리티 스크립트
- **cron/**: 크론 작업 스크립트

### 2. 코드 통합
- `notion_api.py` + `notion_poster.py` → `src/services/notion.py`
- 모든 `load_env_file()` → `src/core/config.py` 통합
- `database.py` → `src/core/database.py`
- `search.py` → `src/services/search.py`
- `utils.py` → `src/utils/helpers.py`

### 3. Import 경로 변경
모든 import 경로가 새 구조에 맞게 업데이트되었습니다:
- `from database import Database` → `from src.core.database import Database`
- `from notion_api import ...` → `from src.services.notion import ...`
- `from utils import ...` → `from src.utils.helpers import ...`
- `from search import ...` → `from src.services.search import ...`

## 📝 사용 방법

### 메인 스크립트 실행
```bash
python scripts/auto_poster.py
```

### 설정 확인
```bash
python tools/check_setup.py
```

### 커리큘럼 설정
```bash
python scripts/setup_curriculum.py
```

### 크론 작업 활성화
```bash
./cron/enable_cron_with_check.sh
```

## 🔧 개발자 가이드

### 새 모듈 추가
1. 적절한 폴더 선택 (`src/core/`, `src/services/`, `src/utils/`)
2. 모듈 파일 생성
3. `__init__.py`에 export 추가 (선택사항)
4. 다른 파일에서 import 시 `from src.폴더.모듈 import ...` 형식 사용

### 환경 변수 로드
모든 스크립트는 프로젝트 루트에 `sys.path`를 추가한 후:
```python
from src.core.config import load_env_file
load_env_file()
```

### 데이터베이스 접근
```python
from src.core.database import Database
db = Database()  # 자동으로 프로젝트 루트의 keywords.db 사용
```

