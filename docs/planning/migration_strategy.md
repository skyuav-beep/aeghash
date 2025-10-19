
# Alembic 마이그레이션 전략 (Codex Task1)

## 1. 목표
- Wallet 및 Mining 테이블 구조를 버전 관리하여 배포 환경에 안전하게 반영한다.
- 개발/스테이징/운영 환경에서 동일한 스키마를 유지하고 롤백 가능하도록 설계한다.

## 2. 기본 구성
- Alembic 초기화
  ```bash
  alembic init migrations
  ```
- `alembic.ini`
  - `sqlalchemy.url`은 환경 변수에서 주입 (`env.py`에서 `os.environ["DATABASE_URL"]`)하도록 수정.
- `migrations/env.py`
  - `from aeghash.infrastructure.database import Base`
  - `target_metadata = Base.metadata`
  - 세션 관리: contextmanager를 사용하거나 Alembic 제공 세션 사용.

## 3. 마이그레이션 작성 원칙
- 모델 변경 후 `alembic revision --autogenerate -m "create wallet tables"`
- 자동 생성된 스크립트 검토 후 필요 시 수동 수정 (인덱스, 제약조건 등).
- 주요 테이블
  - `wallets`, `wallet_transactions`
  - `mining_balances`, `mining_withdrawals`
- Seed/Init 데이터는 별도 스크립트로 관리 (Alembic 스크립트에서 직접 데이터 삽입은 지양).

## 4. 배포 파이프라인
- 개발 환경: 로컬 SQLite/포스트그레 테스트 DB에 적용 → 테스트 통과 확인.
- 스테이징/운영: 배포 직전 `alembic upgrade head` 실행.
- 롤백 전략: 문제 발생 시 `alembic downgrade -1` 혹은 특정 revision으로 롤백.
- CI 체크: PR에서 `alembic upgrade head`를 테스트 DB에 실행해 스키마 검증.

## 5. 이후 작업
1. Alembic 설정 파일과 migrations 디렉터리 생성.
2. 현재 모델을 기준으로 첫 마이그레이션 작성 (`create initial wallet/mining tables`).
3. 배포 스크립트에 Alembic 명령을 통합하고 Git Hooks/CI 파이프라인에 추가.
