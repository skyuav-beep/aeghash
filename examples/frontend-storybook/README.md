# Storybook + Chromatic + Playwright 데모

토큰 기반 UI 컴포넌트를 스토리북/Chromatic/Playwright 파이프라인에 연결하는 샘플 프로젝트입니다.

## 사용법
```bash
pnpm install
pnpm run tokens:sync           # 루트 토큰을 CSS/Tailwind 산출물로 변환
pnpm run storybook             # http://localhost:6006
```

### Chromatic 업로드
```bash
CHROMATIC_PROJECT_TOKEN=<token> pnpm run chromatic
```

### Playwright 비주얼 테스트
```bash
pnpm run storybook &           # 별도 터미널에서 실행
pnpm run test:visual
```

### 접근성 테스트
```bash
pnpm run test:a11y
```

테스트/빌드 전에는 항상 `pnpm run tokens:sync`로 토큰을 최신 상태로 동기화해야 합니다.
