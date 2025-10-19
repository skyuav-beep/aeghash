# Figma ↔ Storybook 토큰 매핑 검증 로그

## 1. 개요
- 목적: 디자인 토큰(JSON)과 Figma 컴포넌트, Storybook 구현 사이의 명명 규칙과 속성이 일관한지 검증한다.
- 범위: 버튼, 입력, 카드를 포함한 공통 컴포넌트 및 토스트 UI. `tokens/*.json`과 `scripts/export_design_tokens.py`에서 생성되는 CSS/JS 산출물을 기준으로 한다.

## 2. 참조 스냅샷
- Figma 라이브러리: `AEG Hash DS` (`https://www.figma.com/file/<redacted>/AEG-Hash-DS?node-id=1021%3A2045`) — 2024-06-10 스냅샷
- Storybook 브랜치: `feat/ui-foundation` — 커밋 `4d2f1e6` (2024-06-11)
- 토큰 배포물: `tokens/dist/design-tokens.css`, `tokens/dist/tailwind.tokens.cjs`

> 위 스냅샷 식별자는 작업 로그 공유용으로 남겨두며, 민감 식별자는 실제 문서/PR에서만 공개한다.

## 3. 매핑 테이블
| Figma 컴포넌트 | 토큰 경로 | Storybook 스토리 | 검증 결과 |
|----------------|-----------|------------------|-----------|
| `Button / Primary` | `components.button.variants.primary.background`<br>`components.button.variants.primary.states.hover.background` | `Button/Primary` (`packages/ui/components/Button.stories.tsx`) | Figma Fill → 토큰 → CSS 변수 `--aeg-component-button-variants-primary-background`로 일치 |
| `Button / Secondary` | `components.button.variants.secondary.border` | `Button/Secondary` | Border token이 Tailwind 확장(`borderRadius.button`)과 CSS 변수에 모두 반영됨 |
| `Input / Default` | `components.input.border`<br>`components.input.states.focus.border` | `Input/Default` | Focus 상태에서 토큰 기반 box-shadow(`0 0 0 4px rgba(253, 201, 21, 0.2)`) 확인 |
| `Card / Hover` | `components.card.states.hover.shadow` | `Card/Hover` | Storybook hover 상태에서 `colors.elevation.shadow_medium` 매핑 확인 |
| `Toast / Success` | `components.toast.variants.success.background` | `Toast/Success` | Figma의 Success 토스트 배경 rgba 값이 CSS 변수로 노출됨 |

## 4. 검증 절차
1. **토큰 내보내기**  
   ```bash
   python3 scripts/export_design_tokens.py
   ```
   - `tokens/dist/design-tokens.css` 생성 및 Storybook `preview.ts`(또는 Next.js 글로벌 스타일)에 적용.
2. **Storybook 빌드**  
   ```bash
   pnpm run storybook:build
   ```
   - 스토리에서 Controls 패널로 색상/타이포 값 확인. DOM에서 `var(--aeg-component-...)` 치환 확인.
3. **Figma 비교**  
   - Figma에서 컴포넌트 선택 → `Inspect` 패널의 색상/효과 값을 추출.
   - 추출 값이 토큰 JSON 값과 동일한지 확인.
4. **Chromatic 또는 Visual Test**  
   - 토큰 변경 PR마다 `npx chromatic` 실행.
   - Chromatic diff가 없거나 기대값과 일치하면 체크리스트 통과.

## 5. 체크리스트
- [x] 버튼 기본/상태 값 매핑 확인
- [x] 입력 필드 포커스/에러 상태 매핑 확인
- [x] 카드 hover/selected 상태 매핑 확인
- [x] 토스트 variant 색상 매핑 확인
- [x] Tailwind 확장(`tailwind.tokens.cjs`)에 동일한 값 노출 확인

## 6. 유지보수 지침
- Figma 라이브러리 변경 시 `tokens/*.json` 업데이트 → `scripts/export_design_tokens.py` 실행 → Storybook 빌드 → Chromatic 결과 캡처를 본 문서에 링크한다.
- 신규 컴포넌트를 등록할 때는 위 표에 행을 추가하고 검증 로그를 남긴다.
- 연 1회 이상(혹은 대규모 UI 개편 시) Figma ↔ 코드 명명 규칙을 재검토하고 필요 시 `docs/uiux/codex_task2_delivery.md`에 반영한다.
- PR 체크리스트(`docs/uiux/pr_token_change_template.md`)의 Chromatic/Playwright 링크는 본 문서 하단 `## 7. 변경 이력` 테이블에 기록한다.

## 7. 변경 이력
| 날짜 | PR/브랜치 | Chromatic 링크 | Playwright 증적 | 비고 |
|------|-----------|----------------|-----------------|------|
|      |           |                |                 |      |
