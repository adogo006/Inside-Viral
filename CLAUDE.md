# CLAUDE.md

이 파일은 Claude Code(claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

InsideViral은 DC 인사이드 갤러리 게시물을 크롤링하고, NLP 감성 분석을 수행하여 "혼돈지수" 바이럴 감성 지표를 산출하는 한국어 온라인 커뮤니티 감성 분석 시스템입니다.

## 아키텍처

Docker Compose 기반 멀티컨테이너 마이크로서비스:

```
[프론트엔드] → [FastApi] → [크롤러] → [NLP]
                    ↓
               [PostgreSQL]
```

| 서비스 | 내부 URL | 포트 |
|--------|----------|------|
| API (FastApi) | `http://api:8000/` | 8000 |
| NLP | `http://nlp:8001/` | 8001 |
| 크롤러 | `http://crawler:8002/` | 8002 |
| Nginx (프론트엔드) | `http://nginx:80/` | 80 |
| DB | `db:5432` | 5432 |

---

## 디렉토리별 상세

### FastApi/ — API 게이트웨이 (포트 8000)

크롤링 요청을 조율하고, DB에서 감정 데이터를 조회하여 프론트엔드에 제공하는 메인 API 서버.

#### main.py — 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 정상 응답 |
| `GET` | `/api/sentiments` | `average_sentiments_for_one_day` 테이블에서 감정 시계열 조회. `gall_id`와 `timeframe`(1D/7D/1M/1Y) 파라미터 |
| `POST` | `/crawl` | 크롤러에 크롤링 요청 전달. uuid 생성 → DB에 RequestLog 생성 → 크롤러 POST |
| `GET` | `/crawl/{request_id}` | RequestLog로 상태 조회 |
| `POST` | `/crawl/callback` | 크롤러 완료 후 콜백. DB 업데이트 → 웹훅 알림 → NLP 감정 할당 요청 |
| `POST` | `/crawl/cancel/{request_id}` | 실행 중인 크롤링 취소 |
| `GET` | `/crawl/healthcheck` | 크롤러 서비스 상태 확인 |

**주요 함수:**
- `notify_user_or_admin(request_id, status, error_message, saved_rows)` — 콜백 수신 후 `ADMIN_WEBHOOK_URL`으로 웹훅 전송 (없으면 로그만)
- `request_nlp_assign_sentiment(request_id)` — `NLP_URL/assign-sentiment`에 POST하여 NLP 처리 트리거

#### api_crud.py — RequestLog CRUD

- `api_create_request_log(db, request_log)` — PostgreSQL upsert (`INSERT ON CONFLICT DO UPDATE`). 성공 0, 실패 -1
- `api_get_request_log(db, request_id)` — request_id로 1건 조회
- `api_update_request_log(db, request_id, request_log)` — 기존 로그 필드 업데이트

#### scheduler_runtime.py — APScheduler 런타임

- `start_scheduler()` — `ENABLE_CLEANUP_SCHEDULER=true`이면 실행. `DB_CLEANUP_CRON`(기본 `0 4 * * *`, 매일 04:00 UTC)으로 `cleanup_not_finished_logs` 등록
- `stop_scheduler()` — graceful shutdown

#### scheduler_jobs.py (develop 브랜치) — 스케줄 Job

- `cleanup_not_finished_logs()` — `finished_at IS NOT NULL`인 RequestLog 삭제
- `compute_average_sentiment_in_scheduler()` — 모든 갤러리에 대해 `compute_average_sentiment(db, gall_id, datetime.now(), period=1)` 호출
- `delete_low_priority_words_in_scheduler()` — `update_count` 오름차순으로 threshold 초과분 삭제
- `request_crawlling_in_scheduler()` — 사전 정의된 4개 갤러리에 대해 1일 전 데이터 크롤링 요청. `SCHEDULER_CRAWL_RETRY_LIMIT`, `SCHEDULER_CRAWL_TIMEOUT_SEC` 환경변수 사용

#### schemas.py — Pydantic 모델

- `CrawlRelayRequest` — `gall_main_url`(필수), `days`(기본 1), `days_ago`(기본 0)
- `CrawlerCallbackPayload` — `request_id`, `status`(succeeded/failed/cancelled/cancelling), `error_message`, `finished_at`, `saved_rows`
- `RequestLogUpsert` — RequestLog upsert용. `from_attributes=True`
- `SentimentResponse` — `gall_id`, `timeframe`, `data[]` (date + average_sentiment)

---

### crawling/ — DC 인사이드 크롤러 (포트 8002)

DC 갤러리에서 게시글을 크롤링하여 `words` 테이블에 저장하는 서비스.

#### main.py — FastAPI 서버

**엔드포인트:**

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/healthcheck` | 서비스 상태 및 활성 작업 수 반환 |
| `POST` | `/crawl` | 크롤링 요청 수락. `MAX_CONCURRENT_TASKS`(5개) 제한. `asyncio.create_task`로 비동기 실행 |
| `POST` | `/cancel/{request_id}` | `asyncio.Task.cancel()`으로 특정 요청 강제 종료 |

**핵심 함수:**
- `send_callback(callback_url, request_id, status, error_message, saved_rows)` — 완료/실패 시 API 콜백 전송
- `task_crawl_and_save(url, days, previousDays, request_id, callback_url)` — 비동기 크롤링 작업. `runtime_state.active_tasks` 증감 관리

**동시성 제어:**
- `MAX_CONCURRENT_TASKS = 5` (runtime_state.py)
- `active_tasks` 카운터로 동시 작업 추적

#### Crawling.py — 실제 크롤링 로직

**핵심 함수:**

- `startCrawler(initUrl, days, previousDays, request_id)` — 메인 크롤러. DC 갤러리 URL과 기간을 받아 게시글 크롤링 시작
- `firstListParsing(initUrl, now, previousDays, request_id)` — 지정 기간 전날에 해당하는 게시글 번호(gallId, dataNum)를 이진 탐색으로 찾음. 최대 120회 탐색, 50회 에러 시 fallback
- `contentCrawler(Words, gallId, dataNum, firstUrl, now, period, request_id)` — 게시글 본문 파싱. 제목+본문을 합쳐 `wordContent`로 저장. 100개마다 DB 일괄 저장

**User-Agent 로테이션:** 5개 랜덤 헤더 사용 (IP 차단을 방지)

**dynamic_sleep_seconds(min, max):** 활성 작업 수에 따라 동적으로 sleep 시간 조절. 부하 적을수록 빠르게, 5개 풀工作时 기존 딜레이 유지

#### crud_crawling.py — DB 저장 헬퍼

- `save_in_database(db, word_list)` — `words` 테이블에 일괄 upsert. `on_conflict_do_nothing`으로 중복 방지
- `delete_whitespace_word(db)` — `wordContent`가 빈 문자열이나 NULL인 레코드 삭제
- `export_to_txt(db)` — 모든 `wordContent`를 `db_content.txt`로 내보내기 (NLP 모델 학습용)

#### runtime_state.py

```python
MAX_CONCURRENT_TASKS = 5
active_tasks = 0
```

---

### NLP/ — 감성 분석 서비스 (포트 8001)

크롤링된 텍스트에 감정 점수를 부여하고, 키워드 가중치를 업데이트하는 서비스.

#### main.py — FastAPI 서버

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/healthcheck` | 서비스 정상 응답 |
| `POST` | `/extract-keyword` | `words` 테이블에서 `state=PENDING`인 문장을 가져와 키워드 가중치 계산 후 `weights` 테이블 업데이트 |
| `POST` | `/assign-sentiment` | `request_id`에 해당하는 문장에 감정 점수 부여 |

**핵심 함수:**
- `do_extract_keyword()` — `asyncio.to_thread`로 동기 NLP 작업 실행
- `do_assign_sentiment(id)` — 동일하게 스레드풀에서 실행

#### SentimentAnalyzer.py — 감성 분석기

`jaehyeong/koelectra-base-v3-generalized-sentiment-analysis` 모델 사용.

**`analyze_batch(sentences, weights, batch_size=32)`:**
1. ELECTRA 모델로 기본 감정 점수 (`label='1'`→양수, `label='0'`→음수)
2. `weights` 테이블의 키워드 가중치로 보정 (`adjustment += weight`)
3. `final_score = primary_score + adjustment`
4. 0.05초 sleep으로 rate limit 방지

**`main(sentences, weights)`:** 배치 분석 후 `[{word_id, word_content, final_score}]` 형태 반환

#### KeywordExtractor.py — 키워드 가중치 계산

`sentence-transformers/snunlp/KR-SBERT-V40K-klueNLI-augSTS`로 임베딩, `soynlp`로 키워드 추출.

**`calculate_weights(sentences, sentence_scores, all_embeddings, dataset_centroid, classifier)`:**

| 조건 | 설명 |
|------|------|
| 빈도 ≥ 5 | 모델 신뢰도 과보호 방지 |
| cohesion_forward ≥ 0.4 | 단어 응집도 |
| right_branching_entropy ≥ 1.0 | 우측 분기 엔트로피 |
| 모델 confidence ≤ 0.92 | 이미 모델이 아는 단어 배제 |

**가중치 공식:**
```
weight = (sentiment_factor * cohesion_forward) * (semantic_similarity * novelty_bonus)
semantic_similarity = cos_sim(word_centroid, dataset_centroid)
novelty_bonus = 2.0 - model_confidence
```
최종 weight clipping: `[-10.0, 10.0]`

#### crud_NLP.py — NLP용 CRUD

- `get_primary_sentences(db)` — `state=PENDING`이고 `learning_state=PENDING`인 문장 조회. `learning_state`를 `COMPLETED`로 변경 (중복 처리 방지)
- `get_sentences(db, request_id)` — `request_id` 기준 필터링. `request_id="null"`이면 전체 `PENDING` 문장
- `get_weights(db)` — `weights` 테이블 전체 조회
- `update_weights(db, weight_list)` — 키워드 가중치 upsert. `weight = (기존 * 4/5) + (신규 * 1/5)` (이동 평균), `update_count` 1 증가
- `update_sentiment(db, results)` — 각 Word 레코드의 `sentiment`와 `state`를 `COMPLETED`로 업데이트

---

### DB_manager/ — 공통 DB 모델

#### models.py — SQLAlchemy 모델

| 테이블 | 설명 |
|--------|------|
| `Word` | 원시 단어/문장 (`gallId`, `date`, `wordContent`, `sentiment`, `state`, `learning_state`, `request_id`). UniqueConstraint: (gallId, date, wordContent) |
| `WeightInWord` | 키워드 가중치 (`word`, `weight`, `update_count`). UniqueConstraint: word |
| `RequestLog` | 크롤링 요청 생명주기 추적 (`request_id`, `gall_main_url`, `days`, `days_ago`, `status`, `error_message`, `saved_rows`, `created_at`, `finished_at`) |
| `AverageSentimentForOneDay` | 일별 평균 감정 (`gall_id`, `date`, `average_sentiment`). UniqueConstraint: (gall_id, date) |

**Enum:**
- `ProcessState`: PENDING → COMPLETED (NLP 감정 할당 완료)
- `LearningState`: PENDING → COMPLETED (키워드 학습 완료)
- `RequestStatus`: PENDING → RUNNING → SUCCEEDED/FAILED/CANCELLED/CANCELLING/DISPATCH_FAILED

#### database.py — DB 연결

```python
DB_URL = postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}
```

#### crud.py — 공통 CRUD

- `create_word_entry(db, gall_id, up_date, word_content, sentiment_score)` — Word 레코드 생성
- `get_words(db, skip, limit)` — Word 전체 조회 (페이지네이션)
- `get_words_gallId(db, gall_id, limit)` — 특정 갤러리 Word 조회
- `get_words_date(db, gall_id, days)` — 특정 갤러리 N일 이내 Word 조회
- `delete_word(db, word_id)` — Word 레코드 삭제
- `compute_average_sentiment(db, gall_id, target_date, period)` — `words` 테이블에서 평균 계산 → `average_sentiments_for_one_day` 테이블에 upsert
- `delete_low_priority_words(db, threshold)` — `update_count` 오름차순으로 threshold 초과분 삭제
- `get_request_status(db, request_id)` — RequestLog.status 반환

---

### Nginx/src/ — 프론트엔드 (정적 파일)

`lightweight-charts`로 감정 지수 시계열 차트 렌더링.

#### script.js — 차트 로직

- `initChart()` — `lightweight-charts` 초기화, `lineSeries` 생성
- `loadChartData()` — `GET /api/sentiments?gall_id={gallery}&timeframe={tf}` 호출
- `renderChartData(data)` — API 응답 `data[]`의 `date` 필드를 UTC timestamp로 변환하여 차트에 표시
- `returnErr()` — API 실패/빈 데이터 시 "데이터를 불러올 수 없습니다" 메시지 표시
- `updateEmotionGif(chartData)` — 마지막 값 ≥ 75 → `happy.gif`, < 75 → `sad.gif`
- `changeTopic(text, gallId)` — 갤러리 변경 시 재조회

**갤러리 ID:** `us-stocks`, `ko-stocks`, `crypto`, `ent`

#### index.html — UI 구조

- 헤더: 갤러리 선택 드롭다운 + timeframe 버튼 (1D/7D/1M/1Y)
- 차트 컨테이너 + 이모션 GIF 오버레이
- `resetZoom()` 버튼

---

## 실행 방법

```bash
# 전체 서비스 시작
docker-compose -f .devcontainer/docker-compose.yml up

# 크롤러 컨테이너에서 크롤링 직접 실행
docker exec -it insideviral_devcontainer-crawler-1 python3 main.py

# 크롤러 로그 확인
docker logs -f insideviral_devcontainer-crawler-1

# Nginx 이미지 빌드
docker build -f .devcontainer/Nginx_env/Dockerfile -t inside-viral-nginx .
```

개별 서비스: `uvicorn main:app --host 0.0.0.0 --port [포트]`

---

## 환경 변수

`.env` 파일 (`.devcontainer/.env`)에서 관리:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_PORT` | PostgreSQL 연결 | |
| `API_CALLBACK_URL` | 크롤러 → API 콜백 URL | `http://api:8000/crawl/callback` |
| `CRAWLER_URL` | 크롤러 서비스 URL | `http://crawler:8002/` |
| `NLP_URL` | NLP 서비스 URL | `http://nlp:8001/` |
| `ENABLE_CLEANUP_SCHEDULER` | 정리 스케줄러 활성화 | `true` |
| `DB_CLEANUP_CRON` | 정리 스케줄 cron | `0 4 * * *` |
| `DB_CLEANUP_RETENTION_DAYS` | 로그 보관 일수 | `7` |
| `SCHEDULER_CRAWL_RETRY_LIMIT` | 크롤링 재시도 횟수 | `2` |
| `SCHEDULER_CRAWL_TIMEOUT_SEC` | 크롤링 타임아웃 (초) | `1800` |
