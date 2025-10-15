# 조직·보너스 엔진 설계 초안 (v0.1)

## 1. 범위와 목표
- 유니레벨/바이너리 조직 트리 데이터를 일관되게 저장하고 조회한다.
- 신규 가입 시 바이너리 스필오버 규칙을 적용해 좌·우 라인을 자동 배치한다.
- 보너스 배치 파이프라인이 주문(PAID) 이벤트를 입력으로 받아 각 보너스 항목을 계산하고 지갑/원장에 기록하도록 설계한다.
- 단계 3(Task1) 체크리스트: `조직도 스키마`, `스필오버 알고리즘`, `보너스 배치 파이프라인`을 문서화한다.

## 2. 데이터 모델 제안

### 2.1 공통 테이블
| 테이블 | 설명 | 주요 컬럼 |
| --- | --- | --- |
| `organization_nodes` | 모든 조직 트리 노드를 보관 | `node_id`(PK), `user_id`, `tree_type`(`UNILEVEL`,`BINARY`), `parent_node_id`, `position`, `rank`, `center_id`, `created_at`, `updated_at` |
| `organization_closure` | 트리 경로 조회용 클로저 테이블 | `ancestor_id`, `descendant_id`, `tree_type`, `depth` |
| `organization_metrics_daily` | 일별 누적 PV/매출 지표 | `node_id`, `tree_type`, `metric_date`, `volume_left`, `volume_right`, `personal_volume`, `group_volume`, `orders_count` |
| `organization_rank_history` | 직급 변동 기록 | `node_id`, `rank`, `effective_date`, `source` |

### 2.2 바이너리 보조 테이블
| 테이블 | 설명 | 주요 컬럼 |
| --- | --- | --- |
| `binary_slots` | 노드별 좌/우 슬롯 상태 | `node_id`, `slot`(`LEFT`,`RIGHT`), `status`(`FILLED`,`OPEN`), `child_node_id`, `last_assigned_at` |
| `binary_waiting_queue` | 스필오버 후보(대기열) | `sponsor_node_id`, `candidate_user_id`, `preferred_slot`, `enqueued_at`, `status`(`PENDING`,`PLACED`,`FAILED`) |

### 2.3 보너스/원장 테이블
| 테이블 | 설명 | 주요 컬럼 |
| --- | --- | --- |
| `bonus_transactions` | 보너스 적립 원장(Pending/Confirmed) | `bonus_id`, `user_id`, `bonus_type`, `order_id`, `pv_amount`, `bonus_amount`, `status`, `hold_until`, `created_at`, `confirmed_at` |
| `bonus_daily_closing` | 마감 배치 결과 | `closing_id`, `closing_date`, `status`, `started_at`, `completed_at`, `summary_json` |
| `bonus_retry_queue` | 실패 주문/보너스 재시도 | `queue_id`, `order_id`, `bonus_type`, `failure_reason`, `retry_after`, `retry_count`, `status` |

> `organization_closure`는 유니레벨/바이너리 모두에 사용하며, 바이너리 스필오버 배치 후 즉시 경로 레코드를 생성해 다단계 조회를 빠르게 한다.

## 3. 스필오버 알고리즘 설계

### 3.1 입력/출력
- 입력: `sponsor_user_id`, `binary_tree_id`, `new_user_id`, `preferred_slot(optional)`
- 출력: 배치된 부모 노드(`parent_node_id`), 슬롯(`LEFT` or `RIGHT`)

### 3.2 단계별 로직
1. **스폰서 노드 확보**  
   - `organization_nodes`에서 `tree_type=BINARY`인 스폰서 노드를 찾는다. 없으면 루트 노드 생성.
2. **슬롯 선점 처리**  
   - 트랜잭션 시작 후 `SELECT ... FOR UPDATE`로 스폰서 노드의 `binary_slots` 두 행을 잠근다.
3. **직접 배치 가능 여부**  
   - `preferred_slot`이 비어 있으면 즉시 배치.
   - 두 슬롯 모두 채워져 있으면 스필오버 탐색으로 이동.
4. **스필오버 탐색**  
   - BFS 큐를 사용해 레벨 순서(좌→우)로 빈 슬롯을 탐색한다.  
   - 구현 시 `binary_slots`에서 `status='OPEN'`인 자식 노드를 레벨별로 조회 (`depth`는 `organization_closure` 이용) 후 가장 먼저 발견한 슬롯을 선택한다.
