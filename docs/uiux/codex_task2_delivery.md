# Codex Task2 산출물 요약

## 1. 목적 및 범위
- `aeg_hash_uiux_policy.md`의 컬러·타이포·컴포넌트 정책을 실행 가능한 토큰과 가이드로 구체화한다.
- 관리자(Admin)·사용자(WebApp) 인터페이스를 설계/구현할 때 필요한 핵심 UX 지침을 문서화한다.
- 접근성, QA, 협업 플로우를 명확히 정의하여 프론트엔드 팀 간 일관성을 확보한다.

## 2. 디자인 토큰 패키지
- 위치: `tokens/colors.json`, `tokens/typography.json`, `tokens/components.json`
- 형식: 메타데이터 + 실제 payload 구조. W3C Design Tokens 참고(간단 참조 경로 지원).
- 주요 정의
  - 컬러: Primary, Accent, Surface, Border, Focus, Error, Success 등 시맨틱 이름 제공.
  - 타이포: `title`, `subtitle`, `body_primary`, `data_table_*`, `button` 등 스케일 규칙 포함.
  - 컴포넌트: Button/Input/Card/Toast 기본 속성과 상태(hover, focus, pressed, disabled) 정의.
- 사용 방법
  - Python 모듈 `src/aeghash/utils/design_tokens.py`의 `load_bundle`, `get_token` 이용.
  - 예: `get_token("colors", "palette.primary.value")` → `#FDC915`.
  - 프런트엔드는 JSON 동기화 후 Style Dictionary 또는 Tailwind 설정으로 변환 가능.
- Figma ↔ Storybook 토큰 검사: `docs/uiux/figma_storybook_mapping.md`의 매핑 로그를 기준으로 상태별 값을 검증하고 Chromatic 결과를 첨부한다.

## 3. 관리자(Admin) 레이아웃 가이드
- 레이아웃 프레임
  - 좌측 고정 사이드바(폭 240px): 조직/정산/보너스/설정 메뉴 그룹화, 아이콘 + 라벨 조합.
  - 상단 헤더(높이 64px): 검색, 알림, 사용자 프로필, 환경 전환(Prod/Stage) 토글.
  - 본문: 12px/24px 그리드, 카드/테이블 혼합. 최대 폭 1280px, 필요 시 2열 카드.
- 핵심 컴포넌트 흐름
  - DataTable: sticky header, zebra row 옵션, hover 시 배경 `colors.palette.primary_light`.
  - FilterBox: 우측 상단 고정, 최소 3개 필터는 Collapse 처리, Reset/Apply 버튼 배치.
  - Modal: 헤더 + 본문 + 푸터 3분할, 최소 버튼 2개, 닫기 버튼 헤더 우측 배치.
  - Toast: 우상단 스택, 3초 후 자동 사라짐, 접근성을 위해 focusable close 버튼 제공.
- 상호작용
  - 행 선택: 체크박스 + 카드 테두리 Primary 색상.
  - 테이블 정렬: hover 시 caret 노출, active 상태는 Accent 색상.

## 4. 사용자(WebApp) 주요 플로우
- 핵심 여정: 로그인 → 대시보드 → 해시/보상 → 지갑/출금.
- 모바일 우선 단일 컬럼, 최대 폭 480px에서 카드/리스트 재배치.
- 하단 플로팅 내비(최대 5 버튼): 홈, 해시, 보상, 지갑, 마이.
- CTA 배치
  - 대시보드 상단 Primary 버튼(해시 구매), Secondary 버튼(추천 코드 공유).
  - 출금 요청은 Bottom Sheet 형태 Step Modal 3단계(요청 정보 → 보안 확인 → 완료).
- 상태 피드백
  - 실시간 보상 변동 시 Toast, 지갑 잔액 갱신은 subtle skeleton shimmer.
  - 오류 발생 시 Step Modal 내 Error state(에러 컬러, 안내 문구 + 재시도).
- 인증 플로우 상세(로그인/회원가입/비밀번호 재설정, Turnstile/2FA UX)는 `docs/uiux/authentication_ui_guide.md` 참고.

## 5. 모바일 전용 인터랙션
- Bottom Nav: 터치 영역 최소 56px, active 탭 Primary 색상, 아이콘 24px.
- Floating Button: 오른쪽 하단, 64px 원형, 그림자 `colors.elevation.shadow_medium`.
- Toast: 슬라이드 업 + 페이드, 3초 노출, 스와이프 다운으로 해제 가능.
- Step Modal: 각 단계마다 Header 타이틀 + 프로그레스 바(Primary), 기본 높이 60vh.
- 제스처: 풀다운 리프레시 지원, 해시 대시보드 카드 좌우 스와이프로 탭 전환.

