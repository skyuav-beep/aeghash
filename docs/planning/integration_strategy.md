# Wallet & Mining Service 통합 전략 (Codex Task1)

## 1. 목적
- HashDam/MBlock 어댑터를 서비스 계층과 연결하여 실제 비즈니스 로직(지갑 발급, 토큰 전송, 채굴 출금)을 구현할 준비를 갖춘다.
- 데이터 저장 계층(Repository)을 명확히 정의해 포인트 지갑·정산 모듈과 연동하기 위한 인터페이스를 제공한다.

## 2. 신규 구성요소
- `src/aeghash/core/repositories.py`: Wallet/Mining 서비스가 의존하는 Repository 프로토콜과 DTO (`WalletRecord`, `TransactionRecord`, `MiningBalanceRecord`, `WithdrawalRecord`) 정의.
- `src/aeghash/core/wallet_service.py`: MBlock 클라이언트를 감싸 지갑 생성, 잔액 조회, 전송, Transit 요청을 수행하며, Repository에 결과를 저장.
- `src/aeghash/core/mining_service.py`: HashDam 클라이언트를 감싸 해시 잔액 조회와 출금 요청을 처리하며, Repository에 잔액 및 출금 로그를 저장.
- 단위 테스트: `tests/unit/core/test_wallet_service.py`, `tests/unit/core/test_mining_service.py`.
- 인프라 구현: `src/aeghash/infrastructure/repositories.py`에 SQLAlchemy 기반 저장소(`SqlAlchemyWalletRepository`, `SqlAlchemyMiningRepository`) 및 모델 정의.
- 보조 유틸: `src/aeghash/infrastructure/database.py` (엔진/세션 헬퍼), `src/aeghash/utils/memory_repositories.py` (인메모리 저장소).
- 세션 관리: `src/aeghash/infrastructure/session.py`의 `SessionManager`로 요청 단위 트랜잭션 제어.

## 3. Repository 구현 방향
- WalletRepository
  - `save_wallet`: 지갑 생성 시 사용자와 연결된 주소/Wallet Key 저장.
  - `log_transaction`: 전송/Transit 요청 기록 (상태 `submitted`, `pending-transit`, 향후 승인 결과 업데이트).
- MiningRepository
  - `upsert_balance`: HashDam 잔액 데이터를 사용자별로 갱신(ETL 스케줄러 또는 온디맨드 호출).
  - `log_withdrawal`: 출금 요청 기록 및 후속 정산/출금 워크플로와 연결.

※ 실제 구현 시 SQLAlchemy/Prisma 등 ORM 또는 DB 쿼리 계층에서 위 프로토콜을 구현한다.

## 4. 통합 테스트 계획
- Wallet 서비스
  - MBlock MockTransport + InMemory Repository 기반 통합 테스트 추가 (`tests/integration/test_wallet_flow.py`).
  - 전송/Transit 실패 시 에러 핸들링과 상태 업데이트 검증 계획 유지.
- Wallet 인프라
  - SQLAlchemy 저장소 통합 테스트 (`tests/integration/test_sqlalchemy_repositories.py`)로 ORM 매핑 검증.
- 실패 시나리오
  - `tests/integration/test_wallet_flow.py::test_wallet_transfer_failure_logs_failure`에서 실패 로그 기록 확인.
- 재시도·알림 계획: `docs/planning/retry_notification_strategy.md` 참고.
- Mining 서비스
  - HashDam MockTransport + InMemory Repository 기반 통합 테스트 추가 (`tests/integration/test_mining_flow.py`).
  - 출금 큐 재시도 로직 연결 시 추가 시나리오 작성.
- Mining 인프라
  - SQLAlchemy 저장소 통합 테스트 (`tests/integration/test_sqlalchemy_repositories.py`)로 ORM 매핑 검증.
- 실패 시나리오
  - `tests/integration/test_mining_flow.py::test_mining_withdrawal_failure_logs_failure`에서 실패 로그 기록 확인.
- 재시도·알림 계획: `docs/planning/retry_notification_strategy.md` 참고.

## 5. 다음 단계
1. SessionManager를 앱 초기화 코드에 통합하고 서비스/배치 레이어에서 컨텍스트를 사용하도록 정비.
2. Alembic 마이그레이션을 초기화하고 `wallets`, `wallet_transactions`, `mining_balances`, `mining_withdrawals` 테이블을 생성.
3. 통합 테스트와 ETL 배치(채굴 데이터 수집, 출금 승인) 설계를 확장하고 재시도/알림 워크플로를 구현.