5. **경쟁 조건 처리**  
   - 선택된 슬롯을 다시 `SELECT ... FOR UPDATE` 후 `status='FILLED'`, `child_node_id=new_node_id`로 업데이트.
   - 실패 시(다른 트랜잭션이 선점) 4단계로 되돌아간다.
6. **노드 생성 & 클로저 갱신**  
   - `organization_nodes`에 신규 노드 삽입(`parent_node_id`, `position`, `tree_type` 저장).
   - `organization_closure`에 `(ancestor,parent)`, `(parent,child)`, `(ancestor,child)` 조합을 삽입.
7. **대기열 처리**  
   - 배치가 완료되면 `binary_waiting_queue` 항목을 `PLACED`로 마크하고 이벤트를 발행(`organization.node.placed`).

### 3.3 의사코드
```
function place_binary_member(sponsor_id, new_user_id, preferred_slot=None):
    with transaction():
        sponsor_node = get_binary_node_for_update(sponsor_id)
        slot = find_direct_slot(sponsor_node, preferred_slot)
        if slot is None:
            slot = bfs_find_open_slot(sponsor_node)
        if slot is None:
            enqueue_waiting(sponsor_id, new_user_id)
            raise SpilloverQueueFull()
        child_node = insert_node(parent_id=slot.node_id, position=slot.slot, user_id=new_user_id)
        mark_slot_filled(slot, child_node.node_id)
        update_closure(parent=slot.node_id, child=child_node.node_id)
        return child_node
```

### 3.4 실패/재시도 정책
- 배치 도중 DB Deadlock 또는 슬롯 충돌 발생 시 트랜잭션을 롤백하고 `binary_waiting_queue`에 재시도 항목을 남긴다.
- 큐는 분당 N건(기본 100)씩 워커가 처리하며, 실패 5회 이상 시 `FAILED` 상태로 두고 운영자 알림을 발송한다.

## 4. 보너스 배치 파이프라인 개요

- **입력 이벤트**: 주문 서비스에서 `order.paid` 이벤트 발행 (`order_id`, `user_id`, `pv_amount`, `total_amount`, `line_items` 포함).
- **파이프라인 구성**
  1. **이벤트 수집 레이어**  
     - Kafka 토픽 `orders.paid` 또는 SQS 큐를 소비하는 배치 워커.
  2. **PV/매출 적재**  
     - `organization_metrics_daily`에 개인/그룹 PV 업데이트.  
     - Binary 좌/우 매출은 `organization_closure`를 통해 조상 노드 목록을 구해 좌/우 컬럼에 가산.
  3. **보너스 계산기**  
     - 보너스 유형별 규칙(추천·후원·공유·센터·센터추천)을 모듈화.  
     - 각 계산 결과를 `bonus_transactions`에 `status='PENDING'`으로 삽입.
  4. **포인트/지갑 적립**  
     - `bonus_transactions`를 읽어 `PointWalletService.credit()` 호출, `hold=True`로 대기금액 적립.  
     - 실패 시 `bonus_retry_queue`에 정보 저장.
  5. **마감 배치(Closing)**  
     - 설정된 마감 스케줄에 따라 `bonus_transactions`의 `status='PENDING'`을 `CONFIRMED`로 전환하고 보류금을 해제.  
     - 마감 결과를 `bonus_daily_closing.summary_json`에 통계로 기록.

- **오류 처리**
  - 계산 단계 실패: `bonus_retry_queue`에 즉시 추가, 지연 후 재시도.  
  - 지갑 적립 실패: `RetryConfig`(백오프) 후 `_notifier`를 통해 운영 채널에 알림.

### 4.1 보너스 규칙 캡슐화
- **추천보너스**: 스폰서 유니레벨 경로 10레벨까지, 레벨별 퍼센트(1대 30%, 2~3대 5%, 4대 3%, 5대 2%, 6~10대 1%).  
  - 구현: `ReferralBonusCalculator` 모듈이 `organization_closure`를 기반으로 상위 10레벨을 조회하고, 퍼센티지 매핑 딕셔너리를 적용.
- **후원보너스**: 바이너리 트리 20레벨까지 각 1%. 스필오버 노드도 동일하게 가산.  
  - 구현: `BinaryBonusCalculator`가 `organization_closure`로 윗선 20레벨을 가져온 뒤 좌/우 메트릭을 갱신.
