# 접근성 & QA 체크리스트 (v1.0)

## 1. 대비 & 색상
- 텍스트/아이콘 대비 4.5:1 이상 (`colors.palette.contrast_pairs` 참조).
- 버튼/링크 focus ring 색상 `colors.palette.focus` 적용 및 배경 대비 3:1 확보.
- 상태 배지/알림 배너 색상 3:1 대비 확인.

## 2. 키보드 탐색
- Tab 순서가 시각적 흐름과 일치.
- 모달/시트: 포커스 트랩, ESC로 닫기 가능.
- 사이드바/테이블: Arrow 키 + Space/Enter 동작 지원.

## 3. 스크린 리더
- 버튼/아이콘: `aria-label` 또는 `aria-labelledby` 제공.
- 입력 필드: Label/Helper/Error 텍스트가 `aria-describedby`로 연결.
- Toast/배너: `role="status"` 또는 `role="alert"` 정확히 지정.

## 4. 모션 & 애니메이션
- `prefers-reduced-motion` 감지 시 지속시간 0.12s 이하, 불필요 애니메이션 제거.
- Skeleton/Loading: 최소 0.4초, 최대 2초 사이, 무한 루프 허용.
- Swipe 제스처: 대체 버튼 제공.

## 5. Playwright / Storybook 자동화
- Playwright: contrast 체크(axe-core), 키보드 네비게이션, 포커스 링 검증.
- Storybook: A11y Addon, Interaction Test로 hover/focus 상태 캡처.
- CI: `poetry run pytest -m a11y` 시나리오 추가 예정.
- Playwright 시나리오: `examples/frontend-storybook/tests/visual/admin_ui_kit_a11y.spec.ts`
- GitHub Actions: `.github/workflows/chromatic.yml`에서 Chromatic 빌드를 자동 실행(Secrets: `CHROMATIC_PROJECT_TOKEN`)

## 6. QA 주기
- Pre-release: 스토리북 기준 컴포넌트 레벨 검증 → E2E 시나리오 실행.
- Post-release: 주요 플로우(로그인, 출금, 보상 확인) 월 1회 접근성 스팟 체크.
- 회귀 테스트: 디자인 토큰 변경 시 contrast/포커스 스냅샷 갱신.

## 7. 실행 이력
- 2025-02-18: Storybook Test Runner(`npx @storybook/test-runner --failOnConsole --coverage`) 실행. 결과 `MissingStoryAfterHmrError` 다수 → `src/stories/admin/ui-kit/Card.stories.tsx` 등 스토리 ID와 스냅샷 동기화 필요. 커버리지 리포트는 `examples/frontend-storybook/coverage/storybook/coverage-storybook.json`.
- 2025-02-18: KPI 대시보드 Figma Variants(Desktop/Tablet/Mobile) 대비·키보드 흐름 검수 완료. 결과 `PASS` (세부사항: `docs/uiux/operations_dashboard_ui_review.md` 3~4장).
- 2025-02-18: HTTP 서버 기반 정적 Storybook 접근성 검사 자동화 플로 리허설 완료(`http-server` + Test Runner). 추후 CI 통합 시 동일 셸 스크립트 사용 가능.

## 8. TODO
1. Storybook 스토리 ID 재검토 및 `playground`/`layouts` 변형 id 재생성.
2. `@storybook/test-runner` 커버리지 환경 설정(e.g. `babel-plugin-istanbul`) 추가.
3. QA 문서(Confluence) 업로드 및 CI 워크플로(`.github/workflows/uiux.yml`)에 접근성 태그 스위치 추가.

## 9. 참고 링크
- Storybook: `http://localhost:6006/?path=/docs/admin-ui-kit-button--playground`
- Playwright: `pnpm run test:visual -- admin_ui_kit_a11y.spec.ts`
- Chromatic: https://68f23a8de16c8ee30f00aafa-fhhqahgkvn.chromatic.com/
