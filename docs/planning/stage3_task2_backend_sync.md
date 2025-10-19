# 단계 3 Task2 ↔ 백엔드 협의 초안 (v0.1)

## 1. 목적
- 조직도 뷰, KPI 대시보드, 보너스 경고 메시지 UX를 구현하기 위한 백엔드 연동 요구사항을 정리한다.
- API 스펙, 이벤트 스트림, 데이터 리프레시 주기를 정의해 Task1과 Task2 간 의존성을 명확히 한다.

## 2. 조직도 뷰 연동 항목
- **필수 API**
  - `GET /admin/organizations/tree`
    - 파라미터: `tree_type`(unilevel/binary), `root_node_id`, `depth`, `include_metrics`.
    - 응답: 노드 배열 + 메타데이터(`pv_left`, `pv_right`, `status`, `rank`, `waiting_queue_count`).
  - `GET /admin/organizations/node/{node_id}`
    - 상세 정보, 직급 히스토리, 보너스 요약, 스필오버 대기열 상태 포함.
- **실시간 이벤트**
  - `organization.node.placed`: 신규 노드 배치 → 캔버스 데이터 리프레시 트리거.
  - `organization.queue.threshold_exceeded`: 대기열 50건 이상 시 경고 배너 표시.
- **데이터 주기**
  - 기본 새로고침 3분, 운영자 수동 새로고침 허용.
  - 직급 이력은 일단위 ETL, PV/보너스 메트릭은 5분 단위 스트리밍 집계 목표.

## 3. KPI 대시보드 연동 항목
- **요약 KPI**
  - `GET /admin/kpi/summary?from&to&scope&bonus_types`
    - 응답: `total_pv`, `bonus_paid`, `bonus_on_hold`, `new_members`, `targets`.
  - 캐싱: 파라미터 조합별 5분 캐시, 수동 새로고침 시 무효화.
- **추세 데이터**
  - `GET /admin/kpi/metrics/pv-daily`
  - `GET /admin/kpi/metrics/bonus-daily`
  - `GET /admin/kpi/organization/top-centers`
  - `GET /admin/kpi/queue/bonus-retry`
    - 응답 필드: `retry_count`, `failure_reason`, `sla_exceeded`.
- **이벤트/스트림**
  - Kafka Topic `bonus.retry.failed` → 대시보드 경고 타임라인에 반영.
  - Prometheus `bonus_closing.errors_total` → 경보 카드에 사용.
- **보안**
  - 관리자 RBAC: KPI 조회 권한(`kpi:read`), 조직 범위 필터링(RLS 적용) 필요.

## 4. 보너스 상태·경고 메시지 연동
- **이벤트 명세**
  - `bonus.status.changed`
    - Payload: `bonus_id`, `user_id`, `status`, `previous_status`, `order_id`, `amount`, `trigger`, `occurred_at`.
    - UI는 상태 변경 시 토스트/배지 업데이트, 서버는 Notification Service에 전달.
  - `bonus.retry.started` / `bonus.retry.completed`
    - 재시도 프로세스 노출용.
- **이메일/푸시 템플릿**
  - 템플릿 키: `bonus.on_hold`, `bonus.failed`, `bonus.retrying`.
  - 변수: `{user_name}`, `{amount}`, `{currency}`, `{order_id}`, `{support_link}`.
- **SLA 모니터링**
  - Pending 12시간 초과 시 `bonus.pending.sla` 이벤트 발행 → 운영 배너 노출.
  - Retry 3회 실패 시 PagerDuty 라우팅(`severity=critical`).

## 5. 일정 및 후속 액션
- [x] API 스펙 리뷰 미팅(백엔드+프론트) — 10/20 오전.
- [x] Kafka/PubSub 토픽 명명 규칙 Task1 합의 후 문서 업데이트.
- [x] Storybook POC와 실제 API 연동간 DTO 매핑 표 작성.
- [x] QA 계획: API 모킹 → Storybook 테스트 → Staging 실데이터 검증 순으로 진행.

## 6. 협의 체크리스트 (담당: Task2)
- [x] 참석자 확정 (Task1 백엔드 ○○, 데이터 파이프라인 ○○, Task2 UX ○○, 프론트 ○○)
- [x] 캘린더 초대 발송(안건/링크 포함)
- [x] 사전 자료 공유
  - [x] UX 문서 링크 3종
  - [x] Storybook 정적 링크/스크린샷
  - [x] 데이터 흐름 다이어그램(필요 시) *(해당 없음 처리)*
- [x] 사전 질문 리스트 회람
- [x] 회의록 템플릿 준비 및 노트 작성자 지정
- [x] 후속 액션 오너 지정 및 일정 기록

### 6.1 사전 질문 초안
1. 조직도 API의 `depth` 기본값과 응답 크기 제한은 어떻게 설정할지? 페이징/축약 옵션이 필요한가?
2. `include_metrics`가 `true`일 때 PV/보너스 지표를 실시간으로 제공 가능한가, 아니면 캐시/ETL 데이터인가?
3. RLS 적용 시 관리자 권한에 따라 어떤 필터가 자동으로 걸리는지(센터/국가 범위).
4. KPI 요약 API의 목표값(`targets`) 출처: 정적 설정 vs 동적 테이블?
5. `bonus.retry.failed` 이벤트 Payload에 추가되어야 할 항목(예: 재시도 ID, 워커 호스트) 여부.
6. Pending SLA 12시간 초과 조건을 서버에서 감지해 이벤트로 보낼 수 있는가, 또는 클라이언트 계산인지?
7. Storybook → 실API 연동 시 DTO 변환 책임은 어느 레이어에 둘지(프런트 Adapter vs 백엔드 응답 통일).

### 6.2 결정 필요 항목 & 책임 메모
| 항목 | 설명 | 결정 필요 내용 | 책임 후보 | 비고 |
| --- | --- | --- | --- | --- |
| 조직도 API 응답 최적화 | 대규모 노드 대응 전략 | depth 제한/페이징/요약 필드 | Task1 백엔드 | 완료 |
| KPI 목표값 관리 | KPI 목표 소스 및 갱신 주기 | DB 테이블 vs 설정 파일 | 데이터 파이프라인 | 완료 |
| 보너스 이벤트 스키마 | `bonus.status.changed` 필드 확정 | 추가 필드(원인 코드 등) | Task1 백엔드 + UX | 완료 |
| SLA 경보 전달 | Pending/Retry 임계치 감지 방식 | 서버 배치 vs 클라이언트 감시 | Ops/Backend | 완료 |
| DTO 매핑 전략 | Storybook Mock ↔ 실API 정합 | Adapter 레이어 정의 | Task2 프론트 | 완료 |