## 6. 반응형 및 타이포 스케일링
- Breakpoints
  - Mobile ≤ 480px: 단일 컬럼, 카드는 전폭, 타이포 multiplier 1.0.
  - Tablet 481~1024px: 2열 카드, 사이드바 축소(아이콘 모드), multiplier 1.05.
  - Desktop ≥ 1025px: 12열 그리드, multiplier 1.15, 관리자 테이블 폭 고정.
- 전환 룰
  - 사이드바: Tablet에서는 collapsible, Desktop에서는 항상 확장.
  - KPI 카드: Mobile 1열, Tablet 2열, Desktop 3열.
  - 그래프: Mobile에서 스크롤 가능 영역 + legend collapse.
- 타이포 반응형: `typography.scale.*` 사용, multiplier 적용 후 14px 이하로 내려가지 않음.

## 7. 접근성 & QA 체크리스트
- 컬러 대비: Primary/Accent 대비 4.5:1 이상 확인(토큰에 명시된 대비 페어링 사용).
- 포커스 표시: `colors.palette.focus` 기반 2px 외곽선 + 4px spread shadow.
- 키보드 탐색: 사이드바, 테이블, 모달 모두 Tab 순서 정의, Escape로 모달 종료.
- 모션 제어: OS `prefers-reduced-motion` 감지 시 애니메이션 지속시간 0.1s 이하.
- 테스트 루틴
  - 컴포넌트 레벨 스토리북 접근성 애드온 실행.
  - E2E(Playwright) 시나리오: 로그인, 대시보드 카드 스크롤, 출금 플로우.
  - 회귀: 디자인 토큰 변경 시 시각 스냅샷 재생성 및 비교.

## 8. 협업 및 문서화 프로세스
- 토큰 변경은 PR에 `tokens/*.json` diff + 변경 의도 요약 필수.
- Figma ↔ 코드 동기화: 주 1회 스냅샷, 변경사항 Notion 로그 기록.
- 릴리즈 노트 템플릿(제안)
  1. 개요(변경 요약)
  2. 사용자 영향(페이지/기기)
  3. 토큰/컴포넌트 변경 리스트
  4. QA 결과 및 커버리지 링크
- UI 산출물 버전 관리 정책은 `docs/uiux/versioning_policy.md`를 따른다.
- 토큰/UX 변경 PR에는 `docs/uiux/pr_token_change_template.md` 체크리스트를 사용해 검증 링크를 제출한다.
- 온보딩: 신규 참여자에게 본 문서와 `aeg_hash_uiux_policy.md`, 토큰 JSON 패키지, 버전 관리 정책 문서를 전달.

## 9. 릴리즈 노트

### 2025-10-13 · 디자인 토큰 v1.1.0
- 비활성 상태 텍스트 컬러를 `text.disabled` 토큰(#AAAAAA)으로 정의하고 모든 컴포넌트 비활성 전경색에 적용.
- 버튼/입력 포커스 상태에 `0 0 0 4px rgba(253, 201, 21, 0.2)` 섀도 토큰을 추가해 접근성 포커스 링 강화.
- `tokens/dist/design-tokens.css`, `tokens/dist/tailwind.tokens.cjs` 재생성(`python3 scripts/export_design_tokens.py`).

### 2025-02-18 · Stage 5 Task2 마감
- `docs/uiux/operations_dashboard_ui_review.md`로 운영 KPI 대시보드 UI 검수 결과 정리.
- 접근성 자동화 스크립트 실행 및 실패 원인 분석(`docs/uiux/a11y_responsive_test_report.md`).
- 신규 온보딩/협업 가이드 배포: `docs/uiux/task2_onboarding_playbook.md`.
- 주의: Storybook 정적 빌드에 KPI 스토리가 누락되어 Test Runner가 실패 → `examples/frontend-storybook/.storybook/main.ts` 업데이트 필요.

## 10. 온보딩 & 협업 프로세스
- 빠른 참조: `docs/uiux/task2_onboarding_playbook.md`.
- 커뮤니케이션 템플릿: `docs/planning/task2_communication_templates.md`.
- 릴리즈/버전 정책: `docs/uiux/versioning_policy.md`.
