# KPI 대시보드 시각화 컴포넌트 설계 (v0.1)

## 1. 목적
- 관리자(Admin) 대시보드에서 조직/보너스 성과를 직관적으로 파악할 수 있는 핵심 메트릭과 시각 요소를 정의한다.
- 데이터 소스(보너스 배치, PV 집계, 위험 알림)를 단일 뷰에서 연계해 운영 인사이트를 제공한다.
- 반응형·접근성 요구사항을 충족하는 컴포넌트 스펙을 문서화하여 프론트엔드 구현을 가이드한다.

## 2. 정보 구조
- **요약 KPI 카드 영역 (Row 1)**
  1. `총 매출 PV`
  2. `보너스 지급액`
  3. `보류 보너스`
  4. `신규 가입자`
- **추세 그래프 영역 (Row 2)**
  - `일별 PV 추세` (Area Chart)
  - `보너스 지급 vs 보류` (Stacked Bar)
- **조직 기여도 영역 (Row 3)**
  - `상위 5개 센터 기여도` (Horizontal Bar)
  - `스필오버 대기열 상태` (Donut + 리스트)
- **경보/위험 영역 (Row 4)**
  - `실패 재시도 큐` 테이블
  - `보너스 경보 타임라인`

## 3. KPI 카드 컴포넌트
- 크기: Desktop 기준 3열 그리드(최대 폭 1280px → 카드 폭 400px, 높이 140px).
- 구성
  - 상단 라벨(12px Medium, `colors.text.muted`)
  - 메인 수치(32px Bold, `typography.display.md`)
  - 증감 배지(아이콘 + 퍼센트, 상승 `colors.status.success`, 하락 `colors.status.danger`).
  - 하단 부가 정보(예: 전주 대비, 목표 대비).
- 상태
  - 로딩: Skeleton 3줄, 회색 블록.
  - 오류: 경고 아이콘 + "데이터를 불러오지 못했습니다" + `재시도`.
- 인터랙션: 클릭 시 상세 리포트 페이지 링크(예: 보너스 -> `/admin/bonus/report`).
- 접근성: 카드 전체 `role=button`, `aria-pressed` 미사용, 키보드 Space/Enter 활성.

## 4. 그래프 컴포넌트

### 4.1 일별 PV 추세 (Area Chart)
- 데이터: 지난 30일 PV, 주말 표시(점선).
- 시각 요소: Primary 색상(`colors.palette.primary`) 영역, 평균선 Secondary 색상.
- Hover 시 tooltip: 날짜, PV 값, 전일 대비 퍼센트.
- 상단 필터 드롭다운: 기간(7일/30일/90일) 변경.
- 오류/데이터 없음 시 빈 상태 메시지 + CTA.

### 4.2 보너스 지급 vs 보류 (Stacked Bar)
- 축: X=일자, Y=금액. 지급(Primary), 보류(Warning) 색상 매핑.
- KPI 목표선: 보너스 예산 대비 라인 표시, 초과 시 경고 배지 노출.
- Tooltip: 지급 금액, 보류 금액, 총합.
- 접근성: `aria-describedby`로 막대 설명, 키보드 화살표로 막대 이동.

### 4.3 상위 센터 기여도 (Horizontal Bar)
- Top 5 센터, 좌측에 센터명 + 직급, 우측 바 + 퍼센트.
- 바 색상: 센터별 구분 컬러 팔레트(`colors.data.categorical.*`).
- 클릭 시 해당 센터 조직도 뷰 딥링크.

### 4.4 스필오버 대기열 상태 (Donut + 리스트)
- 도넛 차트: `Pending / Processing / Failed` 비율.
- 중앙 KPI: 총 대기 인원 수 + SLA 초과 퍼센트.
- 하단 리스트: 상위 5 노드(대기 인원 내림차순).
- SLA 초과 시 리스트 행에 경고 아이콘 + Tooltips(정확한 대기 시간).

## 5. 필터 & 컨트롤
- 상단 글로벌 필터 바
  - 기간 선택(오늘/7일/30일/맞춤).
  - 조직 범위: 센터/국가/라인 선택.
  - 보너스 타입 토글(추천/후원/센터/공유/센터추천).
  - 데이터 리프레시 버튼(수동 새로고침).
- 필터 적용 시 모든 위젯 리패치, 적용된 필터는 헤더 Chip 표기.
- 자동 새로고침: 기본 5분, 오른쪽 상단에서 1분/5분/수동 선택.

## 6. 반응형 전략
- Desktop(≥1280px): 3열 레이아웃(카드), 2열 그래프.
- Tablet(768~1279px): KPI 카드 2열, 그래프 단일 컬럼. Donut/리스트는 탭 전환.
- Mobile(≤767px): KPI 카드 단일 컬럼, 그래프는 Sparkline 형태로 축소, 테이블은 요약 카드로 전환.
- 모바일에서 그래프 툴팁은 Bottom Sheet(스크롤 가능)로 노출.

## 7. 접근성 & QA
- 대비: KPI 카드 본문 대비 4.5:1 이상, 그래프 색상 WCAG 준수.
- 키보드 탐색: 글로벌 필터 → 카드 → 그래프 → 테이블 순서.
- 화면 리더: 각 위젯 `aria-label`과 데이터 요약 텍스트 제공(예: "지난 7일 PV 평균 12,500").
- QA 체크리스트
  1. 타임존 전환(UTC/KST) 시 날짜 축 오류 없는지 확인.
  2. 데이터 누락 시 빈 상태 표시 3종(카드/그래프/테이블) 검증.
  3. 자동 새로고침 off → 수동 새로고침 동작 검증.
  4. 보너스 타입 필터 변경 시 모든 컴포넌트가 최신 데이터로 갱신되는지 확인.

## 8. 토큰 매핑
- 카드 배경: `colors.surface.elevated`.
- 그림자: `shadow.card.md`.
- 그래프 Primary: `colors.palette.primary`, 보류: `colors.status.warning`, 실패: `colors.status.danger`.
- 타이포: 라벨 `typography.label.sm`, 수치 `typography.display.md`, 서브텍스트 `typography.body.sm`.
- 테이블 행 높이: 48px, 구분선 `colors.border.subtle`.

## 9. 데이터 연동 요구사항
- API 엔드포인트 제안
  - `GET /admin/kpi/summary?from=&to=&center_id=&bonus_types=`
  - `GET /admin/kpi/metrics/pv-daily`
  - `GET /admin/kpi/metrics/bonus-daily`
  - `GET /admin/kpi/organization/top-centers`
  - `GET /admin/kpi/queue/bonus-retry`
- 응답은 ISO8601 타임스탬프, 통화값은 소수점 2자리, PV는 정수.
- 프론트엔드 캐싱: 요청 파라미터별 5분 캐시, 새로고침 시 강제 무효화.

## 10. 후속 단계
- Figma 위젯 컴포넌트(`Admin/KPI/Card`, `Admin/KPI/Charts`) 업데이트 및 리뷰.
- 스토리북 스캘폴딩: `KpiSummaryCard`, `PvTrendChart`, `BonusStatusTable` Story 추가.
- 데이터 파이프라인팀과 KPI 정의(목표값, 집계 스케줄) 확정.
