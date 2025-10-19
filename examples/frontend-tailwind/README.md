# Tailwind + AEG Hash 디자인 토큰 데모

이 예시는 `tokens/dist` 산출물을 Tailwind 테마에 연결하는 방법을 보여줍니다.

## 준비
```bash
pnpm install        # 또는 npm install
pnpm run tokens:sync  # 루트 토큰을 최신 상태로 변환
```

## 빌드
```bash
pnpm run build:css
```
`dist/output.css`가 생성되며, CSS 변수와 Tailwind 확장을 통해 토큰 값이 적용됩니다.

## 개발 모드
```bash
pnpm run dev
```
토큰 JSON이 변경될 때마다 `pnpm run tokens:sync`를 다시 실행해 `tokens/dist`를 갱신하세요.
