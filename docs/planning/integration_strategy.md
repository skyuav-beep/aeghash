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

## 6. MBlock API 비밀 관리 정책
- **보관 매체**: 운영 환경의 `MBLOCK_API_KEY`와 관련 파라미터는 AWS Secrets Manager(또는 동등한 KMS 지원 비밀 저장소)에 저장한다. 애플리케이션 인스턴스는 부팅 시 IAM 역할을 통해 비밀을 읽고 환경 변수로 주입한다.
- **주입 방식**: 컨테이너/프로세스는 런타임 전에 시크릿을 환경 변수(`MBLOCK_API_BASE_URL`, `MBLOCK_API_KEY`, `MBLOCK_TRANSIT_FEE` 등)로 노출한다. `.env` 파일은 로컬 개발 전용이며 실제 값은 저장소에 커밋하지 않는다.
- **권한 제어**: 운영 IAM 역할은 최소 권한으로 Secrets Manager에 읽기 전용 접근만 허용한다. 개발/QA 환경은 별도의 시크릿으로 분리하고 접근 로그를 CloudTrail로 수집한다.
- **회전 정책**: 키는 90일 주기로 회전하며, 새로운 키는 시크릿 버전업 → 배포 파이프라인 업데이트 → 구 키 폐기 순으로 적용한다. 회전 후에는 실패 요청을 모니터링하고 롤백 체크리스트(링크: `docs/planning/retry_notification_strategy.md`)에 따라 대응한다.
- **감사 및 변경 관리**: 시크릿 수정은 PR 기반 변경 기록과 Slack 알림으로 공지한다. 운영 관리자 2인 승인을 거친 뒤 변경하며, 변경 이력은 `docs/planning/auth_operations_playbook.md`에 업데이트를 남긴다.
- **현장 대응**: 키 유출 징후가 감지되면 즉시 Secrets Manager 버전을 폐기, 애플리케이션 재시작, `Retry Notification` 워크플로로 전송 실패 트랜잭션을 확인한다.

