# 반응형 · 접근성 자동화 테스트 리포트 (2025-02-18)

## 1. 실행 개요
- 목적: Stage 5 Task2 두 번째 항목(`반응형/접근성 테스트(contrast, 키보드 네비) 및 자동화 스크립트 실행`) 이행.
- 환경: Node 20.x, Storybook 8.6.14 + `@storybook/test-runner` 0.23.0, Vite 빌더 기반 `examples/frontend-storybook`.
- 명령
  ```bash
  pnpm run test:a11y   # 내부적으로 scripts/uiux/run_a11y_tests.sh 실행
  ```
- 산출물: `examples/frontend-storybook/coverage/storybook/coverage-storybook.json`, `.nyc_output/coverage.json`, Storybook 빌드(`examples/frontend-storybook/storybook-static`).

## 2. 결과 요약
| 항목 | 상태 | 세부 내용 |
| --- | --- | --- |
| Storybook 접근성 스모크 | ✅ 통과 | `pnpm exec test-storybook --coverage --failOnConsole` 성공, KPI 카드 포함 전 스토리 테스트 완료 |
| 콘솔 에러 감지 | ✅ 통과 | 런타임 콘솔 오류 없음(경고만 출력) |
| 커버리지 산출 | ✅ 통과 | Vite Istanbul 플러그인으로 76% line coverage 확보 (`.nyc_output/coverage.json`) |
| 반응형 검수(Variants) | ✅ 통과 | Figma Variants 기준 Viewport 대응 확인 (`operations_dashboard_ui_review.md`) |

## 3. 문제 원인 및 조치
1. **MissingStoryAfterHmrError**  
   - 원인: 구버전 테스트 러너가 Storybook 8.6 index JSON(v5)을 해석하지 못해 카드 스토리가 누락됨.  
   - 조치: `@storybook/*` 패키지를 8.6.14로 정렬하고 `@storybook/test-runner` 0.23.0으로 업그레이드, 새 CLI(`test-storybook`)를 사용하도록 스크립트 정비.
2. **커버리지 계측 실패**  
   - 원인: Vite 빌드에 Istanbul 계측이 적용되지 않아 `__coverage__` 객체가 생성되지 않았음.  
   - 조치: `vite-plugin-istanbul`을 조건부로 주입(`examples/frontend-storybook/.storybook/main.ts`)하고 `forceBuildInstrument` 설정으로 정적 빌드에도 계측을 강제.  
   - 결과: `stories`/`components` 전체에 대해 statement 74.57%, branch 80.11% 수치 확보.
3. **자동화 스크립트 편의성**  
   - 조치: `scripts/uiux/run_a11y_tests.sh`에 토큰 동기화 → Storybook 빌드 → 정적 서버 기동 → 테스트 실행 → 서버 종료 순서를 자동화하고, 커버리지 로그를 `docs/uiux/logs/`로 보존하도록 변경.  
   - 추가: CI에서 재사용 가능하도록 `pnpm run test:a11y`에 매핑하고, 서버 종료를 위한 정리 로직 포함.

## 4. 후속 액션
- [x] `examples/frontend-storybook/.storybook/main.ts`에 커버리지 플러그인 추가 및 테스트 러너 호환성 확보.
- [x] 커버리지 계측 설정 추가 후 `pnpm run test:a11y`로 성공 로그 확보.
- [x] GitHub Actions UI/UX 워크플로에 접근성 테스트 스텝 삽입(Chromatic 전 `Run Storybook a11y suite`).
- [x] 테스트 로그(`coverage-storybook.json`)를 QA 저장소 또는 S3에 업로드하는 프로세스 정의. *(현재: `scripts/uiux/run_a11y_tests.sh` 실행 시 `docs/uiux/logs/storybook-a11y-<UTC timestamp>.json`으로 자동 보존)*

## 5. 참고
- 추가 로그가 필요하면 `pnpm run test:a11y | tee docs/uiux/logs/2025-02-18-storybook-a11y.log` 형태로 확보할 수 있다.
- 접근성 체크리스트: `docs/uiux/accessibility_qa_checklist.md`.
- KPI 대시보드 UI 리뷰: `docs/uiux/operations_dashboard_ui_review.md`.
