# UI 시각 회귀 & 스토리북 파이프라인 가이드

## 1. 목표
- 디자인 토큰 변경 시 UI가 의도대로 반영되는지 자동으로 검증한다.
- Storybook을 단일 소스로 삼아 컴포넌트 상태, 접근성, 인터랙션을 문서화한다.
- CI 환경에서 스냅샷 비교 및 접근성 검사를 병행해 회귀를 방지한다.

## 2. 필수 도구 스택
- **Storybook 8.x (React/Next.js)** — UI 컴포넌트 카탈로그 및 Docs.
- **Chromatic 또는 Loki** — 브라우저 기반 스냅샷 비교. (Chromatic 권장)
- **@storybook/addon-a11y** — WCAG 대비 검사 수행.
- **Playwright** — 주요 사용자 플로우에 대한 E2E + 비주얼 테스트.
- **GitHub Actions** — CI 파이프라인 통합.

## 3. 프로젝트 구성 예시
```
apps/web/.storybook/
  main.ts         # 스토리북 빌드 설정
  preview.ts      # 토큰 CSS 임포트, 글로벌 데코레이터
apps/web/stories/
  Button.stories.tsx
  DashboardCard.stories.tsx
packages/ui/
  tokens/         # 이 레포의 tokens/dist 를 symlink or npm import
  components/
```
- `tokens/dist/design-tokens.css`는 Storybook `preview.ts`에서 `import "../tokens/dist/design-tokens.css";` 방식으로 주입한다.
- Tailwind 사용 시 `tailwind.config.js`에서 `require("../tokens/dist/tailwind.tokens.cjs")` 후 `theme.extend = tokens.theme.extend`.

## 4. Storybook 체크리스트
- 모든 공용 컴포넌트는 `Docs` 탭에 Props/Usage/Accessibility 섹션 포함.
- 기본/호버/포커스/비활성 상태를 스토리로 분리해 스냅샷 추적.
- `@storybook/testing-library`를 이용해 스토리 상호작용 테스트 작성.
- `preview.ts`에서 `document.documentElement`에 CSS 변수 파일을 적용해 테마 일관성 유지.

## 5. 비주얼 회귀 전략
- **Chromatic** 플로우
  1. Storybook 빌드 → Chromatic CLI 업로드 (`npx chromatic --project-token=<token>`).
  2. 토큰 변경 시 자동으로 델타 하이라이트 제공, UI 승인 워크플로 운영자 지정.
- **Playwright Visual** 플로우
  1. `packages/ui/tests/visual/*.spec.ts` 작성.
  2. `page.addStyleTag`로 `design-tokens.css` 로드 후 주요 화면 캡처.
  3. `expect(await page.screenshot()).toMatchSnapshot("dashboard.png");`

## 6. 접근성 & QA 자동화
- Storybook CI 단계: `npx storybook@latest test --watch=false --coverage`
- `addon-a11y` + `@storybook/test-runner` 조합으로 WCAG 대비 보고서 생성.
- Playwright: 키보드 내비게이션 시나리오(`Tab`, `Shift+Tab`, `Enter`)를 스크립트화.
- Lighthouse CI(선택): 핵심 페이지에 대한 성능·접근성 점수 트래킹.

## 7. GitHub Actions 워크플로 예시
```yaml
name: Frontend UI Checks

on:
  pull_request:
    paths:
      - "packages/ui/**"
      - "tokens/**"

jobs:
  storybook:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: corepack enable && pnpm install --frozen-lockfile
      - run: pnpm run tokens:sync   # scripts/export_design_tokens.py 호출 또는 패키지 배포
      - run: pnpm run storybook:build
      - run: npx chromatic --exit-zero-on-changes --project-token=${{ secrets.CHROMATIC_TOKEN }}

  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: corepack enable && pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps
      - run: pnpm run tokens:sync
      - run: pnpm run test:visual
```

## 8. 운영 및 승인 프로세스
- PR 라벨 `needs-ux-review` 부여 → Chromatic UI Diff 승인 시 제거.
- 토큰 변경 시 `Design QA Checklist`(컬러 대비, 포커스링, 다크모드 호환성 여부 등) 검토 후 머지.
- 릴리즈 노트에 스토리북 배포 링크/Chromatic 빌드 링크 첨부.

## 9. 향후 확장 포인트
- 디자인 토큰 패키지를 npm 레지스트리에 배포해 레포 간 버전 관리.
- Percy 또는 Applitools 통합으로 멀티 뷰포트 캡처 확대.
- 디자인/프런트 협업을 위해 Figma Tokens ↔ 코드 동기화 자동화 스크립트 추가.
