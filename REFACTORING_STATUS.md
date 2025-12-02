# 폴더 구조 리팩토링 진행 상황

## 새 구조

```
auto-content-poster/
├── src/
│   ├── agents/          # 에이전트들 (기존 유지)
│   ├── core/            # 핵심 로직
│   │   ├── database.py  # 데이터베이스 관리
│   │   └── config.py    # 환경 변수 로드
│   ├── services/        # 서비스 레이어
│   │   ├── search.py    # 검색 서비스
│   │   └── notion.py    # Notion API 서비스
│   └── utils/           # 유틸리티
│       └── helpers.py   # 헬퍼 함수들
├── scripts/             # 실행 스크립트
│   ├── auto_poster.py   # 메인 포스팅 스크립트
│   ├── scheduler.py     # 스케줄러
│   ├── check_and_redeploy.py
│   └── setup_curriculum.py
├── tools/               # 유틸리티 스크립트
│   └── check_setup.py
├── cron/                # 크론 스크립트
│   ├── enable_cron.sh
│   ├── enable_cron_with_check.sh
│   ├── disable_cron.sh
│   └── check_cron.sh
└── docs/                # 문서
```

## 진행 상황

- [x] 폴더 구조 생성
- [x] core/config.py 생성 (환경 변수 로드 통합)
- [x] core/database.py 이동 및 경로 수정
- [x] services/notion.py 생성 (notion_api.py + notion_poster.py 통합)
- [x] services/search.py 이동
- [x] utils/helpers.py 이동
- [x] scripts/ 파일들 이동
- [x] tools/ 파일들 이동
- [x] cron/ 파일들 이동
- [x] 모든 import 경로 수정
- [x] 기존 루트 파일들 정리 (참조용으로 남겨둠)

## 다음 단계

모든 import 경로를 새 구조에 맞게 수정해야 합니다.

