# AEG Hash UI/UX 정책 기반 작업 목록

## 개요
- 기반 문서: `aeg_hash_uiux_policy.md` (UI/UX & Color System Policy v1.1)
- 목적: 관리자/사용자 UI 가이드와 공통 디자인 시스템 요구사항을 실행 가능한 작업 단위로 구체화한다.

## 영역별 작업
- **디자인 토큰 정립**
  - `/tokens/colors.json`, `/tokens/typography.json`, `/tokens/components.json` 구조 정의 및 컬러/타이포/컴포넌트 변수 매핑.
  - Figma 라이브러리와 토큰 동기화, 명칭 컨벤션 확정.
- **공통 컴포넌트 라이브러리**
  - 버튼/입력/카드 상태별 스타일 시안과 코드 스펙 문서화.
  - 상태 관리(hover, focus, disabled) 가이드와 스토리북 예제 작성.
- **관리자(Admin) 전용 UI**
  - 좌측 사이드바, 상단 헤더, 본문 테이블 레이아웃 와이어프레임 설계.
  - DataTable, Pagination, FilterBox, Modal, Toast, Tooltip 컴포넌트 흐름 정의 및 접근성 확인.
- **사용자(WebApp) 플로우**
  - 모바일 우선 와이어플로(로그인→대시보드→보상/해시 조회) 및 단일 컬럼 레이아웃 가이드.
  - 하단 플로팅 내비게이션(≤5 버튼), 핵심 CTA 배치 원칙 수립.
- **모바일 전용 인터랙션**
  - Bottom Nav, Floating Button, Toast, Step Modal 마이크로인터랙션 프로토타입 작성.
  - 터치 영역(≥48px) 및 애니메이션(fade-in/out, bounce, scale) 모션 스펙 정의.
- **반응형 레이아웃 가이드**
  - Mobile(360~480px), Tablet(768px), Desktop(1280px+)별 레이아웃 및 타이포 스케일링 규칙.
  - 컴포넌트 재배치 룰과 브레이크포인트 전환 UX 점검 체크리스트.
- **접근성 & QA**
  - 명도 대비(≥4.5:1), 최소 폰트(≥12px), 키보드 탐색 가이드 포함한 접근성 체크리스트.
  - 디자인 QA 및 프론트엔드 회귀 테스트 프로세스 수립.
- **문서화 & 협업**
  - 관리자/사용자 공통 UI 키트 문서화, 릴리즈 노트 템플릿, 온보딩 자료 구성.
  - 버전 관리 정책(토큰/컴포넌트)과 검수 워크플로 정의.

## 의존 관계 및 우선순위
1. 디자인 토큰 구조 확립 후 공통 컴포넌트/레이아웃 작업 진행.
2. 관리자·사용자 플로우 와이어프레임 완성 이후 컴포넌트 상세 및 인터랙션 정의.
3. 반응형/접근성 가이드 정착과 동시에 QA 프로세스 연결.

## 체크리스트
- [x] 토큰 JSON 스키마 및 명명 규칙 확정.
- [x] 버튼/입력/카드 컴포넌트 스토리북 초안 배포.
- [x] 관리자 레이아웃 와이어프레임 및 테이블 UX 검토.
- [x] 사용자 모바일 플로우 와이어플로 및 하단 내비 구현 가이드.
- [x] 모바일 전용 인터랙션 모션 스펙 확정.
- [x] 브레이크포인트별 레이아웃/타이포 가이드 배포.
- [x] 접근성 체크리스트 및 QA 루틴 문서화.
- [x] 문서화·협업 운영 프로세스 정비 및 릴리즈 노트 템플릿 배포.

### 실행 계획 업데이트 (Task2)

| 항목 | 책임자 | 우선순위 | 일정 | 비고 |
| --- | --- | --- | --- | --- |
| 버튼/입력/카드 스토리북 초안 배포 | Task2 프론트엔드 엔지니어 | High | 금주 목요일까지 | 스토리북 브랜치 생성 후 QA 공유 |
| 관리자 레이아웃 와이어프레임 검토 | Task2 UX 리드 | High | 금주 수요일까지 | Figma `Admin/Layout` 페이지에 코멘트 반영 |
| 사용자 모바일 플로우 와이어플로 가이드 | Task2 UX 디자이너 | High | 금주 금요일까지 | 하단 내비 플로우 포함, 검토자 @Task1 PM 태그 |
| 모바일 전용 인터랙션 모션 스펙 | Task2 모션 디자이너 | Medium | 차주 화요일까지 | Lottie 프로토타입 초안 및 모션 파라미터 명시 |
| 브레이크포인트별 레이아웃/타이포 가이드 | Task2 프론트엔드 엔지니어 | Medium | 차주 목요일까지 | `docs/uiux/responsive_layout_guide.md` 초안 추가 |
| 접근성 체크리스트 및 QA 루틴 | Task2 QA · 접근성 챔피언 | Medium | 차주 금요일까지 | 체크리스트 베타 버전 + 자동화 테스트 제안 포함 |

