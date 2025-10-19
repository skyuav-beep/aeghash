# 단계 3 Task2 ↔ Task1 협업 미팅 요청 메시지 초안

안녕하세요, 조직·보너스 엔진 연동 관련해 Task2에서 준비한 UX 스펙을 공유드리며 API/이벤트 협의를 위한 미팅을 요청드립니다.

## 배경
- 조직도 뷰, KPI 대시보드, 보너스 상태 메시지 UX 문서를 단계 3 산출물로 작성했습니다.
- 해당 UX가 실서비스에서 동작하려면 실시간 조직 데이터, KPI 집계, 보너스 상태 이벤트가 필요합니다.
- 상세 요구사항은 `docs/planning/stage3_task2_backend_sync.md`에 정리했습니다.

## 미팅 제안
- **일시**: 10/20(월) 10:00 ~ 11:00 KST (유연 조정 가능)
- **참석자**: Task1 백엔드/데이터 파이프라인 담당, Task2 UX/프론트 대표
- **아젠다**
  1. 조직도 API (`GET /admin/organizations/tree`, `GET /admin/organizations/node/{id}`) 파라미터 검토 및 페이징/권한 정책 논의
  2. KPI 대시보드 API(요약/추세/대기열) 설계와 캐싱 전략 합의
  3. 보너스 상태 이벤트(`bonus.status.changed`, `bonus.retry.*`) 스키마 및 SLA 경보 연동
  4. 데이터 리프레시 주기, 알림 경보(Ops/Slack/PagerDuty) 흐름 정리
  5. 일정/테스트 계획: API Mock → Storybook 연동 → Staging 검증 플로우 확정

## 참고 자료
- UX 문서: `docs/uiux/organization_tree_ui.md`, `docs/uiux/kpi_dashboard_design.md`, `docs/uiux/bonus_status_messaging.md`
- 연동 요구사항 요약: `docs/planning/stage3_task2_backend_sync.md`
- Storybook 데모: `examples/frontend-storybook/storybook-static` (최신 빌드)

위 일정이 어렵다면 가능한 시간대를 회신 부탁드리며, 미팅 전까지 추가 요구사항이 있으면 알려주세요.

감사합니다.***

## 미팅 준비 체크리스트
- [ ] 참석자 확정 및 캘린더 초대 전송
- [ ] API 사전 질문 수집(`stage3_task2_backend_sync.md`에 업데이트)
- [ ] Storybook 데모 캡처/링크 공유
- [ ] 예상 결정 사항과 책임자 지정(문서에 기록)

## 진행 현황 메모
- 제안 메시지 전달 완료(10/16). 회신 대기 중.
