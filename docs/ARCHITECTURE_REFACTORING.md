# 🏗️ Modular Multi-Agent Architecture 구조 변경 계획

## 📁 현재 구조

```
auto-content-poster/
├── agents/                    # 모든 에이전트
│   ├── __init__.py
│   ├── base.py
│   ├── agent_chain.py
│   ├── search_agent.py
│   ├── validation_agent.py
│   ├── fact_check_agent.py
│   ├── content_agent.py
│   ├── posting_agent.py
│   └── keyword_inference_agent.py
├── auto_poster.py            # 메인 진입점
├── scheduler.py              # 크론 작업
├── database.py               # 데이터베이스
├── search.py                 # 검색 유틸리티
├── notion_api.py             # Notion API
├── notion_poster.py          # Notion 포스팅 래퍼
├── utils.py                  # 유틸리티 함수
├── setup_curriculum.py       # 커리큘럼 설정
├── check_setup.py            # 설정 확인
└── docs/                     # 문서
```

## 🎯 새로운 Modular 구조 (제안)

```
auto-content-poster/
├── src/                       # 소스 코드
│   ├── agents/                # 에이전트들
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── chain.py           # agent_chain.py → chain.py
│   │   ├── search.py
│   │   ├── validation.py
│   │   ├── fact_check.py
│   │   ├── content.py
│   │   ├── posting.py
│   │   └── inference.py
│   ├── core/                  # 핵심 로직
│   │   ├── __init__.py
│   │   ├── database.py        # database.py
│   │   └── config.py          # 설정 관리
│   ├── services/              # 서비스 레이어
│   │   ├── __init__.py
│   │   ├── search_service.py  # search.py
│   │   ├── notion_service.py  # notion_api.py, notion_poster.py
│   │   └── posting_service.py # 포스팅 로직
│   └── utils/                 # 유틸리티
│       ├── __init__.py
│       ├── language.py        # 언어 검증 (utils.py의 일부)
│       └── text.py            # 텍스트 처리 (utils.py의 일부)
├── scripts/                   # 실행 스크립트
│   ├── auto_poster.py         # 메인 진입점
│   ├── scheduler.py           # 크론 작업
│   └── setup_curriculum.py    # 커리큘럼 설정
├── docs/                      # 문서
│   ├── AGENT_ARCHITECTURE.md
│   ├── AGENT_FLOW.md
│   └── ARCHITECTURE_REFACTORING.md
├── tests/                     # 테스트 (향후)
│   └── __init__.py
├── check_setup.py             # 설정 확인
├── requirements.txt
└── README.md
```

## ⚠️ 주의사항

이 구조 변경은 **대규모 리팩토링**이 필요합니다:
- 모든 import 경로 수정 필요
- 상대 경로 변경
- 실행 스크립트 경로 수정

현재 상태에서는 **문서화 완료**로 마무리하고, 실제 구조 변경은 단계적으로 진행하는 것을 권장합니다.

## 📝 현재 완료된 작업

✅ 사용되지 않는 파일 삭제:
- `main.py`
- `main_agent.py`
- `content_generator.py`
- `generate_english_only.py`
- `publish_mcp.py`
- `test_notion_api.py`

✅ 에이전트 문서화:
- `docs/AGENT_ARCHITECTURE.md`: 에이전트 상세 설명
- `docs/AGENT_FLOW.md`: 플로우 다이어그램

✅ 설정 스크립트 업데이트:
- `check_setup.py`: 필수 파일 목록 업데이트

## 🔄 다음 단계 (선택사항)

구조 변경을 원하시면 다음 순서로 진행할 수 있습니다:

1. **src/** 디렉토리 생성
2. 파일 이동 및 import 경로 수정
3. 테스트 및 검증
4. 문서 업데이트

하지만 현재 구조도 충분히 모듈화되어 있으며, 문서화가 완료되어 유지보수가 용이합니다.

