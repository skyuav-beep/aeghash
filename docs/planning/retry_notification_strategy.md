
# 재시도 & 알림 워크플로 전략 (Codex Task1)

## 1. 대상 범위
- Wallet 전송/Transit 요청 실패 혹은 장기 지연 건.
- Mining 출금 요청 실패 및 HashDam에서 실패 메시지 수신.

## 2. 재시도 정책
- 1차 재시도: 즉시 1회 (네트워크 드롭 등 일시 오류).
- 2차 재시도: 지수 백오프 2^n 초로 최대 3회.
- 지속 실패 시 상태를 `failed` 계열로 기록하고 알림 시스템에 전달.
- 구현 후보
  - `tenacity` 라이브러리로 재시도 decorator 구성.
  - Celery/Async Queue를 활용한 비동기 재시도.

## 3. 알림 채널
- 내부 Slack/Discord Webhook
  - 메시지 내용: 사용자, 대상 지갑/출금, 최초 요청 시각, 실패 횟수, 에러 메시지.
- 관리자 콘솔 내 알림 큐
  - `failed` 상태 레코드를 표시하고 운영자가 수동 재시도 가능.

## 4. 데이터 모델 영향
- Wallet Transaction: `status` 값에 `retrying`, `failed`, `manual-review` 추가.
- Mining Withdrawal: 실패 시 `status=failed`, 재시도 중 `status=retrying`.
- Audit 로그: 재시도 횟수, 실패 원인 기록.

## 5. 테스트 전략
- 단위 테스트: 재시도 decorator 적용 함수에서 예외 발생 시 재시도 횟수와 상태 변화를 검증.
- 통합 테스트: Mock API가 일정 횟수 실패 후 성공하도록 설정하여 재시도 흐름 검증.
- 운영 검증: Staging 환경에서 의도적 실패를 트리거해 알림이 발송되고 상태가 업데이트되는지 확인.

## 6. 향후 작업
1. 재시도 데코레이터/헬퍼(`aeghash.utils.retry`) 추가.
2. Wallet/Mining 서비스에 재시도 로직 연결 및 상태 업데이트 반영.
3. 알림 연동 모듈 작성 (Webhook/Email 등)과 실패 로그 테이블 설계.
