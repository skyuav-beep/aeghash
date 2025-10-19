# 반응형 레이아웃 & 타이포 가이드 (v0.1)

## 1. Breakpoint 정의
| 구분 | 폭(px) | 주요 레이아웃 특징 |
| --- | --- | --- |
| Mobile | ≤ 480 | 단일 컬럼, Bottom Nav, 카드 전폭 |
| Tablet | 481~1024 | 2열 레이아웃, 축소 사이드바(아이콘 모드) |
| Desktop | ≥ 1025 | 12열 그리드, 고정 사이드바 |

## 2. 그리드 & 간격
- Mobile: 16px gutter, 카드 간격 12px, Padding 16px.
- Tablet: 24px gutter, 카드 간격 16px, Padding 24px.
- Desktop: 24px gutter, 12열(80px) + 24px gutter, 최대 폭 1280px.

## 3. 컴포넌트 재배치 규칙
- KPI 카드: Mobile 1열 → Tablet 2열 → Desktop 3열.
- 그래프: Mobile에서는 가로 스크롤 허용, legend collapse. Desktop에서 legend는 우측 고정.
- 필터 패널: Mobile 상단 Sheet, Tablet 우측 부착, Desktop 오른쪽 고정 패널.
- 테이블: Mobile Card 리스트, Tablet condensed 테이블, Desktop full 테이블.

## 4. 타이포 스케일링
- Base size: Mobile 14px, Tablet 15px(1.05), Desktop 16px(1.15).
- 헤더/타이틀: `typography.scale.title_lg` 기준 multiplier 적용, 최소 16px 유지.
- 본문/캡션: `typography.scale.body_md`, `typography.scale.caption_sm`.

## 5. 상태 & 반응형 토큰
- `typography.scale.*` multiplier를 breakpoint별로 적용.
- `spacing.gutter.mobile/tablet/desktop` 토큰 정의 권장.
- `components.table.density.compact/default` 토큰으로 행 높이 조절.

## 6. 테스트 체크리스트
- Breakpoint 전환 시 레이아웃 깨짐 여부.
- 사이드바/헤더 고정 상태 유지 확인.
- 폰트 크기 최소 12px 이상 보장.
- KPI 카드/그래프 배치 변경이 시각적 위계 유지하는지 검증.

## 7. TODO
1. Figma AutoLayout 설정을 breakpoint 규칙에 맞춰 업데이트.
2. Storybook viewport 애드온에 모바일/태블릿/데스크톱 프리셋 등록.
3. CSS 변수 혹은 Tailwind config에 spacing/typo multiplier 반영.
