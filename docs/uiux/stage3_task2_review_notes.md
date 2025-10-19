# 단계 3 Task2 산출물 리뷰 노트 (v0.1)

## 1. 개요
- 신규 문서
  - `docs/uiux/organization_tree_ui.md`: 조직도 캔버스/정보 패널 UX 가이드.
  - `docs/uiux/kpi_dashboard_design.md`: KPI 대시보드 메트릭·위젯 설계.
  - `docs/uiux/bonus_status_messaging.md`: 보너스 상태·경고 메시지 톤앤매너.
- 스토리북 자산
  - `OrganizationTreeCanvas` 컴포넌트 + 데모 스토리(`Admin/Organization`).
  - `KpiSummaryCard` 컴포넌트 + 상태별 스토리(`Admin/KPI`).
  - `BonusStatusBadge`, `BonusAlertBanner` 컴포넌트 + 경고 사례 스토리(`Admin/Bonus`).

## 2. 검토 요청 항목
- **조직도 뷰 UX**
  - 캔버스 구조(3분할)와 미니맵/줌 인터랙션이 운영 필요에 부합하는지 확인.
  - 대기열 경고 배너 임계값(50건)과 상태바 표기 방식 의견 수렴.
  - 모바일 fallback(리스트 뷰) UX 추가 개선 요구사항 여부.
- **KPI 대시보드**
  - KPI 카드 4종 및 차트 구성이 주요 모니터링 항목을 커버하는지.
  - 자동 새로고침 주기(기본 5분) 합리성 검토.
  - API 엔드포인트 파라미터 설계에 누락된 지표 여부.
- **보너스 경고 메시지**
  - 상태별 카피·톤앤매너가 CS/운영 팀 커뮤니케이션 가이드와 일치하는지.
  - Critical/Warning 우선순위 정책 및 배너/토스트 노출 규칙 검증.
  - 이메일/푸시 메시지 템플릿에 추가 필드 요구사항(예: 티켓 링크) 확인.

## 3. 다음 단계 제안
1. Figma 파일(`Admin/OrganizationTree`, `Admin/KPI`, `Admin/Bonus`)에 동일 스펙 반영 후 디자이너/PO 리뷰.
2. 프론트엔드: Storybook 브랜치 생성 → QA와 함께 접근성/반응형 확인.
3. 백엔드/데이터 파이프라인: KPI API·보너스 이벤트 정의 워크숍 진행(본 문서 9절 참조).

## 5. 2025-10-17 진행 업데이트
- 관리자(Admin) 레이아웃: `Admin/Layout` Figma 페이지 코멘트를 전수 확인하고 사이드바 그룹핑, 테이블 필터 배치, 모달 푸터 버튼 정렬 이슈를 체크리스트에 기록.
- 테이블 UX: Sticky header, zebra row 옵션, 필터 Collapse 임계값(3개) 동작을 확인하고 Storybook 스펙에 반영 예정.
- 후속 작업: 이슈 목록은 Task2 QA와 공유해 Storybook 테이블 컴포넌트 설계 초안으로 연결, Task1에는 필터 API 파라미터 검토 요청 예정.

## 4. 피드백 로그 템플릿
| 구분 | 담당자 | 피드백 요약 | 조치 항목 | 상태 | 비고 |
| --- | --- | --- | --- | --- | --- |
| Figma(조직도) |  | 추가 피드백 없음 | 문서 유지 | 완료 |  |
| Figma(KPI) |  | 추가 피드백 없음 | 문서 유지 | 완료 |  |
| Figma(보너스 메시지) |  | 추가 피드백 없음 | 문서 유지 | 완료 |  |
| Storybook QA |  | 확인 완료 | 추가 조치 없음 | 완료 | 정적 빌드(`storybook-static`) QA팀 전달 완료 |
| 백엔드 회신 |  | 협의 완료, 조치 사항 없음 | 문서 유지 | 완료 |  |
