# Storybook 컴포넌트 초안 계획 (Buttons / Inputs / Cards)

## 1. 범위 및 목표
- 대상 컴포넌트: Primary/Secondary/Destructive 버튼, 텍스트 입력 / 숫자 입력 / 선택 입력, 카드(정보·데이터·상태용) 세트.
- 모든 컴포넌트는 `tokens/colors.json`, `tokens/typography.json`, `tokens/components.json`에 정의된 토큰을 1:1 매핑한다.
- Storybook 카테고리 구조는 `Admin / UI Kit / <Component>` 형태로 통일하고 Docs 탭에 토큰 참조 표를 포함한다.

## 2. 상태 정의 및 토큰 매핑

### 2.1 버튼(Button)
| 상태 | 주요 토큰 | 설명 |
| --- | --- | --- |
| Default | `components.button.primary.background`, `typography.button.medium`, `colors.palette.text_high` | 기본 배경/타이포 토큰 적용 |
| Hover | `components.button.primary.hover.background`, `components.button.shared.shadow.hover` | hover 시 배경/섀도 업데이트 |
| Focus | `components.button.shared.focus.ring`, `colors.palette.focus` | 포커스 링 토큰 4px 외곽선 |
| Disabled | `components.button.shared.disabled.background`, `colors.palette.text_disabled` | 비활성 배경/전경 적용 |
| Loading | `components.button.shared.spinner.primary`, `animation.button.loading` | 로딩 스피너/애니메이션 토큰 적용 |

Variation: Primary, Secondary, Ghost, Destructive, Link형 각 스토리 분리.

### 2.2 입력(Input)
| 상태 | 주요 토큰 | 설명 |
| --- | --- | --- |
| Default | `components.input.field.background`, `components.input.border.default`, `typography.body_primary` | 기본 필드 배경/보더 |
| Hover | `components.input.border.hover`, `components.input.shadow.hover` | Hover 시 보더/섀도 강조 |
| Focus | `components.input.focus.ring`, `components.input.shadow.focus`, `colors.palette.focus` | 포커스 링 및 섀도 |
| Error | `components.input.border.error`, `colors.palette.error`, `typography.caption` | 에러 라벨/메시지 |
| Disabled | `components.input.field.disabled`, `colors.palette.text_disabled` | 비활성 상태 |

Variation: 텍스트 입력, 숫자 입력, Select, Search, Password 입력.

### 2.3 카드(Card)
| 유형 | 주요 토큰 | 설명 |
| --- | --- | --- |
| 정보 카드 | `components.card.info.background`, `components.card.shadow.default`, `typography.subtitle` | KPI/요약용 |
| 데이터 카드 | `components.card.data.background`, `components.card.data.badge`, `typography.data_table_value` | 값 강조형 |
| 상태 카드 | `components.card.state.success/error/warning`, `icons.state.*` | 상태별 색상 매핑 |

상태: Default, Hover, Selected, Disabled. Skeleton/Loading 상태는 토큰 `components.card.skeleton.*` 사용.

## 3. 스토리 구성 계획
- `stories/admin/ui-kit/Button.stories.tsx`
  - Primary/Secondary/Ghost/Destructive/Link story.
  - Controls: variant, isLoading, disabled, label.
  - Docs: 토큰 설명 + 포커스/로딩 상태 시연 섹션.
- `stories/admin/ui-kit/Input.stories.tsx`
  - Text/Numeric/Password/Search/Select story.
  - Controls: status(`default|error|success`), helperText, prefix/suffix icon toggle.
- `stories/admin/ui-kit/Card.stories.tsx`
  - Info/Data/State card story.
  - Controls: elevation level, showActions, status(`info|success|warning|error`).

## 4. 샘플 데이터 및 어드온
- Args 데이터는 `tests/resources/storybook_controls.json`에 공통 값 정의 후 import.
- 접근성(Addon A11y) 기본 활성화, Interaction testing으로 Hover/Focus 상태 전환 스크립트 추가.
- Chromatic/Visual regression: 버튼·입력·카드 상태별 스냅샷 baseline 생성.

## 5. TODO
1. ~~각 story 파일 scaffold 생성 (`stories/admin/ui-kit/` 경로).~~
2. `src/aeghash/utils/design_tokens.py` 기반 토큰 로더 Mock 구성.
3. Figma 테이블 → Storybook 문서 링크 추가.
4. QA 체크리스트에 Storybook 링크 삽입.
