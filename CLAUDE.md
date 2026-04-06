# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

Inside-Viral은 DC 인사이드 갤러리 게시물을 크롤링하고, NLP 감성 분석을 수행하여 "공포 지수" 바이럴 감성 지표를 산출하는 한국어 온라인 커뮤니티 감성 분석 시스템입니다.

## 아키텍처

Docker Compose 기반 멀티컨테이너 마이크로서비스:
- **FastApi** (포트 8000) - API 게이트웨이
- **NLP** (포트 8001) - 감성 분석 및 키워드 추출
- **crawling** (포트 8002) - DC 인사이드 웹 크롤러
- **DB_manager** - 공통 SQLAlchemy 모델 및 DB 유틸리티
- **PostgreSQL 16** - Docker 기반 데이터베이스

서비스 간 내부 Docker 네트워크 (`insideViral-net`)로 통신:
- API는 `http://crawler:8002`, `http://nlp:8001`로 접근
- 모든 서비스는 `db:5432`에서 PostgreSQL에 연결

## 주요 명령어

```bash
# 전체 서비스 시작
docker-compose -f .devcontainer/docker-compose.yml up

# 컨테이너에서 크롤러 직접 실행
docker exec -it insideviral_devcontainer-crawler-1 python3 main.py

# 크롤러 로그 확인
docker logs -f insideviral_devcontainer-crawler-1
```

개별 서비스 실행: `uvicorn main:app --host 0.0.0.0 --port [포트]`

## 주요 구현 사항

- **PYTHONPATH**: 모든 서비스에서 `PYTHONPATH=/workspaces` 설정, 프로젝트 루트를 `/workspaces`에 마운트
- **NLP 모델**: HuggingFace 모델은 이미지 빌드 시 `download_models.py`에서 다운로드
- **데이터베이스**: `words` 테이블(gallId, date, wordContent, sentiment, state)과 `weights` 테이블(word, weight)
- **상태 추적**: `ProcessState` enum(PENDING → COMPLETED)으로 NLP 처리 상태 관리
- **크롤링 대상**: DC 인사이드 gall.dcinside.com 한국 커뮤니티 포럼

## 디렉토리 구조

```
FastApi/           - API 게이트웨이 서비스
crawling/          - 웹 크롤러 서비스
NLP/               - NLP/감성 분석 서비스
DB_manager/        - 공통 DB 모델 및 database.py
.devcontainer/     - Docker 환경 (Dockerfile, docker-compose)
```

## 환경 변수

환경 설정은 `.env` 파일에 있으며(DB_USER, DB_PASS, DB_NAME), docker-compose의 `env_file`로 로드됩니다.