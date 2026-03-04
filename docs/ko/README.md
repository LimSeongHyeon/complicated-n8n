# n8n Docker 다중 워커 구성

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

Docker 기반으로 n8n을 다중 워커 모드로 구성한 프로젝트입니다.

**[English](../../README.md)**

## 아키텍처

```
┌─────────────┐
│  n8n-main   │ ← 웹 UI 및 워크플로우 관리
│  (port:5678)│
└──────┬──────┘
       │
       ├─────→ PostgreSQL (데이터 저장)
       │
       ├─────→ Redis (작업 큐)
       │            ↑
       │            │
       ├────────────┴─────────────┐
       │                          │
┌──────┴──────┐          ┌───────┴─────┐
│ n8n-worker-1│          │ n8n-worker-2│
│  (워커)     │          │  (워커)     │
└─────────────┘          └─────────────┘
       │                          │
       └──────────┬───────────────┘
                  │
          ┌───────┴───────┐
          │ python-runner │ ← Python 스크립트 실행
          │  (port:8000)  │
          └───────────────┘
```

## 구성 요소

| 서비스 | 이미지 | 역할 |
|--------|--------|------|
| **postgres** | postgres:15-alpine | 워크플로우, 사용자, 실행 이력 데이터 저장 |
| **redis** | redis:7-alpine | Bull Queue 기반 작업 큐로 워크플로우 실행 분배 |
| **n8n-main** | n8nio/n8n:latest | 웹 UI, 워크플로우 편집기, webhook 수신 |
| **n8n-worker** | n8nio/n8n:latest | Redis에서 작업을 가져와 워크플로우 실행. 수평 확장 가능 |
| **python-runner** | 자체 빌드 (FastAPI) | n8n 워크플로우에서 Python 스크립트를 실행하는 HTTP 서버 |

## 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_USERNAME/n8n_01.git
cd n8n_01
```

### 2. 환경 변수 설정

```bash
cp .env.example .env

# 보안 키 생성
openssl rand -base64 32  # POSTGRES_PASSWORD에 사용
openssl rand -base64 32  # N8N_ENCRYPTION_KEY에 사용
```

`.env` 파일을 열어 플레이스홀더 값을 변경하세요.

### 3. 서비스 시작

```bash
docker-compose up -d
```

**http://localhost:5678** 에서 n8n에 접속합니다. 첫 접속 시 관리자 계정을 생성하게 됩니다.

## 환경 변수 설정

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `POSTGRES_PASSWORD` | PostgreSQL 비밀번호 | (필수 변경) |
| `N8N_ENCRYPTION_KEY` | 데이터 암호화 키 | (필수 변경) |
| `N8N_PORT` | n8n 웹 포트 | 5678 |
| `N8N_WORKER_REPLICAS` | 워커 인스턴스 개수 | 2 |
| `N8N_WORKER_CONCURRENCY` | 각 워커의 동시 처리 워크플로우 수 | 10 |
| `GENERIC_TIMEZONE` | 타임존 설정 | Asia/Seoul |
| `N8N_LOG_LEVEL` | 로그 레벨 (info, debug, error) | info |

## 워커 수 조정

`.env` 파일에서 워커 수를 변경하세요:

```bash
N8N_WORKER_REPLICAS=5
```

변경 후 재시작:

```bash
docker-compose up -d --scale n8n-worker=${N8N_WORKER_REPLICAS}
```

### 워커 모드 장점

1. **병렬 처리**: 여러 워크플로우를 동시에 실행
2. **확장성**: 워커를 추가하여 처리 능력 향상
3. **안정성**: 워커가 다운되어도 다른 워커가 작업 처리
4. **부하 분산**: Redis 큐를 통한 자동 작업 분배

## Python Runner

Python Runner는 FastAPI 기반 HTTP 서버로, n8n 워크플로우에서 Python 스크립트를 실행할 수 있게 해줍니다.

### 스크립트 추가

1. `python-runner/scripts/`에 Python 스크립트를 추가합니다
2. `python-runner/scripts/requirements.txt`에 의존성을 추가합니다
3. Runner가 자동으로 새 의존성을 감지하고 설치합니다

### 사용 예시

`python-runner/scripts/hello.py`에서 동작하는 예제를 확인하세요.

n8n에서 HTTP Request 노드로 호출:
```json
POST http://python-runner:8000/run
{
  "scriptName": "hello.py",
  "parameters": {"name": "World"}
}
```

## 운영

```bash
# 로그 확인
docker-compose logs -f
docker-compose logs -f n8n-main
docker-compose logs -f n8n-worker

# 상태 확인
docker-compose ps

# 서비스 중지
docker-compose down

# 데이터까지 완전 삭제
docker-compose down -v
```

## 백업

```bash
# PostgreSQL 백업
docker-compose exec postgres pg_dump -U n8n_user n8n > backup_$(date +%Y%m%d).sql

# 워크플로우 내보내기
docker-compose exec n8n-main n8n export:workflow --all --output=/home/node/.n8n/backup/
```

## 커스텀 노드

`custom-nodes/` 디렉토리에 커스텀 n8n 노드를 추가하면 자동으로 로드됩니다.

## 트러블슈팅

### 워커가 작업을 처리하지 않는 경우
1. Redis 확인: `docker-compose logs redis`
2. 워커 로그 확인: `docker-compose logs n8n-worker`

### 데이터베이스 연결 오류
```bash
docker-compose logs postgres
```

### 암호화 키 관련 오류
모든 서비스(main, worker)가 동일한 `N8N_ENCRYPTION_KEY`를 사용해야 합니다.

## 보안 권장사항

1. 첫 실행 전 `.env` 파일의 모든 비밀번호를 변경하세요
2. `N8N_ENCRYPTION_KEY`를 강력한 랜덤 문자열로 설정하세요
3. 프로덕션 환경에서는 HTTPS를 사용하세요
4. `.env` 파일을 절대 Git에 커밋하지 마세요
5. 정기적으로 백업을 수행하세요

## 기여하기

[CONTRIBUTING.md](../../CONTRIBUTING.md)를 참조하세요.

## 라이선스

이 프로젝트는 [MIT License](../../LICENSE)를 따릅니다.

> **참고**: 이 프로젝트는 Docker Compose 배포 구성을 제공합니다. n8n 자체는 [Sustainable Use License](https://github.com/n8n-io/n8n/blob/master/LICENSE.md)를 따릅니다.