- **공유보너스**: 주문 건당 고정 퍼센트(명세 5%).  
  - 구현: 주문자에게 직접 지급, 조건 충족 시 `bonus_transactions` 한 건 생성.
- **센터/센터추천 보너스**: `organization_nodes.center_id`와 `center_referrer_id` 메타를 사용. 센터 존재 여부를 먼저 검증.
- 모든 계산기는 `BonusCalculator` 프로토콜을 구현하고 `calculate(order_context) -> list[BonusCredit]` 형태의 결과를 반환한다.

### 4.2 배치 파이프라인 타임라인
| 단계 | SLA | 비고 |
| --- | --- | --- |
| 이벤트 소비 | < 1분 | 주문 확정 후 1분 이내 PV 반영 |
| 보너스 계산 | < 5분 | 주문당 동기 계산, 장애 시 재시도 큐 이동 |
| 마감 배치 | 일별/주별 | 환경설정 `closing.schedule`로 제어 |
| 보너스 확정 | 마감 후 즉시 | `hold` 해제 → 사용/출금 가능 |

### 4.3 모니터링 & 알림
- 메트릭
  - `bonus_calculator.duration_ms` (Prometheus Histogram)
  - `bonus_retry_queue.size`, `binary_waiting_queue.size`
  - 마감 배치 성공/실패 카운터(`closing.success_total`, `closing.failure_total`)
- 알림
  - 재시도 큐 3회 이상 실패 시 Slack/Webhook 알림(`Severity: warning`)
  - 마감 배치 실패 시 PagerDuty 에스컬레이션(`Severity: critical`)
  - 스필오버 큐 `FAILED` 전환 시 이메일 송신(운영/보안팀)
- 로그
  - 보너스 계산기는 `order_id`, `bonus_type`, `amount`, `calculator_version`를 구조화 로그로 남긴다.
  - 마감 배치는 `bonus_daily_closing.summary_json`에 `total_orders`, `total_amount`, `pending_count`, `retry_count` 포함.

## 5. 후속 작업 체크리스트
- [ ] 유니레벨/바이너리별 인덱스 설계 및 예상 쿼리 패턴 정리.
- [ ] 스필오버 BFS 탐색을 위한 SQL/Redis 캐시 비교 검토.
- [x] 보너스 규칙 모듈별 단위 테스트 시나리오 목록 작성.
- [ ] 마감 배치 스케줄링(Crontab/Airflow) 및 감사 로그 정책 정의.

## 6. 테스트 시나리오 초안

### 6.1 스필오버 배치
- **루트 초기화**: 스폰서 루트에 두 명 순차 추가 → 좌/우 슬롯 각각 할당 확인.
- **BFS 스필오버**: 이미 좌/우가 찬 스폰서에게 신규 사용자를 추가 → 트리 2레벨 왼쪽 자식에 배치되는지 검증.
- **경쟁 조건**: 두 스레드가 동시에 동일 슬롯 요청 → 하나만 성공, 다른 하나는 다음 슬롯 혹은 대기열로 이동.
- **대기열 재시도**: `binary_waiting_queue`에 들어간 항목이 워커 실행 후 `PLACED` 상태로 전환되는지 확인.

### 6.2 보너스 계산기
- **추천보너스**: 유니레벨 5레벨까지 노드를 생성 후 주문 발생 → 각 레벨 퍼센티지가 정확히 적용되는지 비교.
- **후원보너스**: 바이너리 좌/우 균형 상황과 편향 상황 각각에서 1%씩 20레벨 지급 여부 확인.
- **센터보너스**: `center_id`가 없는 주문 시 지급 제외, 존재 시 센터 사용자에게만 지급.
- **실패 처리**: 지갑 적립 단계에서 인위적 예외 발생 → `bonus_retry_queue`에 기록되고 Backoff 후 성공.

### 6.3 마감 배치
- **일별 마감**: `bonus_transactions` 10건 중 2건이 `PENDING` 상태 → 마감 실행 후 모두 `CONFIRMED` 전환 및 `summary_json` 통계 확인.
- **재시도 후 확정**: 마감 시점에 재시도 큐에 있는 주문이 제외되고, 다음 실행에서 포함되는지 검증.

## 6. 참고
- 명세서 `spec.md` 5장(보너스 구조), 12장(시나리오 C, G).
- 데이터 모델 초안 `docs/planning/api_data_model_outline.md` 2.6절.
- 위험/재시도 정책 `docs/planning/retry_notification_strategy.md` 연동.