### 진행 상황 로그

| 날짜 | 항목 | 상태 | 메모 |
| --- | --- | --- | --- |
| 2025-10-17 | 버튼/입력/카드 스토리북 초안 | 완료 | `docs/uiux/storybook_components_plan.md` / `examples/frontend-storybook/src/stories/admin/ui-kit/*` |
| 2025-10-17 | 관리자 레이아웃 와이어프레임 검토 | 완료 | 결과 `docs/uiux/stage3_task2_review_notes.md` 5절에 반영 |
| 2025-10-17 | 모바일 플로우 가이드 | 완료 | `docs/uiux/mobile_flow_wireguide.md` 작성 |
| 2025-10-17 | 모바일 전용 인터랙션 모션 스펙 | 완료 | `docs/uiux/mobile_motion_spec.md` 초안 작성 |
| 2025-10-17 | 브레이크포인트별 레이아웃/타이포 가이드 | 완료 | `docs/uiux/responsive_layout_guide.md` 초안 배포 |
| 2025-10-17 | 접근성 체크리스트 및 QA 루틴 | 완료 | `docs/uiux/accessibility_qa_checklist.md`, `tests/unit/ui/test_storybook_accessibility.py`, Playwright `admin_ui_kit_a11y.spec.ts` |

#### 2025-10-17 후속 실행 항목
- Storybook 구현 진행
  - [x] `stories/admin/ui-kit/Button.stories.tsx` 스캐폴드 생성 및 토큰 매핑 적용 (`docs/uiux/storybook_components_plan.md` 참조).
  - [x] Input/Card 스토리 구성, Controls 및 Docs 탭 토큰 표 연결.
  - [x] Chromatic baseline 및 Interaction 테스트 스크립트 작성. (Chromatic Build #1 — https://www.chromatic.com/build?appId=68f23a8de16c8ee30f00aafa&number=1)
- 테스트/QA
  - [x] 접근성 자동화(`poetry run pytest -m a11y`) 스위트 초안 작성, `docs/uiux/accessibility_qa_checklist.md` 기준 케이스 연결.
  - [x] Storybook Viewport/A11y 애드온 설정 검증.
- 문서 업데이트
  - [x] Storybook 구현 결과 링크를 본 진행 로그에 추가.
  - [x] QA 체크리스트에 Storybook/Chromatic 링크 삽입 후 배포 알림.
- CI 연동
  - [x] Chromatic GitHub Actions 워크플로 추가(`.github/workflows/chromatic.yml`, secret `CHROMATIC_PROJECT_TOKEN`)

#### 2025-10-17 High Priority 실행 순서
1. `버튼/입력/카드` 스토리북 초안
   - 토큰별 스타일 변형(Primary, Secondary, Error 등) 리스트업
   - 각 상태(hover, focus, disabled)별 인터랙션 메모 작성
   - Storybook 카테고리 구조 및 Controls 계획 수립
2. 관리자 레이아웃 와이어프레임 검토
   - 사이드바/헤더/본문 섹션별 Figma 코멘트 확인
   - 테이블 필터·모달 플로우 누락 사항 체크리스트에 기록
   - 검토 결과를 `stage3_task2_review_notes.md`에 요약 예정
3. 사용자 모바일 플로우 와이어플로 가이드
   - 하단 내비게이션 탭 흐름 및 화면 진입 조건 정리
   - CTA/토스트/모달 등 주요 인터랙션 노트 작성
   - QA/검토자 태깅을 위한 레퍼런스 링크 초안 마련

#### 2025-10-17 Medium Priority 실행 순서
1. 모바일 전용 인터랙션 모션 스펙
   - 주요 모션 시나리오(Bottom Nav, Floating Button, Toast, Step Modal)별 파라미터 요구사항 정리
   - `aeg_hash_uiux_policy.md`와 기존 토큰 모션 값 비교, 누락 토큰 식별
   - Lottie 프로토타입 초안 제작 범위 및 산출물 형식 확정
2. 브레이크포인트별 레이아웃/타이포 가이드
   - Breakpoint 별 화면 구성 사례 수집(모바일/태블릿/데스크톱)
   - KPI 카드/그래프 등 핵심 컴포넌트 재배치 규칙 초안화
   - 초안 문서를 `docs/uiux/responsive_layout_guide.md`에 정리할 섹션 구조 설계
3. 접근성 체크리스트 및 QA 루틴
   - 대비 측정, 포커스 이동, 스크린리더 시나리오 등 테스트 케이스 벤치마크 조사
   - Playwright/Storybook 접근성 애드온 등 자동화 도구 후보 비교표 작성
   - 체크리스트 템플릿 초안과 QA 주기(사전/사후) 정의