## 7. HashDam & AEGMALL API 키/인증 정책
- **HashDam 인증 흐름**: 테스트 환경에서는 키 없이 호출 가능하지만, 운영 전용 `HASHDAM_API_KEY`가 발급되는 즉시 AWS Secrets Manager에 저장하고 채굴 서비스 IAM 역할만 읽을 수 있도록 제한한다. 애플리케이션 기동 시 키가 없으면 즉시 실패하도록 부팅 체크를 추가한다. API 호출은 모두 `POST https://api.pool.hashdam.com/v1`에 `{"method": "hashBalance", ...}` 형식의 JSON을 전송하고, `Content-Type: application/json`, `X-HASHDAM-Key` 헤더를 포함한다.
- **IP 화이트리스트**: HashDam은 API Key 단위로 원격 IP를 제한하므로 `HASHDAM_IP_ALLOWLIST` 시크릿에 허용 IP를 관리한다. NAT 게이트웨이 변경 시 HashDam과 즉시 공유하고, 변경 이력을 `docs/planning/auth_operations_playbook.md`에 기록한다.
- **AEGMALL 파트너 키**: 파트너별 `X-AEG-Key`, `X-AEG-Secret`를 발급해 `AEGMALL_<PARTNER>_KEY/SECRET` 네이밍 규칙으로 Secrets Manager에 저장한다. 60일 주기로 회전하고, 회전 후에는 새 키로 서명된 테스트 호출을 실행해 성공 여부를 확인한다.
- **Idempotency-Key 관리**: AEGMALL Inbound API는 `Idempotency-Key` 헤더를 필수로 요구한다. 동일 키로 서로 다른 페이로드를 전송할 경우 409를 반환하고 `idempotency_keys` 테이블에 `FAILED_CONFLICT` 상태로 기록한다. 기본 TTL은 24시간이며, 만료 후에만 같은 키를 재사용한다.
- **HashDam 재시도 전략**: `HashDamClient`는 HTTP 오류·타임아웃·`code != 0` 응답을 즉시 예외로 전달하고, `MiningService`가 `RetryConfig`(기본 3회, 지수 백오프)를 적용해 재시도한다. 최종 실패 시 `WithdrawalRecord.status=failed`로 기록하고 `Notifier`를 통해 경고를 발송한다.
- **AEGMALL 재시도 전략**: 주문 파이프라인은 `RetryConfig` 기반 백오프를 적용해 일시적 오류 발생 시 최대 3회 재시도한다. 반복 실패 시 `idempotency_keys.status=FAILED`로 남기고, 후속 재시도 시 동일 키로 다시 시도하도록 안내한다.
- **알림 채널**: `ALERT_WEBHOOK_URL` 환경 변수를 정의하면 `WebhookNotifier`가 HashDam/Wallet 장애를 즉시 Slack 등 외부 채널로 전송한다. 설정되지 않은 경우에는 알림이 비활성화되므로 운영 환경에서는 필수로 지정한다.
- **2인 승인 정책**: `WithdrawalWorkflowService`는 `two_step_required=True` 구성 시 1차 승인(`approved_pending`) → 2차 승인(`approved`) 흐름을 강제한다. 1차 승인자는 감사 로그에 `approved_stage1`로 기록되며, 2차 승인자가 HashDam 호출을 실행한다. 동일 인물이 두 번 승인하려 하면 `409 Conflict`가 반환되고, HashDam 실패 시 상태가 `failed`로 롤백된다.
- **로깅 및 감사**: 시크릿의 평문 값은 출력하지 않고 키 식별자·회전 일시만 감사 로그에 남긴다. Secrets Manager 변경 이벤트는 EventBridge → Slack #platform-security 로 전달해 실시간 알림을 제공한다.
- **운영 승인**: 키 발급·회전은 보안/운영 2인 승인 후 진행하며, 파트너 전달 시 암호화 채널(사내 Vault, Keybase 등)을 이용한다. 회전 계획과 검증 결과를 릴리즈 노트에 기록한다.

## 8. 출금 위험 탐지 & 경보
- `RiskService`(`src/aeghash/security/risk.py`)는 한도 초과, 차단 IP, 신규 디바이스를 규칙으로 평가해 `risk_events` 테이블과 노티파이어(예: Slack Webhook)에 결과를 남긴다.
- `WithdrawalWorkflowService`는 위험 차단 시 자동으로 출금을 취소하고 `withdrawal_audit_logs`에 `cancelled` 기록과 사유를 저장한다. 리뷰 등급(`severity=review`)의 경우 감사 로그에 `flagged` 항목을 추가해 운영 콘솔에서 확인할 수 있다.
- SQLAlchemy 저장소(`SqlAlchemyRiskRepository`)와 인메모리 대역이 제공되며, 디바이스 정보는 `risk_known_devices` 테이블에 upsert되어 반복적인 디바이스 검증에 활용된다.

## 9. 조직·보너스 엔진
- `OrganizationService`(`src/aeghash/core/organization.py`)가 유니레벨/바이너리 트리를 관리하며, binary 트리는 BFS 기반 spillover로 좌/우 자리를 채운 뒤 `organization_spillovers` 로그에 감사 내역을 남긴다.
- `BonusService`(`src/aeghash/core/bonus.py`)는 구성원의 `path`를 활용해 상위 레벨에 추천/후원 등 보너스를 분배하고 `bonus_entries` 테이블에 `pending` 상태로 기록한다. 보너스 규칙은 `BonusRule`로 정의하며 레벨별 퍼센티지를 설정할 수 있다.
- SQLAlchemy 인프라(`SqlAlchemyOrganizationRepository`, `SqlAlchemyBonusRepository`)와 InMemory 구현이 모두 제공되어, 테스트와 실제 배치 파이프라인에 동일한 인터페이스를 사용할 수 있다.
