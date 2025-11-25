# 자동 노션 포스팅 시스템 🤖

키워드를 등록하면 매일 자동으로 최신 정보를 검색하고, AI가 학습 스토리 형식으로 글을 작성하여 노션에 포스팅하는 시스템입니다.

## ✨ 주요 기능

- 🔍 **자동 검색**: DuckDuckGo 무료 검색
- ✍️ **AI 콘텐츠 생성**: Groq API 무료 티어 사용
- 📚 **학습 스토리 형식**: 초보자가 하나씩 알아가는 스토리로 작성
- 🔗 **자동 키워드 추론**: 이전 포스팅 기반 다음 학습 주제 자동 추론
- 📝 **노션 자동 포스팅**: 한글 + 영문 각 1개씩 자동 포스팅
- ⏰ **완전 자동화**: 크론으로 매일 오전 10시 자동 실행
- 🆓 **완전 무료**: 모든 서비스 무료 티어 사용

## 🚀 빠른 시작

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음을 설정하세요:

```env
# Groq API (무료) - https://console.groq.com 에서 발급
GROQ_API_KEY=gsk_your_groq_api_key_here

# Notion API (무료) - https://www.notion.so/my-integrations 에서 발급
NOTION_API_KEY=secret_your_notion_api_key_here
NOTION_PARENT_PAGE_ID=your_parent_page_id_here

# 완전 자동화 (다음 키워드 자동 활성화)
AUTO_ACTIVATE_NEXT_KEYWORD=true
```

**Notion 설정:**
1. https://www.notion.so/my-integrations 접속
2. "New integration" 생성
3. Internal Integration Token을 `NOTION_API_KEY`에 설정
4. 부모 페이지를 Integration과 공유

### 2. 첫 번째 키워드 추가

```bash
python3 main.py add-keyword "AI"
```

### 3. 크론 설정 (매일 오전 10시 자동 실행)

```bash
# Python 경로 확인
which python3

# 크론 편집
crontab -e

# 다음 라인 추가 (Python 경로는 위 결과로 변경)
0 10 * * * cd /Users/leo/auto-content-poster && /usr/bin/python3 auto_poster.py >> /Users/leo/auto-content-poster/cron.log 2>&1
```

### 4. 완료!

이제 매일 오전 10시에 자동으로:
- 활성 키워드 처리
- 한글 + 영문 포스팅 각 1개 생성
- 노션에 자동 포스팅
- 다음 키워드 자동 추론 및 활성화

## 📋 사용 방법

### 키워드 관리

```bash
# 키워드 추가
python3 main.py add-keyword "키워드"

# 키워드 목록
python3 main.py list-keywords

# 키워드 활성화/비활성화
python3 main.py toggle-keyword "키워드"

# 키워드 삭제
python3 main.py delete-keyword "키워드"
```

### 수동 실행

```bash
# 자동 포스팅 실행 (한글 + 영문)
python3 auto_poster.py
```

### 크론 제어

```bash
# 크론 중지
./disable_cron.sh

# 크론 활성화
./enable_cron.sh

# 크론 상태 확인
./check_cron.sh
```

## 🎯 작동 방식

1. **첫 번째 키워드만 처리**: 첫 번째 활성 키워드만 처리합니다
2. **학습 스토리 형식**: "처음에는 모르고 있었지만..." 형식으로 작성
3. **자동 키워드 추론**: 이전 포스팅 기반으로 자연스러운 다음 학습 주제 추론
4. **완전 자동화**: 포스팅 완료 후 현재 키워드 비활성화, 다음 키워드 자동 활성화

**예시 학습 경로:**
```
AI → 머신러닝 → 딥러닝 → 신경망 ...
```

## 💰 비용

**완전 무료!** 추가 비용 없습니다.

- **Groq API**: 무료 티어 (매우 넉넉함, 0.1% 미만 사용)
- **DuckDuckGo**: 완전 무료
- **Notion API**: 무료 플랜
- **크론**: macOS 내장 기능 (무료)

## ⚙️ 시스템 요구사항

- Python 3.8+
- macOS / Linux
- 인터넷 연결

## 📁 주요 파일

- `auto_poster.py`: 자동 포스팅 메인 스크립트
- `main.py`: 키워드 관리 CLI
- `agents/`: A2A 에이전트 체인
- `database.py`: SQLite 데이터베이스 관리
- `.env`: 환경 변수 설정

## 🔧 문제 해결

### 크론이 실행되지 않음
```bash
# 상태 확인
./check_cron.sh

# 로그 확인
tail -f cron.log
```

### API 오류
- `.env` 파일의 API 키 확인
- Notion 페이지가 Integration과 공유되었는지 확인

### 키워드 확인
```bash
python3 main.py list-keywords
```

## 📚 추가 정보

- **학습 스토리 형식**: 초보자가 하나씩 알아가는 과정을 스토리로 작성
- **자동 키워드 추론**: 이전 포스팅 내용 기반 자연스러운 다음 주제 추론
- **중복 방지**: 오늘 이미 포스팅했는지 자동 확인
- **출처 및 면책문구**: 자동으로 포함됨

## 🎉 완전 자동화

첫 번째 키워드만 추가하면:
- ✅ 매일 자동 포스팅
- ✅ 다음 키워드 자동 추론
- ✅ 학습 경로 자동 따라가기
- ✅ 더 이상 할 일 없음!

---

**이제 시작하세요!** 🚀
