# IT News Mail - Setup Guide

## 설치 및 설정 가이드

### 1. 사전 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)
- 이메일 계정 (Gmail 권장)
- OpenAI API 키 또는 Anthropic API 키

### 2. 설치

#### 2.1 저장소 클론 (또는 다운로드)

```bash
cd it-news-mail
```

#### 2.2 가상환경 생성 (권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 2.3 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 설정

#### 3.1 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 입력합니다:

```bash
cp .env.example .env
```

`.env` 파일 내용:

```env
# AI API Keys (둘 중 하나만 있으면 됩니다)
OPENAI_API_KEY=sk-your-openai-api-key-here
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# Email Configuration
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_FROM=your_email@gmail.com
```

#### 3.2 Gmail 앱 비밀번호 생성

1. Gmail 계정의 2단계 인증 활성화
2. Google 계정 > 보안 > 앱 비밀번호로 이동
3. 앱 비밀번호 생성
4. 생성된 비밀번호를 `.env` 파일의 `EMAIL_PASSWORD`에 입력

#### 3.3 설정 파일 수정

`config/config.yaml` 파일을 열어 필요한 설정을 수정합니다:

```yaml
# AI 제공자 선택 (openai 또는 anthropic)
ai:
  provider: openai  # 또는 anthropic

# 수신자 이메일 추가
email:
  recipients:
    - team1@example.com
    - team2@example.com
```

#### 3.4 뉴스 사이트 목록 커스터마이징 (선택사항)

`site-list.txt` 파일을 수정하여 원하는 뉴스 사이트를 추가/제거할 수 있습니다:

```
# Format: category|site_name|url|selector_type|article_selector
ROBOTICS|Your Site|https://example.com|css|article
```

### 4. 실행

#### 4.1 수동 실행

```bash
python main.py
```

#### 4.2 자동 실행 설정 (스케줄링)

##### Windows (작업 스케줄러)

1. 작업 스케줄러 열기
2. "기본 작업 만들기" 선택
3. 이름: "IT News Mail"
4. 트리거: 매일, 원하는 시간 설정
5. 작업: "프로그램 시작"
6. 프로그램/스크립트: `C:\path\to\venv\Scripts\python.exe`
7. 인수 추가: `C:\path\to\it-news-mail\main.py`
8. 시작 위치: `C:\path\to\it-news-mail`

##### Linux/Mac (Cron)

```bash
# Cron 작업 편집
crontab -e

# 매일 오전 9시에 실행
0 9 * * * cd /path/to/it-news-mail && /path/to/venv/bin/python main.py >> /path/to/logs/cron.log 2>&1
```

### 5. 테스트

#### 5.1 설정 확인

```bash
python -c "from src.utils import load_config; config = load_config(); print('Config loaded successfully!')"
```

#### 5.2 데이터베이스 초기화 확인

```bash
python -c "from src.database.db import init_database; from src.utils import load_config; config = load_config(); db = init_database(config['database']); print('Database initialized!')"
```

#### 5.3 단위 테스트 실행 (pytest 설치 필요)

```bash
pip install pytest
pytest tests/
```

### 6. 문제 해결

#### 6.1 로그 확인

로그 파일은 `logs/` 디렉토리에 저장됩니다:

```bash
# 최근 로그 확인
tail -f logs/it-news-mail.log

# Windows
type logs\it-news-mail.log
```

#### 6.2 일반적인 문제

**문제: ImportError 발생**
```bash
# 해결: 패키지 재설치
pip install -r requirements.txt --force-reinstall
```

**문제: API 키 오류**
```
# 해결: .env 파일에 올바른 API 키가 있는지 확인
# ${OPENAI_API_KEY} 같은 플레이스홀더가 남아있지 않은지 확인
```

**문제: 이메일 전송 실패**
```
# 해결:
# 1. Gmail 앱 비밀번호를 사용하고 있는지 확인
# 2. 2단계 인증이 활성화되어 있는지 확인
# 3. "보안 수준이 낮은 앱" 설정 확인 (Gmail)
```

**문제: 크롤링 실패**
```
# 해결:
# 1. 인터넷 연결 확인
# 2. site-list.txt의 URL이 유효한지 확인
# 3. CSS 셀렉터가 여전히 유효한지 확인 (사이트 구조 변경 가능)
```

### 7. 데이터베이스 관리

#### 7.1 데이터베이스 확인

```bash
# SQLite 데이터베이스 열기
sqlite3 data/news.db

# 테이블 목록 확인
.tables

# 뉴스 개수 확인
SELECT COUNT(*) FROM news;

# 최근 뉴스 확인
SELECT title, site, created_at FROM news ORDER BY created_at DESC LIMIT 10;

# 종료
.quit
```

#### 7.2 데이터베이스 초기화 (주의!)

```bash
# 기존 데이터베이스 삭제 (모든 데이터 손실!)
rm data/news.db

# 다시 실행하면 새 데이터베이스 생성됨
python main.py
```

### 8. 커스터마이징

#### 8.1 이메일 템플릿 수정

`src/mailer/mailer.py`의 `_generate_html_email` 메서드를 수정하여 이메일 디자인을 변경할 수 있습니다.

#### 8.2 요약 프롬프트 수정

`src/summarizer/summarizer.py`의 `_create_summary_prompt` 메서드를 수정하여 요약 스타일을 변경할 수 있습니다.

#### 8.3 크롤링 로직 수정

`src/crawler/crawler.py`를 수정하여 크롤링 방식을 커스터마이즈할 수 있습니다.

### 9. 다음 단계

- [ ] 실제 운영 환경에 배포
- [ ] 모니터링 및 알림 설정
- [ ] 추가 뉴스 소스 등록
- [ ] 사용자 피드백 수집
- [ ] 동영상 생성 기능 구현 (Sora API 출시 시)

### 10. 지원

문제가 발생하면:
1. `logs/` 디렉토리의 로그 파일 확인
2. GitHub Issues에 문제 리포트
3. README.md의 "향후 개선 사항" 참조
