# 데이터베이스 & 트랜잭션 전략 (Codex Task1)

## 1. 목표
- Wallet/Mining 서비스가 의존하는 SQLAlchemy 저장소를 PostgreSQL 기반 운영 환경에 연결하기 위한 전략을 정리한다.
- 세션 수명, 트랜잭션 범위, 재시도 정책을 정의해 안전한 지갑/출금 처리를 보장한다.

## 2. 인프라 구성
- 드라이버: `postgresql+psycopg` (async 연결 필요 시 `asyncpg` 고려).
- 연결 방식
  - 앱 서버: SQLAlchemy `create_engine_and_session` 헬퍼(`src/aeghash/infrastructure/database.py`)를 PostgreSQL URL로 초기화.
  - 배치 작업: 동일 헬퍼 재사용, 세션을 contextmanager로 감싸 자동 커밋/롤백 처리.
- 환경 변수 (`.env`)
  - `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/aeghash`
  - `SQLALCHEMY_ECHO=false`, `SQLALCHEMY_POOL_SIZE=10` 등 추가 설정 고려.

## 3. 세션 & 트랜잭션 정책
- 기본 철학: 요청 단위 트랜잭션
  - 웹 요청 또는 배치 작업 단위로 세션을 생성하고 종료 시 commit/rollback.
- 컨텍스트 매니저 예시:

```python
from contextlib import contextmanager
from aeghash.infrastructure.session import SessionManager

session_manager = SessionManager(settings.database_url)

with session_manager.session_scope() as session:
    repo = SqlAlchemyWalletRepository(session)
    # ... business logic ...

# 또는 Wallet/Miner 서비스 스코프 활용
from aeghash.infrastructure.bootstrap import wallet_service_scope

with wallet_service_scope(session_manager, mblock_client_factory, settings) as wallet_service:
    wallet_service.create_wallet(user_id="user-1")
```

- Wallet/Mining 서비스는 세션 기반 Repository 인스턴스를 주입받아 사용하며, 서비스 호출자는 위 컨텍스트로 세션 수명을 제어한다.

## 4. 재시도 & 보상 로직
- 네트워크 오류/Deadlock etc.
  - `sqlalchemy.exc.OperationalError`, `DBAPIError`에 대해 최대 3회 지수 백오프 재시도.
  - 재시도 실패 시 서비스 레이어에서 Repository에 실패 상태 기록 후 호출자에게 예외 전달.
- Wallet 전송 보상
  - 실패 시 상태 `failed`로 기록 후 알림/승인 담당자에게 전달(추후 알림 시스템 연결).
  - Transit 요청이 `pending-transit`에서 장시간 머무를 경우 Polling 또는 콜백을 통해 최종 상태 업데이트.
- Mining 출금 보상
  - HashDam API 실패 시 `failed` 로그와 함께 재시도 큐에 등록.
  - Withdraw ID 미수신(Empty) 상태는 재시도 시 새로운 요청 ID로 업데이트.

## 5. 테스트 전략
- 단위 테스트: 인메모리/Mock 기반으로 실패 시 상태 기록 확인 (완료됨).
- 통합 테스트: SQLite→PostgreSQL 전환 시 `sqlalchemy.url`을 테스트 DB로 설정하여 마이그레이션/트랜잭션 롤백 테스트 수행.
- 배포 전 체크
  - 마이그레이션 툴(Alembic)로 스키마 버전 관리.
  - 샌드박스 환경에서 HashDam/MBlock 실키와 PostgreSQL 연결 검증.

## 6. 다음 단계
1. PostgreSQL 연결 URL을 `.env` 및 배포 환경 시크릿에 등록.
2. 세션 컨텍스트 헬퍼를 `src/aeghash/infrastructure/session.py` 등으로 분리하고 서비스 초기화 코드에 통합.
3. Alembic 기반 마이그레이션 스크립트를 작성하여 Wallet/Miner 테이블 스키마를 관리.
4. 재시도 로직을 구체화(예: `tenacity` 라이브러리 또는 자체 백오프 구현)하고 실패 알림 흐름을 Event/Queue와 연계.
